"""Quick probe: print bone positions and body mesh bounds to plan coat vertex selection."""
import bpy
from mathutils import Vector

INPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_lipsync.glb'

bpy.ops.wm.read_factory_settings(use_empty=True)
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

bpy.ops.import_scene.gltf(filepath=INPUT_GLB)

armature = None
body = None
outfit = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        armature = obj
    elif obj.type == 'MESH':
        n = (obj.name + ' ' + (obj.data.name if obj.data else '')).lower()
        if 'avatarbody' in n or obj.name == 'Object_7':
            body = obj
        if 'outfit' in n or obj.name == 'Object_17':
            outfit = obj

print(f"\nArmature: {armature.name}")
print(f"Body: {body.name} ({len(body.data.vertices)} verts)")
print(f"Outfit: {outfit.name} ({len(outfit.data.vertices)} verts)")

# Print key bone positions
key_bones = ['Hips_01', 'Spine_02', 'Spine1_03', 'Spine2_04', 'Neck_05', 'Neck_06', 'Neck_07', 'Head_08',
             'LeftShoulder_012', 'LeftArm_013', 'LeftForeArm_014', 'LeftHand_017',
             'RightShoulder_038', 'RightArm_039', 'RightForeArm_040', 'RightHand_043',
             'LeftUpLeg_064', 'RightUpLeg_069']
print("\n--- Bone positions (world) ---")
for name in key_bones:
    b = armature.data.bones.get(name)
    if b:
        head_w = armature.matrix_world @ b.head_local
        print(f"  {name:30s} head=({head_w.x:.4f}, {head_w.y:.4f}, {head_w.z:.4f})")

# Body mesh bounds
print("\n--- AvatarBody bounds ---")
verts_w = [body.matrix_world @ v.co for v in body.data.vertices]
min_x = min(v.x for v in verts_w)
max_x = max(v.x for v in verts_w)
min_y = min(v.y for v in verts_w)
max_y = max(v.y for v in verts_w)
min_z = min(v.z for v in verts_w)
max_z = max(v.z for v in verts_w)
print(f"  X: {min_x:.4f} to {max_x:.4f}")
print(f"  Y: {min_y:.4f} to {max_y:.4f}")
print(f"  Z: {min_z:.4f} to {max_z:.4f}")

# Count verts in torso region (between hips and neck Y)
hips = armature.matrix_world @ armature.data.bones['Hips_01'].head_local
neck = armature.matrix_world @ armature.data.bones['Neck_05'].head_local
print(f"\n--- Torso region (Hips to Neck) ---")
print(f"  Hips Y: {hips.y:.4f}, Neck Y: {neck.y:.4f}")
torso_count = sum(1 for v in verts_w if hips.y <= v.y <= neck.y)
print(f"  Body verts in torso Y range: {torso_count}/{len(verts_w)}")

# Also include some shoulder/upper arm area
lshoulder = armature.matrix_world @ armature.data.bones['LeftShoulder_012'].head_local
rshoulder = armature.matrix_world @ armature.data.bones['RightShoulder_038'].head_local
lforearm = armature.matrix_world @ armature.data.bones['LeftForeArm_014'].head_local
rforearm = armature.matrix_world @ armature.data.bones['RightForeArm_040'].head_local
print(f"  LShoulder X: {lshoulder.x:.4f}, RShoulder X: {rshoulder.x:.4f}")
print(f"  LForeArm X: {lforearm.x:.4f}, RForeArm X: {rforearm.x:.4f}")

# Outfit mesh vertex groups
print(f"\n--- Outfit vertex groups ---")
for vg in outfit.vertex_groups[:10]:
    print(f"  {vg.name}")
print(f"  ... total: {len(outfit.vertex_groups)}")

# Check body vertex groups
print(f"\n--- Body vertex groups ---")
for vg in body.vertex_groups[:10]:
    print(f"  {vg.name}")
print(f"  ... total: {len(body.vertex_groups)}")
