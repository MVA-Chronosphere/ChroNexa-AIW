"""
Quick diagnostic: identify which meshes are teeth by checking vertex positions.
Teeth should be INSIDE the mouth (behind the lips, between upper and lower lip Z).
"""
import bpy
from mathutils import Vector

INPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor.glb'

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=INPUT_GLB)

print("\n=== MESH ANALYSIS: Finding teeth ===\n")

for obj in sorted(bpy.data.objects, key=lambda o: o.name):
    if obj.type != 'MESH':
        continue
    
    mesh = obj.data
    verts = mesh.vertices
    if len(verts) == 0:
        continue
    
    # Get vertex bounds
    xs = [v.co.x for v in verts]
    ys = [v.co.y for v in verts]  # Blender Y = depth (front = negative)
    zs = [v.co.z for v in verts]  # Blender Z = height
    
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    z_min, z_max = min(zs), max(zs)
    
    # Mouth area in Blender coords:
    # Z (height): 1.49 - 1.56 (lip area)
    # Y (depth): < 0 is front face
    # X (width): -0.06 to 0.06
    
    # Check if mesh is in mouth interior
    # Teeth are typically: behind lips (Y > -0.10, i.e. deeper than lip surface)
    # At mouth height (Z between lower lip and upper lip)
    mouth_verts = sum(1 for v in verts 
        if abs(v.co.x) < 0.06 
        and v.co.y > -0.12 and v.co.y < 0.0
        and 1.48 < v.co.z < 1.56)
    
    # Deeper inside mouth (behind lip surface at Y ~ -0.10)
    interior_verts = sum(1 for v in verts
        if abs(v.co.x) < 0.06
        and v.co.y > -0.09  # behind the lip surface
        and 1.48 < v.co.z < 1.56)
    
    # Check parent hierarchy for clues
    parent_name = obj.parent.name if obj.parent else "None"
    
    # Check for node names that hint at teeth
    is_candidate = (mouth_verts > len(verts) * 0.3 or 
                    'teeth' in obj.name.lower() or
                    'tooth' in obj.name.lower() or
                    'gum' in obj.name.lower())
    
    marker = " *** TEETH CANDIDATE ***" if is_candidate else ""
    
    print(f"{obj.name:20s} {len(verts):6d}v  "
          f"X[{x_min:+.3f},{x_max:+.3f}] "
          f"Y[{y_min:+.3f},{y_max:+.3f}] "
          f"Z[{z_min:+.3f},{z_max:+.3f}]  "
          f"mouth={mouth_verts} interior={interior_verts}  "
          f"parent={parent_name}{marker}")

# Also check the scene hierarchy
print("\n=== SCENE HIERARCHY ===\n")
def print_tree(obj, indent=0):
    marker = ""
    if obj.type == 'MESH':
        marker = f" [{len(obj.data.vertices)}v]"
    elif obj.type == 'ARMATURE':
        marker = " [ARMATURE]"
    print(f"{'  ' * indent}{obj.name}{marker} ({obj.type})")
    for child in sorted(obj.children, key=lambda c: c.name):
        print_tree(child, indent + 1)

for obj in bpy.data.objects:
    if obj.parent is None:
        print_tree(obj)
