"""
Blender script: Add 15 Oculus viseme shape keys with CORRECT displacement directions.

Key fix: Previous scripts produced jaw rotation that pushed the chin BACKWARD
into the skull instead of DOWNWARD. This script uses pure directional displacements:
  - Mouth opening = lower lip/chin move DOWN (Blender -Z → GLB -Y)
  - Lip rounding  = lips move FORWARD (Blender -Y → GLB +Z)
  - Lip spread    = corners move outward (Blender ±X)
  - Minimal backward displacement

Large magnitudes + wide falloff radii for clearly visible mouth opening.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/add_oculus_visemes_v2.py
"""
import bpy
import math
from mathutils import Vector

INPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor.glb'
OUTPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_lipsync.glb'

# ─── 1. Import ───
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=INPUT_GLB)

head_obj = bpy.data.objects.get('Object_9')
if not head_obj:
    raise RuntimeError("Object_9 (head mesh) not found")

mesh = head_obj.data
verts = mesh.vertices

# ─── 2. Facial landmarks (Blender Z-up coordinates) ───
# In Blender: X=left/right, Y=front(-)/back(+), Z=up(+)/down(-)
MOUTH_CENTER   = Vector((0.0002, -0.1112, 1.5340))
UPPER_LIP      = Vector((0.0003, -0.1116, 1.5363))
LOWER_LIP      = Vector((0.0000, -0.1054, 1.5177))
LEFT_CORNER    = Vector((0.0503, -0.0616, 1.5282))
RIGHT_CORNER   = Vector((-0.0518, -0.0633, 1.5282))
CHIN           = Vector((0.0028, -0.0994, 1.4948))

LIP_SEAM_Z = (UPPER_LIP.z + LOWER_LIP.z) / 2  # ~1.527

print(f"[Visemes] UPPER_LIP Z: {UPPER_LIP.z:.4f}")
print(f"[Visemes] LOWER_LIP Z: {LOWER_LIP.z:.4f}")
print(f"[Visemes] LIP_SEAM Z:  {LIP_SEAM_Z:.4f}")
print(f"[Visemes] CHIN Z:      {CHIN.z:.4f}")
print(f"[Visemes] Lip gap:     {UPPER_LIP.z - LOWER_LIP.z:.4f}")


def smooth_falloff(distance, radius):
    """Smooth bell-curve falloff: 1.0 at center, 0.0 at radius."""
    if distance >= radius:
        return 0.0
    t = distance / radius
    return (1.0 - t * t) ** 2


def is_front_face(co):
    """Is this vertex on the front of the face (not back of head)?"""
    return co.y < 0.02


def is_lower_face(co, seam_z):
    """Is this vertex below the lip seam? With smooth blend zone."""
    if co.z > seam_z + 0.01:
        return 0.0  # Upper face — no effect
    if co.z < seam_z - 0.01:
        return 1.0  # Lower face — full effect
    t = (seam_z + 0.01 - co.z) / 0.02
    return t


def zone_weight(co_z, zone, seam_z):
    """Weight based on which side of the lip seam the vertex is on.
    Smooth transition across a 0.006 blend zone to avoid hard edges."""
    if zone == 'all':
        return 1.0
    margin = 0.003  # half of blend zone
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


def compute_displacement(v_co, control_points, seam_z):
    """Compute total displacement from zone-aware control points.
    Each: (center_position, displacement_vector, influence_radius, zone)
    zone: 'lower' = only below lip seam, 'upper' = only above, 'all' = everywhere"""
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
# All displacements in Blender coordinates:
#   X+ = left, X- = right
#   Y- = forward (toward camera), Y+ = backward
#   Z+ = up, Z- = down
#
# GLB conversion: GLB_X = X, GLB_Y = Z, GLB_Z = -Y
# So Blender -Z (down) → GLB -Y (down) ✓
#    Blender -Y (forward) → GLB +Z (toward camera) ✓

# Mouth area centers for different regions
MID_UPPER_LIP = UPPER_LIP.copy()
MID_LOWER_LIP = LOWER_LIP.copy()
MID_CHIN = CHIN.copy()

# ── Scale factors ──
# These are much larger than before to ensure visible mouth opening.
# The lip gap is only 0.019, so we need displacements of 0.03-0.06 to double/triple it.

OCULUS_VISEMES = {
    # ══════════════════════════════════════════════════════════════════
    # Format: (center, displacement, radius, zone)
    # zone: 'lower' = below lip seam only, 'upper' = above only, 'all' = both
    # This prevents lower-lip "pull down" from dragging upper lip down too
    # ══════════════════════════════════════════════════════════════════

    # 0: viseme_aa — WIDE OPEN "ah" (a, ɑ, aɪ)
    'viseme_aa': [
        (LOWER_LIP,    Vector((0, 0, -0.055)),  0.06, 'lower'),
        (CHIN,         Vector((0, 0, -0.065)),  0.08, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.015)),  0.04, 'upper'),
        (LEFT_CORNER,  Vector(( 0.010, 0, -0.008)), 0.04, 'all'),
        (RIGHT_CORNER, Vector((-0.010, 0, -0.008)), 0.04, 'all'),
    ],

    # 1: viseme_E — MID OPEN, SPREAD "eh" (ɛ, e, ə)
    'viseme_E': [
        (LOWER_LIP,    Vector((0, 0, -0.030)),  0.05, 'lower'),
        (CHIN,         Vector((0, 0, -0.035)),  0.06, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.010)),  0.04, 'upper'),
        (LEFT_CORNER,  Vector(( 0.020, 0, 0)),  0.05, 'all'),
        (RIGHT_CORNER, Vector((-0.020, 0, 0)),  0.05, 'all'),
    ],

    # 2: viseme_I — NARROW SPREAD "ee" (i, ɪ)
    'viseme_I': [
        (LOWER_LIP,    Vector((0, 0, -0.012)),  0.04, 'lower'),
        (CHIN,         Vector((0, 0, -0.015)),  0.05, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.005)),  0.03, 'upper'),
        (LEFT_CORNER,  Vector(( 0.030, 0, 0.005)), 0.06, 'all'),
        (RIGHT_CORNER, Vector((-0.030, 0, 0.005)), 0.06, 'all'),
    ],

    # 3: viseme_O — ROUNDED OPEN "oh" (o, ɔ)
    'viseme_O': [
        (LOWER_LIP,    Vector((0, -0.008, -0.040)),  0.05, 'lower'),
        (CHIN,         Vector((0, 0,      -0.045)),  0.07, 'lower'),
        (UPPER_LIP,    Vector((0, -0.008,  0.012)),  0.04, 'upper'),
        (LEFT_CORNER,  Vector((-0.018, -0.005, 0)),  0.05, 'all'),
        (RIGHT_CORNER, Vector(( 0.018, -0.005, 0)),  0.05, 'all'),
    ],

    # 4: viseme_U — PURSED "oo" (u, ʊ)
    'viseme_U': [
        (LOWER_LIP,    Vector((0, -0.015, -0.020)),  0.04, 'lower'),
        (CHIN,         Vector((0, 0,      -0.022)),  0.05, 'lower'),
        (UPPER_LIP,    Vector((0, -0.015,  0.010)),  0.04, 'upper'),
        (LEFT_CORNER,  Vector((-0.025, -0.008, 0)),  0.06, 'all'),
        (RIGHT_CORNER, Vector(( 0.025, -0.008, 0)),  0.06, 'all'),
    ],

    # 5: viseme_PP — LIPS PRESSED (p, b, m)
    'viseme_PP': [
        (LOWER_LIP,    Vector((0, -0.004,  0.012)),  0.04, 'lower'),
        (UPPER_LIP,    Vector((0, -0.004, -0.010)),  0.04, 'upper'),
        (CHIN,         Vector((0, 0,       0.005)),  0.03, 'lower'),
        (LEFT_CORNER,  Vector(( 0.004, 0, 0)),  0.03, 'all'),
        (RIGHT_CORNER, Vector((-0.004, 0, 0)),  0.03, 'all'),
    ],

    # 6: viseme_SS — TEETH NEARLY CLOSED, SIBILANT (s, z, ʃ)
    'viseme_SS': [
        (LOWER_LIP,    Vector((0, 0, -0.010)),  0.04, 'lower'),
        (CHIN,         Vector((0, 0, -0.012)),  0.04, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.004)),  0.03, 'upper'),
        (LEFT_CORNER,  Vector(( 0.018, 0, 0.003)), 0.05, 'all'),
        (RIGHT_CORNER, Vector((-0.018, 0, 0.003)), 0.05, 'all'),
    ],

    # 7: viseme_TH — DENTAL (θ, ð) — tongue tip visible
    'viseme_TH': [
        (LOWER_LIP,    Vector((0, 0, -0.022)),  0.05, 'lower'),
        (CHIN,         Vector((0, 0, -0.025)),  0.05, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.008)),  0.04, 'upper'),
        (LEFT_CORNER,  Vector(( 0.006, 0, 0)),  0.03, 'all'),
        (RIGHT_CORNER, Vector((-0.006, 0, 0)),  0.03, 'all'),
    ],

    # 8: viseme_DD — ALVEOLAR STOP (t, d)
    'viseme_DD': [
        (LOWER_LIP,    Vector((0, 0, -0.025)),  0.05, 'lower'),
        (CHIN,         Vector((0, 0, -0.028)),  0.05, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.006)),  0.035, 'upper'),
        (LEFT_CORNER,  Vector(( 0.010, 0, 0)),  0.04, 'all'),
        (RIGHT_CORNER, Vector((-0.010, 0, 0)),  0.04, 'all'),
    ],

    # 9: viseme_FF — LABIODENTAL (f, v) — lower lip under upper teeth
    'viseme_FF': [
        (LOWER_LIP,    Vector((0, 0.010, 0.015)),  0.04, 'lower'),
        (CHIN,         Vector((0, 0,     0.008)),   0.04, 'lower'),
        (UPPER_LIP,    Vector((0, 0,    -0.003)),   0.03, 'upper'),
    ],

    # 10: viseme_kk — VELAR STOP (k, g)
    'viseme_kk': [
        (LOWER_LIP,    Vector((0, 0, -0.028)),  0.05, 'lower'),
        (CHIN,         Vector((0, 0, -0.032)),  0.06, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.006)),  0.035, 'upper'),
        (LEFT_CORNER,  Vector(( 0.006, 0, 0)),  0.03, 'all'),
        (RIGHT_CORNER, Vector((-0.006, 0, 0)),  0.03, 'all'),
    ],

    # 11: viseme_nn — NASAL (n, ŋ)
    'viseme_nn': [
        (LOWER_LIP,    Vector((0, 0, -0.018)),  0.04, 'lower'),
        (CHIN,         Vector((0, 0, -0.020)),  0.05, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.005)),  0.03, 'upper'),
        (LEFT_CORNER,  Vector(( 0.006, 0, 0)),  0.03, 'all'),
        (RIGHT_CORNER, Vector((-0.006, 0, 0)),  0.03, 'all'),
    ],

    # 12: viseme_RR — LIQUID (r, l, w)
    'viseme_RR': [
        (LOWER_LIP,    Vector((0, -0.004, -0.022)),  0.05, 'lower'),
        (CHIN,         Vector((0, 0,      -0.025)),  0.05, 'lower'),
        (UPPER_LIP,    Vector((0, -0.004,  0.006)),  0.035, 'upper'),
        (LEFT_CORNER,  Vector(( 0.005, -0.002, 0)),  0.03, 'all'),
        (RIGHT_CORNER, Vector((-0.005, -0.002, 0)),  0.03, 'all'),
    ],

    # 13: viseme_CH — AFFRICATE (tʃ, dʒ)
    'viseme_CH': [
        (LOWER_LIP,    Vector((0, -0.006, -0.018)),  0.04, 'lower'),
        (CHIN,         Vector((0, 0,      -0.020)),  0.05, 'lower'),
        (UPPER_LIP,    Vector((0, -0.006,  0.006)),  0.035, 'upper'),
        (LEFT_CORNER,  Vector((-0.008, -0.004, 0)),  0.04, 'all'),
        (RIGHT_CORNER, Vector(( 0.008, -0.004, 0)),  0.04, 'all'),
    ],

    # 14: viseme_sil — SILENCE / REST
    'viseme_sil': [],
}


# ─── 4. Create shape keys ───
if not mesh.shape_keys:
    head_obj.shape_key_add(name='Basis', from_mix=False)

for viseme_name, control_points in OCULUS_VISEMES.items():
    sk = head_obj.shape_key_add(name=viseme_name, from_mix=False)
    sk.value = 0.0

    moved = 0
    max_disp = 0.0
    max_disp_dir = Vector((0,0,0))

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

    print(f"[Visemes] {viseme_name:12s}: {moved:5d} verts, max disp: {max_disp:.5f}  dir: X={max_disp_dir.x:+.4f} Y={max_disp_dir.y:+.4f} Z={max_disp_dir.z:+.4f}")


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

names = [kb.name for kb in mesh.shape_keys.key_blocks if kb.name != 'Basis']
print(f"[Visemes] Done! {len(names)} shape keys: {names}")
