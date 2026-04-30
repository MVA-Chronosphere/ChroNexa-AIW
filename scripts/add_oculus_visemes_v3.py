"""
Blender script v3: Add 15 Oculus viseme shape keys to ALL face-area meshes.

Previous issues:
  v1: Jaw rotation pushed chin backward instead of downward
  v2: Zone separation worked, but displacements were 3x too large (Blender export
      multiplies by root scale 1.878), AND morph targets were only on Object_9
      while Object_14/15 (teeth/gums) covered the mouth area without deforming.

Fixes in v3:
  1. Magnitudes reduced ~3x to account for 1.878x export scale
  2. Radii tightened ~2x for natural lip deformation (not whole-chin stretching)
  3. Morph targets applied to Object_9 (face), Object_14, Object_15 (teeth/gums)
     so ALL mouth-area meshes deform together

Run:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/add_oculus_visemes_v3.py
"""
import bpy
from mathutils import Vector

INPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor.glb'
OUTPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_lipsync.glb'

# ─── 1. Import ───
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=INPUT_GLB)

# Meshes to apply morph targets to:
# Object_9 = face/head (7419v) — main face mesh
# Object_14 = teeth lower (2511v) — lower teeth + inner lip/gum
# Object_15 = teeth upper (2497v) — upper teeth + inner lip/gum
TARGET_MESHES = ['Object_9', 'Object_14', 'Object_15']

mesh_objects = {}
for name in TARGET_MESHES:
    obj = bpy.data.objects.get(name)
    if obj:
        mesh_objects[name] = obj
        print(f"[Visemes] Found {name}: {len(obj.data.vertices)} verts")
    else:
        print(f"[Visemes] WARNING: {name} not found")

if 'Object_9' not in mesh_objects:
    raise RuntimeError("Object_9 (head mesh) not found")


# ─── 2. Facial landmarks (Blender Z-up coordinates) ───
# Blender: X=left/right, Y=front(-)/back(+), Z=up(+)/down(-)
# Export: GLB_X = X, GLB_Y = Z * 1.878, GLB_Z = -Y * 1.878
# So Blender -Z (down) → GLB -Y (down) ✓ but SCALED by 1.878!
EXPORT_SCALE = 1.878

MOUTH_CENTER = Vector((0.0002, -0.1112, 1.5340))
UPPER_LIP    = Vector((0.0003, -0.1116, 1.5363))
LOWER_LIP    = Vector((0.0000, -0.1054, 1.5177))
LEFT_CORNER  = Vector((0.0503, -0.0616, 1.5282))
RIGHT_CORNER = Vector((-0.0518, -0.0633, 1.5282))
CHIN         = Vector((0.0028, -0.0994, 1.4948))

LIP_SEAM_Z = (UPPER_LIP.z + LOWER_LIP.z) / 2  # ~1.527
LIP_GAP = UPPER_LIP.z - LOWER_LIP.z  # ~0.0186

print(f"[Visemes] LIP_SEAM Z: {LIP_SEAM_Z:.4f}")
print(f"[Visemes] Lip gap: {LIP_GAP:.4f}")
print(f"[Visemes] Export scale: {EXPORT_SCALE}")
print(f"[Visemes] Lip gap in GLB: {LIP_GAP * EXPORT_SCALE:.4f}")


def smooth_falloff(distance, radius):
    if distance >= radius:
        return 0.0
    t = distance / radius
    return (1.0 - t * t) ** 2


def zone_weight(co_z, zone, seam_z):
    """Weight based on which side of the lip seam the vertex is on."""
    if zone == 'all':
        return 1.0
    margin = 0.003
    if zone == 'lower':
        if co_z > seam_z + margin:
            return 0.0
        if co_z < seam_z - margin:
            return 1.0
        return (seam_z + margin - co_z) / (2 * margin)
    elif zone == 'upper':
        if co_z < seam_z - margin:
            return 0.0
        if co_z > seam_z + margin:
            return 1.0
        return (co_z - seam_z + margin) / (2 * margin)
    return 1.0


def is_front_face(co):
    return co.y < 0.02


def compute_displacement(v_co, control_points, seam_z):
    total = Vector((0, 0, 0))
    for center, disp, radius, zone in control_points:
        zw = zone_weight(v_co.z, zone, seam_z)
        if zw < 0.001:
            continue
        dist = (v_co - center).length
        w = smooth_falloff(dist, radius) * zw
        if w > 0.001:
            total += disp * w
    return total


# ─── 3. Viseme definitions ───
# CRITICAL: All magnitudes are in Blender units. The export multiplies by 1.878.
# Target mouth opening for viseme_aa:
#   Lower lip down: 0.018 Blender → 0.034 GLB
#   Upper lip up:   0.008 Blender → 0.015 GLB
#   Total opening:  0.026 Blender → 0.049 GLB
#   Original gap:   0.019 Blender → 0.035 GLB
#   Final gap:      0.045 Blender → 0.084 GLB (~13% of face height) ✓
#
# Radii are TIGHT to avoid stretching the whole chin:
#   Lower lip: 0.020-0.025 (only immediate lip edge)
#   Chin:      0.025-0.035 (subtle chin follow-through)
#   Upper lip: 0.015-0.020

OCULUS_VISEMES = {
    # 0: viseme_aa — WIDE OPEN "ah"
    'viseme_aa': [
        (LOWER_LIP,    Vector((0, 0, -0.018)),  0.025, 'lower'),
        (CHIN,         Vector((0, 0, -0.012)),  0.030, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.008)),  0.020, 'upper'),
        (LEFT_CORNER,  Vector(( 0.004, 0, -0.004)), 0.020, 'all'),
        (RIGHT_CORNER, Vector((-0.004, 0, -0.004)), 0.020, 'all'),
    ],

    # 1: viseme_E — MID OPEN, SPREAD "eh"
    'viseme_E': [
        (LOWER_LIP,    Vector((0, 0, -0.012)),  0.022, 'lower'),
        (CHIN,         Vector((0, 0, -0.008)),  0.025, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.005)),  0.018, 'upper'),
        (LEFT_CORNER,  Vector(( 0.008, 0, 0)),  0.025, 'all'),
        (RIGHT_CORNER, Vector((-0.008, 0, 0)),  0.025, 'all'),
    ],

    # 2: viseme_I — NARROW SPREAD "ee"
    'viseme_I': [
        (LOWER_LIP,    Vector((0, 0, -0.005)),  0.018, 'lower'),
        (CHIN,         Vector((0, 0, -0.004)),  0.022, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.003)),  0.015, 'upper'),
        (LEFT_CORNER,  Vector(( 0.012, 0, 0.002)), 0.028, 'all'),
        (RIGHT_CORNER, Vector((-0.012, 0, 0.002)), 0.028, 'all'),
    ],

    # 3: viseme_O — ROUNDED OPEN "oh"
    'viseme_O': [
        (LOWER_LIP,    Vector((0, -0.003, -0.014)),  0.022, 'lower'),
        (CHIN,         Vector((0, 0,      -0.010)),  0.028, 'lower'),
        (UPPER_LIP,    Vector((0, -0.003,  0.006)),  0.018, 'upper'),
        (LEFT_CORNER,  Vector((-0.008, -0.002, 0)),  0.022, 'all'),
        (RIGHT_CORNER, Vector(( 0.008, -0.002, 0)),  0.022, 'all'),
    ],

    # 4: viseme_U — PURSED "oo"
    'viseme_U': [
        (LOWER_LIP,    Vector((0, -0.006, -0.008)),  0.020, 'lower'),
        (CHIN,         Vector((0, 0,      -0.006)),  0.022, 'lower'),
        (UPPER_LIP,    Vector((0, -0.006,  0.004)),  0.018, 'upper'),
        (LEFT_CORNER,  Vector((-0.010, -0.003, 0)),  0.025, 'all'),
        (RIGHT_CORNER, Vector(( 0.010, -0.003, 0)),  0.025, 'all'),
    ],

    # 5: viseme_PP — LIPS PRESSED (p, b, m)
    'viseme_PP': [
        (LOWER_LIP,    Vector((0, -0.002,  0.005)),  0.018, 'lower'),
        (UPPER_LIP,    Vector((0, -0.002, -0.004)),  0.018, 'upper'),
        (CHIN,         Vector((0, 0,       0.002)),  0.015, 'lower'),
        (LEFT_CORNER,  Vector(( 0.002, 0, 0)),  0.015, 'all'),
        (RIGHT_CORNER, Vector((-0.002, 0, 0)),  0.015, 'all'),
    ],

    # 6: viseme_SS — SIBILANT (s, z)
    'viseme_SS': [
        (LOWER_LIP,    Vector((0, 0, -0.004)),  0.018, 'lower'),
        (CHIN,         Vector((0, 0, -0.003)),  0.020, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.002)),  0.015, 'upper'),
        (LEFT_CORNER,  Vector(( 0.008, 0, 0.001)), 0.025, 'all'),
        (RIGHT_CORNER, Vector((-0.008, 0, 0.001)), 0.025, 'all'),
    ],

    # 7: viseme_TH — DENTAL (θ, ð)
    'viseme_TH': [
        (LOWER_LIP,    Vector((0, 0, -0.008)),  0.020, 'lower'),
        (CHIN,         Vector((0, 0, -0.006)),  0.022, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.004)),  0.018, 'upper'),
        (LEFT_CORNER,  Vector(( 0.003, 0, 0)),  0.015, 'all'),
        (RIGHT_CORNER, Vector((-0.003, 0, 0)),  0.015, 'all'),
    ],

    # 8: viseme_DD — ALVEOLAR STOP (t, d)
    'viseme_DD': [
        (LOWER_LIP,    Vector((0, 0, -0.010)),  0.020, 'lower'),
        (CHIN,         Vector((0, 0, -0.007)),  0.022, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.003)),  0.016, 'upper'),
        (LEFT_CORNER,  Vector(( 0.004, 0, 0)),  0.018, 'all'),
        (RIGHT_CORNER, Vector((-0.004, 0, 0)),  0.018, 'all'),
    ],

    # 9: viseme_FF — LABIODENTAL (f, v)
    'viseme_FF': [
        (LOWER_LIP,    Vector((0, 0.004, 0.006)),  0.018, 'lower'),
        (CHIN,         Vector((0, 0,     0.003)),   0.018, 'lower'),
        (UPPER_LIP,    Vector((0, 0,    -0.002)),   0.015, 'upper'),
    ],

    # 10: viseme_kk — VELAR STOP (k, g)
    'viseme_kk': [
        (LOWER_LIP,    Vector((0, 0, -0.010)),  0.020, 'lower'),
        (CHIN,         Vector((0, 0, -0.008)),  0.025, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.003)),  0.016, 'upper'),
        (LEFT_CORNER,  Vector(( 0.003, 0, 0)),  0.015, 'all'),
        (RIGHT_CORNER, Vector((-0.003, 0, 0)),  0.015, 'all'),
    ],

    # 11: viseme_nn — NASAL (n, ŋ)
    'viseme_nn': [
        (LOWER_LIP,    Vector((0, 0, -0.007)),  0.018, 'lower'),
        (CHIN,         Vector((0, 0, -0.005)),  0.022, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.003)),  0.015, 'upper'),
        (LEFT_CORNER,  Vector(( 0.003, 0, 0)),  0.015, 'all'),
        (RIGHT_CORNER, Vector((-0.003, 0, 0)),  0.015, 'all'),
    ],

    # 12: viseme_RR — LIQUID (r, l, w)
    'viseme_RR': [
        (LOWER_LIP,    Vector((0, -0.002, -0.008)),  0.020, 'lower'),
        (CHIN,         Vector((0, 0,      -0.006)),  0.022, 'lower'),
        (UPPER_LIP,    Vector((0, -0.002,  0.003)),  0.016, 'upper'),
        (LEFT_CORNER,  Vector(( 0.003, -0.001, 0)),  0.015, 'all'),
        (RIGHT_CORNER, Vector((-0.003, -0.001, 0)),  0.015, 'all'),
    ],

    # 13: viseme_CH — AFFRICATE (tʃ, dʒ)
    'viseme_CH': [
        (LOWER_LIP,    Vector((0, -0.003, -0.008)),  0.020, 'lower'),
        (CHIN,         Vector((0, 0,      -0.006)),  0.022, 'lower'),
        (UPPER_LIP,    Vector((0, -0.003,  0.003)),  0.016, 'upper'),
        (LEFT_CORNER,  Vector((-0.004, -0.002, 0)),  0.020, 'all'),
        (RIGHT_CORNER, Vector(( 0.004, -0.002, 0)),  0.020, 'all'),
    ],

    # 14: viseme_sil — SILENCE / REST
    'viseme_sil': [],
}


# ─── 4. Create shape keys on ALL target meshes ───
for obj_name, obj in mesh_objects.items():
    mesh = obj.data
    verts = mesh.vertices

    if not mesh.shape_keys:
        obj.shape_key_add(name='Basis', from_mix=False)

    for viseme_name, control_points in OCULUS_VISEMES.items():
        sk = obj.shape_key_add(name=viseme_name, from_mix=False)
        sk.value = 0.0

        moved = 0
        max_disp = 0.0
        max_disp_dir = Vector((0, 0, 0))

        for i, v in enumerate(verts):
            co = v.co
            if not is_front_face(co):
                continue

            total_disp = compute_displacement(co, control_points, LIP_SEAM_Z)

            if total_disp.length > 0.0001:
                sk.data[i].co = co + total_disp
                moved += 1
                if total_disp.length > max_disp:
                    max_disp = total_disp.length
                    max_disp_dir = total_disp.copy()

        # GLB magnitudes (Blender * export_scale)
        glb_max = max_disp * EXPORT_SCALE
        print(f"[Visemes] {obj_name:10s} {viseme_name:12s}: {moved:4d} verts, "
              f"blender={max_disp:.5f} glb={glb_max:.5f}  "
              f"dir: X={max_disp_dir.x:+.4f} Y={max_disp_dir.y:+.4f} Z={max_disp_dir.z:+.4f}")


# ─── 5. Export ───
print(f"\n[Visemes] Exporting to {OUTPUT_GLB}...")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(
    filepath=OUTPUT_GLB,
    export_format='GLB',
    export_animations=True,
    export_morph=True,
    export_morph_normal=True,
    export_skins=True,
    export_all_influences=True,
    use_selection=False,
)

# Verify
for obj_name, obj in mesh_objects.items():
    if obj.data.shape_keys:
        names = [kb.name for kb in obj.data.shape_keys.key_blocks if kb.name != 'Basis']
        print(f"[Visemes] {obj_name}: {len(names)} shape keys")

print("[Visemes] Done!")
