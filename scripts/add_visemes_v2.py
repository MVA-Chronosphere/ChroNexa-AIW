"""
Blender script: Add Rhubarb viseme shape keys using control-point deformation.
Uses smooth radial falloff from facial landmarks for natural-looking mouth shapes.

Run: /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/add_visemes_v2.py
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

# ─── 2. Facial landmarks (from analysis) ───
MOUTH_CENTER   = Vector((0.0002, -0.1112, 1.5340))
UPPER_LIP      = Vector((0.0003, -0.1116, 1.5363))
LOWER_LIP      = Vector((0.0000, -0.1054, 1.5177))
LEFT_CORNER    = Vector((0.0503, -0.0616, 1.5282))
RIGHT_CORNER   = Vector((-0.0518, -0.0633, 1.5282))
CHIN           = Vector((0.0028, -0.0994, 1.4948))

# Derived
MOUTH_WIDTH = (LEFT_CORNER - RIGHT_CORNER).length  # ~0.102
LIP_HEIGHT = UPPER_LIP.z - LOWER_LIP.z             # ~0.019

print(f"[Visemes] Mouth width: {MOUTH_WIDTH:.4f}, lip height: {LIP_HEIGHT:.4f}")
print(f"[Visemes] Mouth center: {MOUTH_CENTER}")


def smooth_falloff(distance, radius):
    """Smooth bell-curve falloff: 1.0 at center, 0.0 at radius."""
    if distance >= radius:
        return 0.0
    t = distance / radius
    # Cubic ease-out for smooth natural falloff
    return (1.0 - t * t) * (1.0 - t * t)


def compute_displacement(v_co, control_points):
    """Compute total displacement for a vertex from multiple control points.
    Each control point: (position, displacement_vector, influence_radius)
    """
    total = Vector((0, 0, 0))
    for pos, disp, radius in control_points:
        dist = (v_co - pos).length
        weight = smooth_falloff(dist, radius)
        if weight > 0.001:
            total += disp * weight
    return total


# ─── 3. Viseme definitions using control points ───
# Each viseme is a list of (landmark_position, displacement_vector, radius)
# Displacement in local space: X=left/right, Y=front(neg)/back(pos), Z=up/down

S = 0.015  # Scale factor for displacements

VISEMES = {
    # A: MBP — lips pressed together (M, B, P sounds)
    'viseme_A': [
        (UPPER_LIP,    Vector((0,  0,      -1.0*S)),  0.04),  # upper lip down
        (LOWER_LIP,    Vector((0,  0,       1.2*S)),   0.04),  # lower lip up
        (CHIN,         Vector((0,  0,       0.5*S)),   0.04),  # chin up slightly
        (LEFT_CORNER,  Vector((0,  0,       0)),       0.03),
        (RIGHT_CORNER, Vector((0,  0,       0)),       0.03),
    ],

    # B: EE — wide spread (teeth visible, as in "see")
    'viseme_B': [
        (UPPER_LIP,    Vector((0, -0.3*S,   0.8*S)),   0.04),  # upper lip up + forward
        (LOWER_LIP,    Vector((0, -0.3*S,  -0.6*S)),   0.04),  # lower lip down + forward
        (LEFT_CORNER,  Vector(( 1.5*S, 0,   0)),       0.04),  # spread left
        (RIGHT_CORNER, Vector((-1.5*S, 0,   0)),       0.04),  # spread right
        (CHIN,         Vector((0,  0,      -0.4*S)),   0.04),  # chin down slightly
    ],

    # C: EH/AH — slightly open mouth (as in "bed", "bad")
    'viseme_C': [
        (UPPER_LIP,    Vector((0, -0.2*S,   0.5*S)),   0.04),  # upper lip up
        (LOWER_LIP,    Vector((0, -0.2*S,  -1.5*S)),   0.05),  # lower lip down
        (LEFT_CORNER,  Vector(( 0.5*S, 0,   0)),       0.03),  # slight spread
        (RIGHT_CORNER, Vector((-0.5*S, 0,   0)),       0.03),
        (CHIN,         Vector((0,  0,      -1.2*S)),   0.05),  # chin down
    ],

    # D: AI — wide open mouth (as in "my", "eye")
    'viseme_D': [
        (UPPER_LIP,    Vector((0, -0.3*S,   0.8*S)),   0.05),  # upper lip up
        (LOWER_LIP,    Vector((0, -0.3*S,  -2.5*S)),   0.06),  # lower lip way down
        (LEFT_CORNER,  Vector(( 0.8*S, 0,   0)),       0.04),  # slight spread
        (RIGHT_CORNER, Vector((-0.8*S, 0,   0)),       0.04),
        (CHIN,         Vector((0,  0,      -2.5*S)),   0.06),  # chin way down
    ],

    # E: OH — rounded open (as in "go", "oh")
    'viseme_E': [
        (UPPER_LIP,    Vector((0, -0.8*S,   0.6*S)),   0.04),  # up + forward (round)
        (LOWER_LIP,    Vector((0, -0.8*S,  -1.5*S)),   0.05),  # down + forward
        (LEFT_CORNER,  Vector((-0.8*S, -0.3*S, 0)),    0.04),  # corners inward (pucker)
        (RIGHT_CORNER, Vector(( 0.8*S, -0.3*S, 0)),    0.04),
        (CHIN,         Vector((0,  0,      -1.5*S)),   0.05),  # chin down
    ],

    # F: OO/W — tight round pucker (as in "you", "who")
    'viseme_F': [
        (UPPER_LIP,    Vector((0, -1.5*S,   0.3*S)),   0.04),  # push forward
        (LOWER_LIP,    Vector((0, -1.5*S,  -0.5*S)),   0.04),  # push forward + slight down
        (LEFT_CORNER,  Vector((-1.5*S, -0.5*S, 0)),    0.05),  # corners inward (pucker)
        (RIGHT_CORNER, Vector(( 1.5*S, -0.5*S, 0)),    0.05),
        (CHIN,         Vector((0,  0,      -0.4*S)),   0.04),
    ],

    # G: F/V — bottom lip tucked under top teeth
    'viseme_G': [
        (UPPER_LIP,    Vector((0,  0,      -0.2*S)),   0.03),  # upper lip stays
        (LOWER_LIP,    Vector((0,  0.8*S,   1.0*S)),   0.04),  # lower lip UP and BACK (tucked)
        (LEFT_CORNER,  Vector((0,  0,       0)),       0.02),
        (RIGHT_CORNER, Vector((0,  0,       0)),       0.02),
        (CHIN,         Vector((0,  0,       0.3*S)),   0.03),  # chin up slightly
    ],

    # H: L/TH — tongue tip position, slight open
    'viseme_H': [
        (UPPER_LIP,    Vector((0, -0.2*S,   0.3*S)),   0.04),  # slight up
        (LOWER_LIP,    Vector((0, -0.2*S,  -1.0*S)),   0.04),  # moderate down
        (LEFT_CORNER,  Vector((0,  0,       0)),       0.02),
        (RIGHT_CORNER, Vector((0,  0,       0)),       0.02),
        (CHIN,         Vector((0,  0,      -0.8*S)),   0.04),  # chin down
    ],
}

# ─── 4. Create shape keys ───
if not mesh.shape_keys:
    head_obj.shape_key_add(name='Basis', from_mix=False)
basis = mesh.shape_keys.key_blocks['Basis']

for viseme_name, control_points in VISEMES.items():
    sk = head_obj.shape_key_add(name=viseme_name, from_mix=False)
    sk.value = 0.0

    moved = 0
    max_disp = 0.0
    for i, v in enumerate(verts):
        co = v.co
        disp = compute_displacement(co, control_points)
        if disp.length > 0.0001:
            sk.data[i].co = co + disp
            moved += 1
            if disp.length > max_disp:
                max_disp = disp.length
        # else: sk.data[i].co is already == basis

    print(f"[Visemes] {viseme_name}: {moved} verts moved, max displacement: {max_disp:.5f}")


# ─── 5. Export ───
print(f"[Visemes] Exporting to {OUTPUT_GLB}...")
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

names = [kb.name for kb in mesh.shape_keys.key_blocks]
print(f"[Visemes] Done! Shape keys: {names}")
