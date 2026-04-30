"""
Blender script: Add 15 Oculus viseme shape keys using JAW ROTATION physics.

The key innovation: instead of translating vertices downward to open the mouth,
we ROTATE vertices around the jaw hinge (temporomandibular joint) — exactly how
a real human jaw works. This creates natural mouth opening arcs.

Lip-specific shapes (rounding, spreading, protrusion) use radial control-point
deformation layered on top of the jaw rotation.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/add_oculus_visemes.py
"""
import bpy
import math
from mathutils import Vector, Matrix

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

# ─── 3. Jaw rotation parameters ───
# The temporomandibular joint (TMJ) — the jaw hinge.
# Located at ear level, behind the jaw ramus.
# The jaw rotates around an axis running ear-to-ear (X axis) at this point.
JAW_PIVOT = Vector((0.0, -0.02, 1.56))  # Y slightly behind face surface, Z at jaw joint height

# Transition zone: vertices smoothly blend from no-rotation to full-rotation
JAW_BLEND_TOP = 1.545     # Above this Z: no jaw rotation (upper lip, nose, etc.)
JAW_BLEND_BOTTOM = 1.520  # Below this Z: full jaw rotation (chin, lower jaw)

# Only affect front-of-face vertices (not back of head)
FACE_Y_THRESHOLD = 0.02   # Vertices with Y > this are behind the head, skip them

# Mouth proximity radius for lip-specific deformations
MOUTH_REGION_RADIUS = 0.08


def jaw_rotation_weight(v_co):
    """Compute how much jaw rotation affects this vertex.
    Returns 0.0 for vertices above the lip line (upper face),
    1.0 for vertices below (lower jaw/chin),
    smooth blend in between."""
    # Skip vertices behind the face
    if v_co.y > FACE_Y_THRESHOLD:
        return 0.0
    
    z = v_co.z
    if z >= JAW_BLEND_TOP:
        return 0.0
    if z <= JAW_BLEND_BOTTOM:
        return 1.0
    
    # Smooth cosine blend in transition zone
    t = (JAW_BLEND_TOP - z) / (JAW_BLEND_TOP - JAW_BLEND_BOTTOM)
    return 0.5 - 0.5 * math.cos(t * math.pi)


def apply_jaw_rotation(v_co, angle_deg):
    """Rotate a vertex around the jaw pivot (X axis), simulating jaw opening.
    Returns the displacement vector."""
    weight = jaw_rotation_weight(v_co)
    if weight < 0.001:
        return Vector((0, 0, 0))
    
    # Position relative to jaw pivot
    rel = v_co - JAW_PIVOT
    
    # Rotate around X axis (ear-to-ear)
    angle_rad = math.radians(angle_deg) * weight
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # Rotation around X axis: Y' = Y*cos - Z*sin, Z' = Y*sin + Z*cos
    new_y = rel.y * cos_a - rel.z * sin_a
    new_z = rel.y * sin_a + rel.z * cos_a
    
    new_pos = JAW_PIVOT + Vector((rel.x, new_y, new_z))
    return new_pos - v_co


def smooth_falloff(distance, radius):
    """Smooth bell-curve falloff: 1.0 at center, 0.0 at radius."""
    if distance >= radius:
        return 0.0
    t = distance / radius
    return (1.0 - t * t) ** 2


def lip_deformation(v_co, control_points):
    """Compute lip-specific deformation from control points.
    Each control point: (position, displacement_vector, radius)"""
    total = Vector((0, 0, 0))
    for pos, disp, radius in control_points:
        dist = (v_co - pos).length
        weight = smooth_falloff(dist, radius)
        if weight > 0.001:
            total += disp * weight
    return total


# ─── 4. Oculus viseme definitions ───
# Each viseme: (jaw_angle_degrees, lip_control_points)
# Jaw angle: positive = open, 0 = closed
# Control points: (landmark, displacement_vector, radius)

S = 0.020  # Base scale for lip deformations

OCULUS_VISEMES = {
    # 0: viseme_aa — wide open "ah" (a, ɑ)
    'viseme_aa': {
        'jaw': 25.0,
        'lips': [
            (UPPER_LIP,    Vector((0, -0.2*S,  0.3*S)),   0.035),  # slight up
            (LEFT_CORNER,  Vector(( 0.4*S, 0,  0)),        0.03),   # slight spread
            (RIGHT_CORNER, Vector((-0.4*S, 0,  0)),        0.03),
        ]
    },

    # 1: viseme_E — mid open, spread "eh" (ɛ, e, ə)
    'viseme_E': {
        'jaw': 12.0,
        'lips': [
            (UPPER_LIP,    Vector((0, -0.2*S,  0.2*S)),   0.035),
            (LOWER_LIP,    Vector((0, -0.1*S, -0.2*S)),   0.035),
            (LEFT_CORNER,  Vector(( 1.0*S, 0,  0)),        0.04),   # spread wide
            (RIGHT_CORNER, Vector((-1.0*S, 0,  0)),        0.04),
        ]
    },

    # 2: viseme_I — narrow spread "ee" (i, ɪ)
    'viseme_I': {
        'jaw': 6.0,
        'lips': [
            (UPPER_LIP,    Vector((0, -0.1*S,  0.1*S)),   0.03),
            (LOWER_LIP,    Vector((0, -0.1*S, -0.1*S)),   0.03),
            (LEFT_CORNER,  Vector(( 1.5*S, 0,   0.2*S)),  0.045),  # wide spread + slight up
            (RIGHT_CORNER, Vector((-1.5*S, 0,   0.2*S)),  0.045),
        ]
    },

    # 3: viseme_O — rounded open "oh" (o, ɔ)
    'viseme_O': {
        'jaw': 18.0,
        'lips': [
            (UPPER_LIP,    Vector((0, -0.8*S,  0.3*S)),   0.04),   # forward + up
            (LOWER_LIP,    Vector((0, -0.8*S, -0.2*S)),   0.04),   # forward + slight down
            (LEFT_CORNER,  Vector((-0.8*S, -0.3*S, 0)),   0.045),  # inward (round)
            (RIGHT_CORNER, Vector(( 0.8*S, -0.3*S, 0)),   0.045),  # inward (round)
        ]
    },

    # 4: viseme_U — pursed "oo" (u, ʊ)
    'viseme_U': {
        'jaw': 8.0,
        'lips': [
            (UPPER_LIP,    Vector((0, -1.2*S,  0.2*S)),   0.04),   # strong forward protrusion
            (LOWER_LIP,    Vector((0, -1.2*S, -0.1*S)),   0.04),   # strong forward protrusion
            (LEFT_CORNER,  Vector((-1.5*S, -0.5*S, 0)),   0.05),   # strong inward (pucker)
            (RIGHT_CORNER, Vector(( 1.5*S, -0.5*S, 0)),   0.05),
        ]
    },

    # 5: viseme_PP — lips pressed together (p, b, m)
    'viseme_PP': {
        'jaw': 0.0,
        'lips': [
            (UPPER_LIP,    Vector((0,  0,     -0.8*S)),   0.035),  # upper lip down (press)
            (LOWER_LIP,    Vector((0,  0,      1.0*S)),   0.035),  # lower lip up (press)
            (CHIN,         Vector((0,  0,      0.3*S)),   0.03),   # chin up slightly
            (LEFT_CORNER,  Vector(( 0.2*S, 0,  0)),       0.025),  # very slight spread
            (RIGHT_CORNER, Vector((-0.2*S, 0,  0)),       0.025),
        ]
    },

    # 6: viseme_SS — teeth nearly closed, sibilant (s, z, ʃ)
    'viseme_SS': {
        'jaw': 3.0,
        'lips': [
            (UPPER_LIP,    Vector((0, -0.1*S,  0.1*S)),   0.03),
            (LOWER_LIP,    Vector((0, -0.1*S, -0.1*S)),   0.03),
            (LEFT_CORNER,  Vector(( 1.0*S, 0,   0.1*S)),  0.04),   # spread
            (RIGHT_CORNER, Vector((-1.0*S, 0,   0.1*S)),  0.04),
        ]
    },

    # 7: viseme_TH — dental, tongue between teeth (θ, ð)
    'viseme_TH': {
        'jaw': 7.0,
        'lips': [
            (UPPER_LIP,    Vector((0, -0.2*S,  0.2*S)),   0.035),
            (LOWER_LIP,    Vector((0, -0.2*S, -0.3*S)),   0.035),
            (LEFT_CORNER,  Vector(( 0.3*S, 0,  0)),       0.03),
            (RIGHT_CORNER, Vector((-0.3*S, 0,  0)),       0.03),
        ]
    },

    # 8: viseme_DD — alveolar stop (t, d)
    'viseme_DD': {
        'jaw': 8.0,
        'lips': [
            (UPPER_LIP,    Vector((0, -0.1*S,  0.15*S)),  0.03),
            (LOWER_LIP,    Vector((0, -0.1*S, -0.2*S)),   0.035),
            (LEFT_CORNER,  Vector(( 0.5*S, 0,  0)),       0.03),
            (RIGHT_CORNER, Vector((-0.5*S, 0,  0)),       0.03),
        ]
    },

    # 9: viseme_FF — labiodental, lower lip under teeth (f, v)
    'viseme_FF': {
        'jaw': 4.0,
        'lips': [
            (UPPER_LIP,    Vector((0,  0,     -0.1*S)),   0.03),   # stays mostly in place
            (LOWER_LIP,    Vector((0,  0.6*S,  0.8*S)),   0.04),   # lower lip UP and BACK (tucked under teeth)
            (CHIN,         Vector((0,  0,      0.2*S)),    0.025),  # chin up slightly
        ]
    },

    # 10: viseme_kk — velar stop, moderate open (k, g)
    'viseme_kk': {
        'jaw': 10.0,
        'lips': [
            (UPPER_LIP,    Vector((0, -0.1*S,  0.1*S)),   0.03),
            (LOWER_LIP,    Vector((0, -0.1*S, -0.2*S)),   0.035),
            (LEFT_CORNER,  Vector(( 0.3*S, 0,  0)),       0.03),
            (RIGHT_CORNER, Vector((-0.3*S, 0,  0)),       0.03),
        ]
    },

    # 11: viseme_nn — nasal, slight open (n, ŋ)
    'viseme_nn': {
        'jaw': 6.0,
        'lips': [
            (UPPER_LIP,    Vector((0, -0.1*S,  0.1*S)),   0.03),
            (LOWER_LIP,    Vector((0, -0.1*S, -0.15*S)),  0.03),
            (LEFT_CORNER,  Vector(( 0.3*S, 0,  0)),       0.025),
            (RIGHT_CORNER, Vector((-0.3*S, 0,  0)),       0.025),
        ]
    },

    # 12: viseme_RR — liquid, relaxed slight open (r, l, w)
    'viseme_RR': {
        'jaw': 8.0,
        'lips': [
            (UPPER_LIP,    Vector((0, -0.3*S,  0.15*S)),  0.035),  # slight forward
            (LOWER_LIP,    Vector((0, -0.3*S, -0.15*S)),  0.035),
            (LEFT_CORNER,  Vector(( 0.2*S, -0.1*S, 0)),   0.03),
            (RIGHT_CORNER, Vector((-0.2*S, -0.1*S, 0)),   0.03),
        ]
    },

    # 13: viseme_CH — affricate, slight round (tʃ, dʒ)
    'viseme_CH': {
        'jaw': 6.0,
        'lips': [
            (UPPER_LIP,    Vector((0, -0.4*S,  0.15*S)),  0.035),  # forward (slight round)
            (LOWER_LIP,    Vector((0, -0.4*S, -0.15*S)),  0.035),
            (LEFT_CORNER,  Vector((-0.4*S, -0.2*S, 0)),   0.04),   # slight inward
            (RIGHT_CORNER, Vector(( 0.4*S, -0.2*S, 0)),   0.04),
        ]
    },

    # 14: viseme_sil — silence / rest (no deformation)
    'viseme_sil': {
        'jaw': 0.0,
        'lips': []
    },
}


# ─── 5. Create shape keys ───
if not mesh.shape_keys:
    head_obj.shape_key_add(name='Basis', from_mix=False)

for viseme_name, viseme_def in OCULUS_VISEMES.items():
    jaw_angle = viseme_def['jaw']
    lip_controls = viseme_def['lips']

    sk = head_obj.shape_key_add(name=viseme_name, from_mix=False)
    sk.value = 0.0

    moved = 0
    max_disp = 0.0

    for i, v in enumerate(verts):
        co = v.co
        total_disp = Vector((0, 0, 0))

        # Layer 1: Jaw rotation
        if jaw_angle > 0.01:
            jaw_disp = apply_jaw_rotation(co, jaw_angle)
            total_disp += jaw_disp

        # Layer 2: Lip-specific deformations (applied on top)
        if lip_controls:
            lip_disp = lip_deformation(co, lip_controls)
            total_disp += lip_disp

        if total_disp.length > 0.0001:
            sk.data[i].co = co + total_disp
            moved += 1
            if total_disp.length > max_disp:
                max_disp = total_disp.length

    print(f"[Visemes] {viseme_name:12s}: {moved:5d} verts moved, max displacement: {max_disp:.5f}")


# ─── 6. Export ───
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
print(f"[Visemes] Done! Created {len(names)} shape keys: {names}")
