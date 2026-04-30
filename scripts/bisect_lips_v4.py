"""
Blender script v4: BISECT lip seam + split edges + viseme morph targets.

Previous approaches failed because:
  - split_edges alone: faces still span the seam, they just stretch
  - delete faces: removes the lower lip entirely (0 verts below seam)

This approach:
  1. Use bmesh.ops.bisect_plane to CUT faces along the lip seam plane
     → creates new vertices/edges AT the exact seam line
     → faces that crossed the seam are subdivided into sub-faces on each side
     → NO geometry is removed
  2. Split the new seam edges to create two independent edge loops
     → upper and lower lip vertices are now SEPARATE
  3. Add large viseme morph targets
  4. Export GLB

Run:
  /Applications/Blender.app/Contents/MacOS/Blender --background \
    --python scripts/bisect_lips_v4.py
"""
import bpy
import bmesh
from mathutils import Vector

INPUT_GLB  = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor.glb'
OUTPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_lipsync.glb'

# ─── 1. Import original model ───
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=INPUT_GLB)

obj = bpy.data.objects.get('Object_9')
if not obj:
    raise RuntimeError("Object_9 not found!")

print(f"[v4] Object_9 BEFORE: {len(obj.data.vertices)} verts, "
      f"{len(obj.data.edges)} edges, {len(obj.data.polygons)} faces")

# ─── 2. Facial landmarks (Blender Z-up) ───
UPPER_LIP_Z = 1.5363
LOWER_LIP_Z = 1.5177
LIP_SEAM_Z  = (UPPER_LIP_Z + LOWER_LIP_Z) / 2  # 1.5270
EXPORT_SCALE = 1.878

MOUTH_CENTER = Vector((0.0002, -0.1112, 1.5340))
UPPER_LIP    = Vector((0.0003, -0.1116, UPPER_LIP_Z))
LOWER_LIP    = Vector((0.0000, -0.1054, LOWER_LIP_Z))
LEFT_CORNER  = Vector((0.0503, -0.0616, 1.5282))
RIGHT_CORNER = Vector((-0.0518, -0.0633, 1.5282))
CHIN         = Vector((0.0028, -0.0994, 1.4948))

print(f"[v4] Lip seam Z: {LIP_SEAM_Z:.4f}")
print(f"[v4] Upper lip Z: {UPPER_LIP_Z:.4f}, Lower lip Z: {LOWER_LIP_Z:.4f}")
print(f"[v4] Lip gap Blender: {UPPER_LIP_Z - LOWER_LIP_Z:.4f}")
print(f"[v4] Lip gap GLB: {(UPPER_LIP_Z - LOWER_LIP_Z) * EXPORT_SCALE:.4f}")

# ─── 3. Bisect the mouth area along the lip seam plane ───
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bm = bmesh.new()
bm.from_mesh(obj.data)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# Count cross-seam faces BEFORE bisection
def is_mouth_region(co):
    """Check if coordinate is in the front mouth area."""
    return (abs(co.x) < 0.07 and
            co.y < 0.02 and
            1.48 < co.z < 1.58)

pre_cross = 0
for face in bm.faces:
    has_above = False
    has_below = False
    for v in face.verts:
        if not is_mouth_region(v.co):
            continue
        d = v.co.z - LIP_SEAM_Z
        if d > 0.001:
            has_above = True
        elif d < -0.001:
            has_below = True
    if has_above and has_below:
        pre_cross += 1

print(f"[v4] Cross-seam faces BEFORE bisect: {pre_cross}")

# Collect geometry in the mouth area for bisection
# Include faces + their edges + their vertices
mouth_faces = set()
mouth_edges = set()
mouth_verts = set()

for face in bm.faces:
    # A face is in the mouth area if ANY of its vertices are near the lip seam
    face_in_mouth = False
    for v in face.verts:
        if is_mouth_region(v.co):
            face_in_mouth = True
            break
    if face_in_mouth:
        mouth_faces.add(face)
        for e in face.edges:
            mouth_edges.add(e)
        for v in face.verts:
            mouth_verts.add(v)

mouth_geom = list(mouth_verts) + list(mouth_edges) + list(mouth_faces)

print(f"[v4] Mouth geometry: {len(mouth_faces)} faces, "
      f"{len(mouth_edges)} edges, {len(mouth_verts)} verts")

# Bisect along Z = LIP_SEAM_Z plane (horizontal cut through lips)
# plane_no = (0, 0, 1) means the cut is horizontal (perpendicular to Z)
result = bmesh.ops.bisect_plane(
    bm,
    geom=mouth_geom,
    plane_co=Vector((0, 0, LIP_SEAM_Z)),
    plane_no=Vector((0, 0, 1)),
    dist=0.0001,       # very tight: only cut faces that truly cross the plane
    clear_inner=False,  # keep geometry below the plane
    clear_outer=False,  # keep geometry above the plane
)

# geom_cut contains the new geometry created by the cut
new_geom = result.get('geom_cut', [])
new_edges = [e for e in new_geom if isinstance(e, bmesh.types.BMEdge)]
new_verts = [v for v in new_geom if isinstance(v, bmesh.types.BMVert)]

print(f"[v4] Bisect created: {len(new_verts)} new verts, {len(new_edges)} new edges")

bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# Count cross-seam faces AFTER bisection (should be near zero)
post_cross = 0
for face in bm.faces:
    has_above = False
    has_below = False
    for v in face.verts:
        if not is_mouth_region(v.co):
            continue
        d = v.co.z - LIP_SEAM_Z
        if d > 0.001:
            has_above = True
        elif d < -0.001:
            has_below = True
    if has_above and has_below:
        post_cross += 1

print(f"[v4] Cross-seam faces AFTER bisect: {post_cross}")
print(f"[v4] After bisect: {len(bm.verts)} verts, {len(bm.faces)} faces")

# ─── 4. Split the seam edges to separate upper and lower lip ───
# Find ALL edges that lie on or very near the seam plane in the mouth area
seam_edges = []
for edge in bm.edges:
    v0, v1 = edge.verts
    # Both vertices should be on/near the seam AND in the mouth area
    if not (is_mouth_region(v0.co) and is_mouth_region(v1.co)):
        continue
    # Both vertices within tight tolerance of seam Z
    if (abs(v0.co.z - LIP_SEAM_Z) < 0.002 and
        abs(v1.co.z - LIP_SEAM_Z) < 0.002):
        seam_edges.append(edge)

print(f"[v4] Seam edges to split: {len(seam_edges)}")

if seam_edges:
    bmesh.ops.split_edges(bm, edges=seam_edges)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    print(f"[v4] After edge split: {len(bm.verts)} verts, {len(bm.faces)} faces")

# Verify: count remaining cross-seam edges
remaining = 0
for edge in bm.edges:
    v0, v1 = edge.verts
    if not (is_mouth_region(v0.co) and is_mouth_region(v1.co)):
        continue
    d0 = v0.co.z - LIP_SEAM_Z
    d1 = v1.co.z - LIP_SEAM_Z
    if d0 * d1 < 0 and abs(d0) > 0.002 and abs(d1) > 0.002:
        remaining += 1

print(f"[v4] Remaining cross-seam edges: {remaining}")

# Count vertices on each side of seam in mouth area
above_count = 0
below_count = 0
on_seam_count = 0
for v in bm.verts:
    if not is_mouth_region(v.co):
        continue
    d = v.co.z - LIP_SEAM_Z
    if d > 0.002:
        above_count += 1
    elif d < -0.002:
        below_count += 1
    else:
        on_seam_count += 1

print(f"[v4] Mouth verts — above: {above_count}, below: {below_count}, on seam: {on_seam_count}")

# Write back to mesh
bm.to_mesh(obj.data)
bm.free()
obj.data.update()

print(f"[v4] Final mesh: {len(obj.data.vertices)} verts, {len(obj.data.polygons)} faces")

# ─── 5. Add viseme shape keys ───
print(f"\n[v4] === ADDING VISEME MORPH TARGETS ===")

mesh = obj.data
if not mesh.shape_keys:
    obj.shape_key_add(name='Basis', from_mix=False)

def smooth_falloff(distance, radius):
    if distance >= radius:
        return 0.0
    t = distance / radius
    return (1.0 - t * t) ** 2

def is_front_face(co):
    return co.y < 0.02

def zone_weight(co_z, zone, seam_z):
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

# LARGE magnitudes — mouth MUST visibly open
# Lower lip: 0.040 Blender = 0.075 GLB (12% of face height)
# Upper lip: 0.018 Blender = 0.034 GLB
# Total opening: 0.058 Blender = 0.109 GLB (17% of face height)
OCULUS_VISEMES = {
    'viseme_aa': [
        (LOWER_LIP,    Vector((0, 0, -0.040)),  0.035, 'lower'),
        (CHIN,         Vector((0, 0, -0.025)),  0.040, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.018)),  0.030, 'upper'),
        (LEFT_CORNER,  Vector(( 0.008, 0, -0.008)), 0.025, 'all'),
        (RIGHT_CORNER, Vector((-0.008, 0, -0.008)), 0.025, 'all'),
    ],
    'viseme_E': [
        (LOWER_LIP,    Vector((0, 0, -0.028)),  0.030, 'lower'),
        (CHIN,         Vector((0, 0, -0.018)),  0.035, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.012)),  0.025, 'upper'),
        (LEFT_CORNER,  Vector(( 0.015, 0, 0)),  0.030, 'all'),
        (RIGHT_CORNER, Vector((-0.015, 0, 0)),  0.030, 'all'),
    ],
    'viseme_I': [
        (LOWER_LIP,    Vector((0, 0, -0.012)),  0.025, 'lower'),
        (CHIN,         Vector((0, 0, -0.008)),  0.030, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.006)),  0.020, 'upper'),
        (LEFT_CORNER,  Vector(( 0.020, 0, 0.003)), 0.035, 'all'),
        (RIGHT_CORNER, Vector((-0.020, 0, 0.003)), 0.035, 'all'),
    ],
    'viseme_O': [
        (LOWER_LIP,    Vector((0, -0.006, -0.032)),  0.030, 'lower'),
        (CHIN,         Vector((0, 0,      -0.020)),  0.035, 'lower'),
        (UPPER_LIP,    Vector((0, -0.006,  0.014)),  0.025, 'upper'),
        (LEFT_CORNER,  Vector((-0.015, -0.004, 0)),  0.028, 'all'),
        (RIGHT_CORNER, Vector(( 0.015, -0.004, 0)),  0.028, 'all'),
    ],
    'viseme_U': [
        (LOWER_LIP,    Vector((0, -0.010, -0.018)),  0.028, 'lower'),
        (CHIN,         Vector((0, 0,      -0.012)),  0.030, 'lower'),
        (UPPER_LIP,    Vector((0, -0.010,  0.008)),  0.025, 'upper'),
        (LEFT_CORNER,  Vector((-0.018, -0.006, 0)),  0.030, 'all'),
        (RIGHT_CORNER, Vector(( 0.018, -0.006, 0)),  0.030, 'all'),
    ],
    'viseme_PP': [
        (LOWER_LIP,    Vector((0, -0.004,  0.008)),  0.025, 'lower'),
        (UPPER_LIP,    Vector((0, -0.004, -0.006)),  0.025, 'upper'),
        (CHIN,         Vector((0, 0,       0.004)),  0.020, 'lower'),
    ],
    'viseme_SS': [
        (LOWER_LIP,    Vector((0, 0, -0.008)),  0.025, 'lower'),
        (CHIN,         Vector((0, 0, -0.006)),  0.028, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.004)),  0.020, 'upper'),
        (LEFT_CORNER,  Vector(( 0.015, 0, 0.002)), 0.030, 'all'),
        (RIGHT_CORNER, Vector((-0.015, 0, 0.002)), 0.030, 'all'),
    ],
    'viseme_TH': [
        (LOWER_LIP,    Vector((0, 0, -0.018)),  0.028, 'lower'),
        (CHIN,         Vector((0, 0, -0.012)),  0.030, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.008)),  0.025, 'upper'),
    ],
    'viseme_DD': [
        (LOWER_LIP,    Vector((0, 0, -0.022)),  0.028, 'lower'),
        (CHIN,         Vector((0, 0, -0.015)),  0.030, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.006)),  0.022, 'upper'),
    ],
    'viseme_FF': [
        (LOWER_LIP,    Vector((0, 0.006, 0.010)),  0.025, 'lower'),
        (UPPER_LIP,    Vector((0, 0,    -0.004)),   0.020, 'upper'),
    ],
    'viseme_kk': [
        (LOWER_LIP,    Vector((0, 0, -0.022)),  0.028, 'lower'),
        (CHIN,         Vector((0, 0, -0.016)),  0.035, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.006)),  0.022, 'upper'),
    ],
    'viseme_nn': [
        (LOWER_LIP,    Vector((0, 0, -0.015)),  0.025, 'lower'),
        (CHIN,         Vector((0, 0, -0.010)),  0.030, 'lower'),
        (UPPER_LIP,    Vector((0, 0,  0.006)),  0.020, 'upper'),
    ],
    'viseme_RR': [
        (LOWER_LIP,    Vector((0, -0.004, -0.018)),  0.028, 'lower'),
        (CHIN,         Vector((0, 0,      -0.012)),  0.030, 'lower'),
        (UPPER_LIP,    Vector((0, -0.004,  0.006)),  0.022, 'upper'),
    ],
    'viseme_CH': [
        (LOWER_LIP,    Vector((0, -0.006, -0.018)),  0.028, 'lower'),
        (CHIN,         Vector((0, 0,      -0.012)),  0.030, 'lower'),
        (UPPER_LIP,    Vector((0, -0.006,  0.006)),  0.022, 'upper'),
        (LEFT_CORNER,  Vector((-0.006, -0.004, 0)),  0.025, 'all'),
        (RIGHT_CORNER, Vector(( 0.006, -0.004, 0)),  0.025, 'all'),
    ],
    'viseme_sil': [],
}

for viseme_name, control_points in OCULUS_VISEMES.items():
    sk = obj.shape_key_add(name=viseme_name, from_mix=False)
    sk.value = 0.0

    moved = 0
    max_disp = 0.0

    for i, v in enumerate(mesh.vertices):
        co = v.co
        if not is_front_face(co):
            continue

        total_disp = compute_displacement(co, control_points, LIP_SEAM_Z)

        if total_disp.length > 0.0001:
            sk.data[i].co = co + total_disp
            moved += 1
            if total_disp.length > max_disp:
                max_disp = total_disp.length

    glb_max = max_disp * EXPORT_SCALE
    print(f"[v4] {viseme_name:12s}: {moved:4d} verts, "
          f"blender={max_disp:.5f} glb={glb_max:.5f}")


# ─── 6. Export ───
print(f"\n[v4] Exporting to {OUTPUT_GLB}...")
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

if obj.data.shape_keys:
    names = [kb.name for kb in obj.data.shape_keys.key_blocks if kb.name != 'Basis']
    print(f"[v4] Shape keys: {len(names)}: {', '.join(names[:5])}...")

print("[v4] DONE!")
