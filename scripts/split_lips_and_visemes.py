"""
Blender script: Split the lip seam in Object_9 so mouth can OPEN.

Root cause: The face mesh (Object_9) has triangles that span from upper lip
vertices to lower lip vertices. Moving vertices apart just STRETCHES those
triangles — the mouth never opens. We must split the edges along the lip
seam to create two independent lip edges.

Steps:
  1. Import the original GLB
  2. Find Object_9 (face mesh)
  3. Identify the lip seam edge loop (edges crossing the lip boundary)
  4. Split those edges using bmesh — this duplicates seam vertices,
     creating separate upper/lower lip geometry
  5. Add viseme morph targets with LARGE displacements
  6. Export new GLB

Also: Object_14 and Object_15 are HAIR meshes, NOT teeth.
Only Object_9 needs mouth modification.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender --background \
    --python scripts/split_lips_and_visemes.py
"""
import bpy
import bmesh
from mathutils import Vector

INPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor.glb'
OUTPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_lipsync.glb'

# ─── 1. Import ───
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=INPUT_GLB)

obj = bpy.data.objects.get('Object_9')
if not obj:
    raise RuntimeError("Object_9 not found!")

print(f"[LipSplit] Object_9: {len(obj.data.vertices)} verts, "
      f"{len(obj.data.edges)} edges, {len(obj.data.polygons)} faces")

# ─── 2. Facial landmarks (Blender Z-up, Y-depth) ───
MOUTH_CENTER = Vector((0.0002, -0.1112, 1.5340))
UPPER_LIP    = Vector((0.0003, -0.1116, 1.5363))
LOWER_LIP    = Vector((0.0000, -0.1054, 1.5177))
LEFT_CORNER  = Vector((0.0503, -0.0616, 1.5282))
RIGHT_CORNER = Vector((-0.0518, -0.0633, 1.5282))
CHIN         = Vector((0.0028, -0.0994, 1.4948))

LIP_SEAM_Z = (UPPER_LIP.z + LOWER_LIP.z) / 2  # ~1.527
EXPORT_SCALE = 1.878

# Mouth bounds in Blender coordinates
MOUTH_X_RANGE = 0.06   # half-width from center
MOUTH_Z_MIN = 1.49     # below lower lip
MOUTH_Z_MAX = 1.56     # above upper lip
MOUTH_Y_MAX = 0.01     # front face only (Y < 0.01 is front)

print(f"[LipSplit] Lip seam Z: {LIP_SEAM_Z:.4f}")
print(f"[LipSplit] Upper lip Z: {UPPER_LIP.z:.4f}, Lower lip Z: {LOWER_LIP.z:.4f}")

# ─── 3. Split lip seam edges ───
# Need to set Object_9 as active and enter edit mode
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bm = bmesh.new()
bm.from_mesh(obj.data)
bm.edges.ensure_lookup_table()
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# Find edges that cross the lip seam
# An edge crosses the seam if one vert is above LIP_SEAM_Z and the other is below,
# AND both vertices are in the front mouth area
SEAM_TOLERANCE = 0.004  # vertices within this of seam are considered "on seam"

def is_mouth_area(co):
    """Is this vertex in the front mouth region?"""
    return (abs(co.x) < MOUTH_X_RANGE and
            co.y < MOUTH_Y_MAX and
            MOUTH_Z_MIN < co.z < MOUTH_Z_MAX)

def lip_side(co_z):
    """Returns 'upper', 'lower', or 'seam'"""
    if co_z > LIP_SEAM_Z + SEAM_TOLERANCE:
        return 'upper'
    elif co_z < LIP_SEAM_Z - SEAM_TOLERANCE:
        return 'lower'
    return 'seam'

cross_seam_edges = []
seam_vert_indices = set()

for edge in bm.edges:
    v0, v1 = edge.verts
    if not (is_mouth_area(v0.co) and is_mouth_area(v1.co)):
        continue
    
    s0 = lip_side(v0.co.z)
    s1 = lip_side(v1.co.z)
    
    crosses = False
    if s0 == 'upper' and s1 == 'lower':
        crosses = True
    elif s0 == 'lower' and s1 == 'upper':
        crosses = True
    elif s0 == 'seam' and s1 in ('upper', 'lower'):
        crosses = True
    elif s1 == 'seam' and s0 in ('upper', 'lower'):
        crosses = True
    elif s0 == 'seam' and s1 == 'seam':
        crosses = True
    
    if crosses:
        cross_seam_edges.append(edge)
        seam_vert_indices.add(v0.index)
        seam_vert_indices.add(v1.index)

print(f"[LipSplit] Found {len(cross_seam_edges)} cross-seam edges")
print(f"[LipSplit] Affecting {len(seam_vert_indices)} vertices")

for i, edge in enumerate(cross_seam_edges[:10]):
    v0, v1 = edge.verts
    print(f"[LipSplit]   Edge {i}: v{v0.index}(Z={v0.co.z:.4f},{lip_side(v0.co.z)}) — "
          f"v{v1.index}(Z={v1.co.z:.4f},{lip_side(v1.co.z)})")

if len(cross_seam_edges) == 0:
    print("[LipSplit] WARNING: No cross-seam edges found!")
else:
    # STEP A: Split edges to duplicate shared vertices at seam
    bmesh.ops.split_edges(bm, edges=cross_seam_edges)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    print(f"[LipSplit] After edge split: {len(bm.verts)} verts, {len(bm.faces)} faces")
    
    # STEP B: Delete faces that span the seam (have verts on BOTH sides)
    # These are the triangles that STRETCH when lips move apart
    cross_seam_faces = []
    for face in bm.faces:
        verts_in_mouth = [v for v in face.verts if is_mouth_area(v.co)]
        if len(verts_in_mouth) < 2:
            continue
        
        sides = set()
        for v in verts_in_mouth:
            d = v.co.z - LIP_SEAM_Z
            if d > 0.001:
                sides.add('upper')
            elif d < -0.001:
                sides.add('lower')
        
        if 'upper' in sides and 'lower' in sides:
            cross_seam_faces.append(face)
    
    print(f"[LipSplit] Found {len(cross_seam_faces)} faces spanning seam — DELETING")
    
    # Print some examples
    for i, face in enumerate(cross_seam_faces[:5]):
        zs = [f"{v.co.z:.4f}" for v in face.verts]
        print(f"[LipSplit]   Face {i}: Z=[{', '.join(zs)}]")
    
    if cross_seam_faces:
        bmesh.ops.delete(bm, geom=cross_seam_faces, context='FACES')
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        print(f"[LipSplit] After face delete: {len(bm.verts)} verts, {len(bm.faces)} faces")
    
    # Verify: count remaining cross-seam edges
    remaining = 0
    for edge in bm.edges:
        v0, v1 = edge.verts
        if not (is_mouth_area(v0.co) and is_mouth_area(v1.co)):
            continue
        d0 = v0.co.z - LIP_SEAM_Z
        d1 = v1.co.z - LIP_SEAM_Z
        if d0 * d1 < 0 and abs(d0) > 0.001 and abs(d1) > 0.001:
            remaining += 1
    print(f"[LipSplit] Remaining strict cross-seam edges: {remaining}")

# Write back to mesh
bm.to_mesh(obj.data)
bm.free()
obj.data.update()

verts_after = len(obj.data.vertices)
print(f"[LipSplit] Final mesh: {verts_after} verts")

print(f"\n[LipSplit] === ADDING VISEME MORPH TARGETS ===")

# ─── 5. Add viseme shape keys with LARGE mouth openings ───
# Only on Object_9 — Object_14/15 are hair, not teeth

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

# BIGGER magnitudes than v3 — mouth must VISIBLY open
# v3 had lower_lip down = 0.018 Blender = 0.034 GLB
# Now: lower_lip down = 0.040 Blender = 0.075 GLB  (2.2x bigger)
# And WIDER radii to affect more lip vertices

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
    print(f"[LipSplit] {viseme_name:12s}: {moved:4d} verts, "
          f"blender={max_disp:.5f} glb={glb_max:.5f}")


# ─── 6. Export ───
print(f"\n[LipSplit] Exporting to {OUTPUT_GLB}...")
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
if obj.data.shape_keys:
    names = [kb.name for kb in obj.data.shape_keys.key_blocks if kb.name != 'Basis']
    print(f"[LipSplit] Shape keys: {len(names)}: {', '.join(names[:5])}...")

print("[LipSplit] DONE!")
