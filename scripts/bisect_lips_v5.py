"""
Blender script v5: Bisect lips + face-connectivity zone detection.

Root cause of v4 failure:
  After bisect+split_edges, duplicated seam vertices have IDENTICAL positions
  (both at Z=LIP_SEAM_Z). The zone_weight() function uses vertex Z to determine
  if a vertex belongs to upper or lower lip. Since both copies have the same Z,
  both get the same morph displacement → they move together → no gap opens.

Fix: Determine each seam vertex's zone by checking which faces it belongs to.
  - If all connected faces are ABOVE the seam → upper lip vertex → push UP
  - If all connected faces are BELOW the seam → lower lip vertex → push DOWN
  This makes the two copies of each seam vertex move in OPPOSITE directions.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender --background \
    --python scripts/bisect_lips_v5.py
"""
import bpy
import bmesh
from mathutils import Vector

INPUT_GLB  = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor.glb'
OUTPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_lipsync.glb'

# ─── 1. Import ───
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=INPUT_GLB)

obj = bpy.data.objects.get('Object_9')
if not obj:
    raise RuntimeError("Object_9 not found!")

print(f"[v5] Object_9 BEFORE: {len(obj.data.vertices)} verts, {len(obj.data.polygons)} faces")

# ─── 2. Landmarks ───
UPPER_LIP_Z = 1.5363
LOWER_LIP_Z = 1.5177
# v4 used midpoint (1.5270) — TOO LOW, cut through lower lip!
# The actual lip contact line is at MOUTH_CENTER.z = 1.5340
LIP_SEAM_Z  = 1.5340
EXPORT_SCALE = 1.878

MOUTH_CENTER = Vector((0.0002, -0.1112, 1.5340))
UPPER_LIP    = Vector((0.0003, -0.1116, UPPER_LIP_Z))
LOWER_LIP    = Vector((0.0000, -0.1054, LOWER_LIP_Z))
LEFT_CORNER  = Vector((0.0503, -0.0616, 1.5282))
RIGHT_CORNER = Vector((-0.0518, -0.0633, 1.5282))
CHIN         = Vector((0.0028, -0.0994, 1.4948))

print(f"[v5] Lip seam Z: {LIP_SEAM_Z:.4f}")

# ─── 3. Bisect ───
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bm = bmesh.new()
bm.from_mesh(obj.data)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

def is_mouth_region(co):
    return (abs(co.x) < 0.07 and co.y < 0.02 and 1.48 < co.z < 1.58)

# Count pre-bisect cross-seam
pre_cross = sum(1 for f in bm.faces
    if any(v.co.z - LIP_SEAM_Z > 0.001 for v in f.verts if is_mouth_region(v.co))
    and any(v.co.z - LIP_SEAM_Z < -0.001 for v in f.verts if is_mouth_region(v.co)))
print(f"[v5] Cross-seam faces BEFORE: {pre_cross}")

# Collect mouth geometry
mouth_geom = []
for face in bm.faces:
    if any(is_mouth_region(v.co) for v in face.verts):
        mouth_geom.append(face)
        for e in face.edges:
            mouth_geom.append(e)
        for v in face.verts:
            mouth_geom.append(v)
mouth_geom = list(set(mouth_geom))

# Bisect
result = bmesh.ops.bisect_plane(
    bm, geom=mouth_geom,
    plane_co=Vector((0, 0, LIP_SEAM_Z)),
    plane_no=Vector((0, 0, 1)),
    dist=0.0001,
    clear_inner=False,
    clear_outer=False,
)

new_geom = result.get('geom_cut', [])
new_edges = [e for e in new_geom if isinstance(e, bmesh.types.BMEdge)]
print(f"[v5] Bisect: {len(new_edges)} new edges on seam")

bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# ─── 4. Split seam edges ───
seam_edges = []
for edge in bm.edges:
    v0, v1 = edge.verts
    if not (is_mouth_region(v0.co) and is_mouth_region(v1.co)):
        continue
    if (abs(v0.co.z - LIP_SEAM_Z) < 0.002 and
        abs(v1.co.z - LIP_SEAM_Z) < 0.002):
        seam_edges.append(edge)

print(f"[v5] Splitting {len(seam_edges)} seam edges")

if seam_edges:
    bmesh.ops.split_edges(bm, edges=seam_edges)

bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

print(f"[v5] After split: {len(bm.verts)} verts, {len(bm.faces)} faces")

# ─── 5. Build face-connectivity zone map ───
# For each vertex on/near the seam, determine zone by its connected faces
# A face's center Z tells us if it's above or below the seam

SEAM_TOL = 0.004  # vertices within this of seam Z need face-based detection

# vertex_zone[vert_index] = 'upper' | 'lower' | 'seam' | None (not in mouth)
vertex_zone = {}

for v in bm.verts:
    if not is_mouth_region(v.co):
        continue
    
    dz = v.co.z - LIP_SEAM_Z
    
    # Clear case: far from seam
    if dz > SEAM_TOL:
        vertex_zone[v.index] = 'upper'
        continue
    if dz < -SEAM_TOL:
        vertex_zone[v.index] = 'lower'
        continue
    
    # ON the seam — use face connectivity
    # Check the average Z of all connected face centers (excluding the seam plane)
    above_faces = 0
    below_faces = 0
    for face in v.link_faces:
        # Face center Z (average of all face vertex Z)
        face_center_z = sum(fv.co.z for fv in face.verts) / len(face.verts)
        if face_center_z > LIP_SEAM_Z + 0.001:
            above_faces += 1
        elif face_center_z < LIP_SEAM_Z - 0.001:
            below_faces += 1
    
    if above_faces > 0 and below_faces == 0:
        vertex_zone[v.index] = 'upper'
    elif below_faces > 0 and above_faces == 0:
        vertex_zone[v.index] = 'lower'
    elif above_faces > below_faces:
        vertex_zone[v.index] = 'upper'
    elif below_faces > above_faces:
        vertex_zone[v.index] = 'lower'
    else:
        # Tie or no clear winner — default to looking at which side
        # has the vertex's deepest neighbor
        vertex_zone[v.index] = 'upper' if dz >= 0 else 'lower'

# Count zone assignments
zone_counts = {'upper': 0, 'lower': 0}
for vi, zone in vertex_zone.items():
    if zone in zone_counts:
        zone_counts[zone] += 1

print(f"[v5] Zone map — upper: {zone_counts['upper']}, lower: {zone_counts['lower']}")

# Verify: seam vertices split correctly
seam_verts_upper = sum(1 for v in bm.verts
    if is_mouth_region(v.co) and abs(v.co.z - LIP_SEAM_Z) < SEAM_TOL
    and vertex_zone.get(v.index) == 'upper')
seam_verts_lower = sum(1 for v in bm.verts
    if is_mouth_region(v.co) and abs(v.co.z - LIP_SEAM_Z) < SEAM_TOL
    and vertex_zone.get(v.index) == 'lower')
print(f"[v5] Seam verts — upper: {seam_verts_upper}, lower: {seam_verts_lower}")

# Write mesh back
bm.to_mesh(obj.data)
bm.free()
obj.data.update()

print(f"[v5] Final mesh: {len(obj.data.vertices)} verts, {len(obj.data.polygons)} faces")

# ─── 6. Add viseme shape keys using face-connectivity zones ───
print(f"\n[v5] === ADDING VISEME MORPH TARGETS ===")

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

def zone_weight_v5(vert_index, co_z, zone, seam_z):
    """Zone weight using face-connectivity map for seam vertices."""
    if zone == 'all':
        return 1.0
    
    # Get this vertex's zone from the connectivity map
    v_zone = vertex_zone.get(vert_index, None)
    
    # If vertex not in mouth area, use position-based fallback
    if v_zone is None:
        margin = 0.003
        if zone == 'lower':
            if co_z > seam_z + margin: return 0.0
            if co_z < seam_z - margin: return 1.0
            return (seam_z + margin - co_z) / (2 * margin)
        elif zone == 'upper':
            if co_z < seam_z - margin: return 0.0
            if co_z > seam_z + margin: return 1.0
            return (co_z - seam_z + margin) / (2 * margin)
        return 1.0
    
    # For vertices with a known zone from face connectivity:
    if zone == 'lower':
        return 1.0 if v_zone == 'lower' else 0.0
    elif zone == 'upper':
        return 1.0 if v_zone == 'upper' else 0.0
    return 1.0

def compute_displacement_v5(vert_index, v_co, control_points, seam_z):
    total = Vector((0, 0, 0))
    for center, disp, radius, zone in control_points:
        zw = zone_weight_v5(vert_index, v_co.z, zone, seam_z)
        if zw < 0.001:
            continue
        dist = (v_co - center).length
        w = smooth_falloff(dist, radius) * zw
        if w > 0.001:
            total += disp * w
    return total


# Viseme definitions (same large magnitudes as v4)
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

# Track stats for viseme_aa specifically
aa_down_count = 0
aa_up_count = 0
aa_zero_seam = 0

for viseme_name, control_points in OCULUS_VISEMES.items():
    sk = obj.shape_key_add(name=viseme_name, from_mix=False)
    sk.value = 0.0

    moved = 0
    max_disp = 0.0

    for i, v in enumerate(mesh.vertices):
        co = v.co
        if not is_front_face(co):
            continue

        total_disp = compute_displacement_v5(i, co, control_points, LIP_SEAM_Z)

        if total_disp.length > 0.0001:
            sk.data[i].co = co + total_disp
            moved += 1
            if total_disp.length > max_disp:
                max_disp = total_disp.length
            
            # Track aa stats for seam verts
            if viseme_name == 'viseme_aa' and abs(co.z - LIP_SEAM_Z) < SEAM_TOL:
                if total_disp.z < -0.001:
                    aa_down_count += 1
                elif total_disp.z > 0.001:
                    aa_up_count += 1
                else:
                    aa_zero_seam += 1

    glb_max = max_disp * EXPORT_SCALE
    print(f"[v5] {viseme_name:12s}: {moved:4d} verts, "
          f"blender={max_disp:.5f} glb={glb_max:.5f}")

print(f"[v5] viseme_aa seam stats — pushed DOWN: {aa_down_count}, "
      f"pushed UP: {aa_up_count}, zero: {aa_zero_seam}")

# ─── 7. Export ───
print(f"\n[v5] Exporting to {OUTPUT_GLB}...")
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
    print(f"[v5] Shape keys: {len(names)}")

print("[v5] DONE!")
