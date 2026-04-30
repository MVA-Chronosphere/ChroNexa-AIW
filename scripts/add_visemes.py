"""
Blender script to add Rhubarb lip-sync viseme shape keys to the Indian Doctor avatar.
Run with: /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/add_visemes.py

The model has NO morph targets, so we create them by displacing vertices
in the mouth/lip region of the head mesh (Object_16, 48815 verts).

Local space coordinates (Object_16):
  X: [-0.1475, 0.1214]  (left-right)
  Y: [-0.1140, 0.1240]  (front-back, front = negative Y)
  Z: [1.3573, 1.7148]   (up-down)
  Mouth area: Z ~1.44 to 1.50

Rhubarb visemes: A(MBP), B(EE), C(EH), D(AI), E(OH), F(OO), G(FV), H(L), X(rest)
"""
import bpy
import math
import os
from mathutils import Vector

INPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor.glb'
OUTPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_lipsync.glb'

# ─── 1. Import the model ───
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=INPUT_GLB)

head_obj = bpy.data.objects.get('Object_9')
if not head_obj:
    raise RuntimeError("Could not find Object_9 (head mesh)")

mesh = head_obj.data
verts = mesh.vertices

# ─── 2. Compute mouth geometry parameters ───
all_z = [v.co.z for v in verts]
all_x = [v.co.x for v in verts]
z_min, z_max = min(all_z), max(all_z)
z_range = z_max - z_min
x_center = (max(all_x) + min(all_x)) / 2.0

# Mouth zone boundaries (empirically determined from Object_9 vertex analysis)
# Head mesh local space: X [-0.11, 0.11], Y [-0.12, 0.10], Z [1.357, 1.702]
# Front face = negative Y.  Mouth area ~Z 27-42%
# Mouth zone boundaries (from face profile analysis of Object_9)
# Face profile (front_Y by Z%):
#   Z 39% = chin (-0.099), Z 44% = lower lip (-0.105), 
#   Z 48% = mouth crease (-0.110), Z 52% = upper lip (-0.112),
#   Z 56% = nose base (-0.119), Z 59% = nose tip (-0.124)
MOUTH_Z_LOW = z_min + z_range * 0.42    # bottom of lower lip
MOUTH_Z_HIGH = z_min + z_range * 0.55   # top of upper lip / nose base
MOUTH_Z_CENTER = z_min + z_range * 0.48 # lip line (mouth crease)
MOUTH_X_HALF_WIDTH = 0.05   # half-width of mouth area
MOUTH_FRONT_Y = 0.00        # include front-facing vertices (front = negative Y)

# Extended zone for jaw movement
JAW_Z_LOW = z_min + z_range * 0.36      # jaw / chin area (below lips)
JAW_Z_HIGH = MOUTH_Z_LOW                # bottom of lip region

print(f"[Visemes] Head Z range: {z_min:.4f} - {z_max:.4f} ({z_range:.4f})")
print(f"[Visemes] Mouth zone: Z {MOUTH_Z_LOW:.4f} - {MOUTH_Z_HIGH:.4f}, center {MOUTH_Z_CENTER:.4f}")
print(f"[Visemes] X center: {x_center:.4f}")


def classify_vertex(v):
    """Classify a vertex into mouth region categories.
    Returns dict with weights for: upper_lip, lower_lip, corner, jaw, chin
    """
    co = v.co
    result = {
        'upper_lip': 0.0,
        'lower_lip': 0.0,
        'corner': 0.0,
        'jaw': 0.0,
        'chin': 0.0,
    }

    x_dist = abs(co.x - x_center)

    # Must be in front half of the head
    if co.y > MOUTH_FRONT_Y:
        return result

    # Front factor: 1.0 at most-forward, fading to 0.0 at MOUTH_FRONT_Y
    # The front of the face has the most negative Y values (~-0.12)
    # Use a gentle falloff so front-facing vertices get full weight
    y_min_face = -0.12  # most forward Y in head mesh
    front_factor = max(0, min(1, (MOUTH_FRONT_Y - co.y) / (MOUTH_FRONT_Y - y_min_face)))

    # ── Upper lip region ──
    if MOUTH_Z_CENTER <= co.z <= MOUTH_Z_HIGH and x_dist < MOUTH_X_HALF_WIDTH:
        z_factor = 1.0 - abs(co.z - MOUTH_Z_CENTER) / (MOUTH_Z_HIGH - MOUTH_Z_CENTER)
        x_factor = 1.0 - (x_dist / MOUTH_X_HALF_WIDTH)
        result['upper_lip'] = z_factor * x_factor * front_factor

    # ── Lower lip region ──
    if MOUTH_Z_LOW <= co.z <= MOUTH_Z_CENTER and x_dist < MOUTH_X_HALF_WIDTH:
        z_factor = 1.0 - abs(co.z - MOUTH_Z_CENTER) / (MOUTH_Z_CENTER - MOUTH_Z_LOW)
        x_factor = 1.0 - (x_dist / MOUTH_X_HALF_WIDTH)
        result['lower_lip'] = z_factor * x_factor * front_factor

    # ── Lip corners ──
    if MOUTH_Z_LOW <= co.z <= MOUTH_Z_HIGH:
        corner_width = MOUTH_X_HALF_WIDTH * 1.5
        if 0.02 < x_dist < corner_width:
            z_center_dist = abs(co.z - MOUTH_Z_CENTER)
            z_factor = max(0, 1.0 - z_center_dist / ((MOUTH_Z_HIGH - MOUTH_Z_LOW) * 0.5))
            x_factor = max(0, 1.0 - abs(x_dist - 0.04) / 0.04)
            result['corner'] = z_factor * x_factor * front_factor

    # ── Jaw region ──
    if JAW_Z_LOW <= co.z <= MOUTH_Z_LOW and x_dist < MOUTH_X_HALF_WIDTH * 2:
        z_factor = (co.z - JAW_Z_LOW) / (MOUTH_Z_LOW - JAW_Z_LOW)  # stronger near mouth
        x_factor = 1.0 - (x_dist / (MOUTH_X_HALF_WIDTH * 2))
        result['jaw'] = z_factor * x_factor * front_factor * 0.8

    # ── Chin ──
    if z_min + z_range * 0.08 <= co.z <= JAW_Z_LOW and x_dist < MOUTH_X_HALF_WIDTH * 2.5:
        z_factor = (co.z - (z_min + z_range * 0.08)) / (JAW_Z_LOW - (z_min + z_range * 0.08))
        result['chin'] = z_factor * front_factor * 0.5

    return result


# ─── 3. Pre-classify all vertices ───
print("[Visemes] Classifying vertices...")
vert_classes = [classify_vertex(v) for v in verts]

# Count affected vertices
affected = sum(1 for vc in vert_classes if any(v > 0.01 for v in vc.values()))
print(f"[Visemes] {affected} vertices in mouth/jaw region (of {len(verts)} total)")

# ─── 4. Create Basis shape key ───
if not mesh.shape_keys:
    head_obj.shape_key_add(name='Basis', from_mix=False)
basis = mesh.shape_keys.key_blocks['Basis']

# ─── 5. Define viseme displacements ───
# Each viseme maps to offsets applied to classified vertex regions
# Offsets are (dx, dy, dz) in local space
# Positive Z = up, Negative Y = forward, Positive/Negative X = right/left

SCALE = 0.06  # Base displacement scale — must be large enough to see on the face

VISEME_DEFS = {
    # A: MBP - lips pressed together (closed mouth)
    'viseme_A': {
        'upper_lip': (0, 0, -0.6 * SCALE),      # upper lip moves down
        'lower_lip': (0, 0,  0.6 * SCALE),       # lower lip moves up
        'corner':    (0, 0,  0),
        'jaw':       (0, 0,  0.3 * SCALE),       # jaw up slightly
        'chin':      (0, 0,  0.2 * SCALE),
    },
    # B: EE - wide/spread (teeth showing)
    'viseme_B': {
        'upper_lip': (0, -0.3 * SCALE, 0.3 * SCALE),   # up + slightly forward
        'lower_lip': (0, -0.2 * SCALE, -0.3 * SCALE),   # down + slightly forward
        'corner':    ('spread', -0.2 * SCALE, 0),        # spread sideways
        'jaw':       (0, 0, -0.3 * SCALE),               # slight jaw opening
        'chin':      (0, 0, -0.2 * SCALE),
    },
    # C: EH/AH - slightly open
    'viseme_C': {
        'upper_lip': (0, -0.2 * SCALE, 0.4 * SCALE),
        'lower_lip': (0, -0.2 * SCALE, -0.7 * SCALE),
        'corner':    (0, 0, 0),
        'jaw':       (0, 0, -0.7 * SCALE),
        'chin':      (0, 0, -0.5 * SCALE),
    },
    # D: AI - wide open mouth
    'viseme_D': {
        'upper_lip': (0, -0.3 * SCALE, 0.5 * SCALE),
        'lower_lip': (0, -0.3 * SCALE, -1.2 * SCALE),
        'corner':    ('spread_slight', 0, 0),
        'jaw':       (0, 0, -1.2 * SCALE),
        'chin':      (0, 0, -0.8 * SCALE),
    },
    # E: OH - rounded, open
    'viseme_E': {
        'upper_lip': (0, -0.5 * SCALE, 0.4 * SCALE),
        'lower_lip': (0, -0.5 * SCALE, -0.8 * SCALE),
        'corner':    ('pucker', -0.3 * SCALE, 0),
        'jaw':       (0, 0, -0.8 * SCALE),
        'chin':      (0, 0, -0.5 * SCALE),
    },
    # F: OO/W - tight round (puckered)
    'viseme_F': {
        'upper_lip': (0, -0.8 * SCALE, 0.2 * SCALE),    # push forward
        'lower_lip': (0, -0.8 * SCALE, -0.3 * SCALE),
        'corner':    ('pucker_tight', -0.5 * SCALE, 0),
        'jaw':       (0, 0, -0.3 * SCALE),
        'chin':      (0, 0, -0.2 * SCALE),
    },
    # G: F/V - lower lip tucked
    'viseme_G': {
        'upper_lip': (0, 0, -0.1 * SCALE),
        'lower_lip': (0, 0.4 * SCALE, 0.5 * SCALE),     # lower lip tucks IN and UP
        'corner':    (0, 0, 0),
        'jaw':       (0, 0, 0.2 * SCALE),
        'chin':      (0, 0, 0.1 * SCALE),
    },
    # H: L/TH - slight open, tongue position
    'viseme_H': {
        'upper_lip': (0, -0.1 * SCALE, 0.2 * SCALE),
        'lower_lip': (0, -0.1 * SCALE, -0.4 * SCALE),
        'corner':    (0, 0, 0),
        'jaw':       (0, 0, -0.4 * SCALE),
        'chin':      (0, 0, -0.3 * SCALE),
    },
}


def apply_corner_special(x_dist, x_sign, mode):
    """Compute X displacement for lip corners based on mode."""
    if mode == 'spread':
        return x_sign * 0.7 * SCALE
    elif mode == 'spread_slight':
        return x_sign * 0.4 * SCALE
    elif mode == 'pucker':
        return -x_sign * 0.4 * SCALE
    elif mode == 'pucker_tight':
        return -x_sign * 0.6 * SCALE
    return 0


# ─── 6. Create shape keys for each viseme ───
for viseme_name, regions in VISEME_DEFS.items():
    sk = head_obj.shape_key_add(name=viseme_name, from_mix=False)
    sk.value = 0.0

    for i, v in enumerate(verts):
        vc = vert_classes[i]
        co = v.co.copy()
        dx, dy, dz = 0.0, 0.0, 0.0

        for region_name, (ox, oy, oz) in regions.items():
            weight = vc.get(region_name, 0.0)
            if weight < 0.01:
                continue

            if region_name == 'corner' and isinstance(ox, str):
                x_sign = 1.0 if co.x > x_center else -1.0
                x_d = co.x - x_center
                actual_dx = apply_corner_special(abs(x_d), x_sign, ox)
                dx += actual_dx * weight
                dy += oy * weight
                dz += oz * weight
            else:
                dx += ox * weight
                dy += oy * weight
                dz += oz * weight

        sk.data[i].co = co + Vector((dx, dy, dz))

    # Verify the shape key has non-zero displacements
    moved = sum(1 for i in range(len(verts))
                if (sk.data[i].co - basis.data[i].co).length > 0.0001)
    print(f"[Visemes] Created {viseme_name}: {moved} vertices displaced")


# ─── 7. Export with morph targets ───
print(f"[Visemes] Exporting to {OUTPUT_GLB}...")

# Select all objects for export
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

print(f"[Visemes] Done! Exported to {OUTPUT_GLB}")
print(f"[Visemes] Shape keys: {[kb.name for kb in mesh.shape_keys.key_blocks]}")
