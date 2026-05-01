"""
Make Doctor Avatar — Blender Script
====================================
Modifies the existing avatar GLB to look like a doctor:
1. Changes outfit mesh material to white (lab coat look)
2. Adds a simple stethoscope from basic primitives
3. Parents stethoscope to existing bones
4. Exports a new GLB with everything intact (bones, morphs, vertex groups)

Usage:
  /Applications/Blender.app/Contents/MacOS/Blender --background \
    --python scripts/make_doctor_avatar.py
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

INPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_lipsync.glb'
OUTPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_final.glb'

print("=" * 60)
print("  Make Doctor Avatar — Blender Script")
print("=" * 60)


# ── Step 0: Clean scene ──
print("\n[Step 0] Cleaning scene...")
bpy.ops.wm.read_factory_settings(use_empty=True)
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ── Step 1: Import avatar ──
print("\n[Step 1] Importing avatar...")
bpy.ops.import_scene.gltf(filepath=INPUT_GLB)

# Find key objects
armature = None
outfit_mesh = None
all_meshes = []

for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        armature = obj
    elif obj.type == 'MESH':
        all_meshes.append(obj)
        name_lower = (obj.name + (obj.data.name if obj.data else '')).lower()
        if 'outfit' in name_lower:
            outfit_mesh = obj

if not armature:
    raise RuntimeError("No armature found in avatar!")

# Fallback: find outfit by name Object_17
if not outfit_mesh:
    for obj in all_meshes:
        if obj.name == 'Object_17':
            outfit_mesh = obj
            break

if not outfit_mesh:
    raise RuntimeError("No outfit mesh found!")

print(f"  Armature: {armature.name}")
print(f"  Outfit mesh: {outfit_mesh.name} ({len(outfit_mesh.data.vertices)} verts)")
print(f"  Total meshes: {len(all_meshes)}")
print(f"  Bones: {len(armature.data.bones)}")


# ── Step 2: Change outfit to white lab coat material ──
print("\n[Step 2] Creating white lab coat material...")
coat_mat = bpy.data.materials.new(name="WhiteLabCoat")
coat_mat.use_nodes = True
bsdf = coat_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    # Clean white with very slight warm tint
    bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.93, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.55
    bsdf.inputs['Metallic'].default_value = 0.0
    # Slight subsurface for cloth-like feel
    if 'Subsurface Weight' in bsdf.inputs:
        bsdf.inputs['Subsurface Weight'].default_value = 0.02

# Replace outfit materials
outfit_mesh.data.materials.clear()
outfit_mesh.data.materials.append(coat_mat)
print(f"  Applied white material to {outfit_mesh.name}")


# ── Step 3: Find bone positions for stethoscope placement ──
print("\n[Step 3] Finding bone positions...")

# Get bone world positions from the armature
def get_bone_head_world(bone_name):
    """Get bone head position in world space."""
    bone = armature.data.bones.get(bone_name)
    if bone:
        return armature.matrix_world @ bone.head_local
    return None

def get_bone_tail_world(bone_name):
    """Get bone tail position in world space."""
    bone = armature.data.bones.get(bone_name)
    if bone:
        return armature.matrix_world @ bone.tail_local
    return None

# Find relevant bones - use the naming from our avatar
# Neck_05, Neck_06, Neck_07, Head_08
# Spine2_04 (upper chest)
neck_pos = get_bone_head_world('Neck_05')
spine2_pos = get_bone_head_world('Spine2_04')
head_pos = get_bone_head_world('Head_08')

if not neck_pos or not spine2_pos:
    # Try alternative bone names
    for bone in armature.data.bones:
        name = bone.name.lower()
        if 'neck' in name and not neck_pos:
            neck_pos = armature.matrix_world @ bone.head_local
        if 'spine2' in name and not spine2_pos:
            spine2_pos = armature.matrix_world @ bone.head_local

print(f"  Neck position: {neck_pos}")
print(f"  Upper chest position: {spine2_pos}")


# ── Step 4: Create stethoscope ──
print("\n[Step 4] Creating stethoscope...")

# Calculate placement relative to avatar
if neck_pos and spine2_pos:
    chest_center = (neck_pos + spine2_pos) / 2
    body_front_z = chest_center.z + 0.08  # slightly in front of body
    
    # Stethoscope dimensions scaled to avatar
    avatar_scale = abs(neck_pos.y - spine2_pos.y)  # neck-to-chest distance
    tube_thickness = avatar_scale * 0.03
    
    steth_parts = []
    
    # ── 4a: Chest piece (disc/diaphragm) ──
    # Small flat cylinder at chest level
    bpy.ops.mesh.primitive_cylinder_add(
        radius=avatar_scale * 0.12,
        depth=avatar_scale * 0.03,
        location=(chest_center.x, chest_center.y - avatar_scale * 0.15, body_front_z + 0.02),
        rotation=(math.pi/2, 0, 0)
    )
    chest_piece = bpy.context.active_object
    chest_piece.name = "Steth_ChestPiece"
    steth_parts.append(chest_piece)
    
    # ── 4b: Tube from chest piece up to neck ──
    # Create a curve-based tube for the main stethoscope tube
    curve_data = bpy.data.curves.new('StethTubeCurve', type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = tube_thickness
    curve_data.bevel_resolution = 4
    
    spline = curve_data.splines.new('BEZIER')
    # Points: chest piece → up center chest → over one shoulder → behind neck → over other shoulder → back down
    # Simplified: just the front tube going up from chest to split at neck
    
    # Main tube: chest to neck center
    tube_points = [
        (chest_center.x, chest_center.y - avatar_scale * 0.15, body_front_z + 0.02),  # at chest piece
        (chest_center.x, chest_center.y + avatar_scale * 0.1, body_front_z + 0.03),   # mid chest
        (chest_center.x, neck_pos.y - avatar_scale * 0.1, body_front_z + 0.02),       # below neck
    ]
    
    spline.bezier_points.add(len(tube_points) - 1)
    for i, pt in enumerate(tube_points):
        bp = spline.bezier_points[i]
        bp.co = Vector(pt)
        bp.handle_type_left = 'AUTO'
        bp.handle_type_right = 'AUTO'
    
    tube_obj = bpy.data.objects.new('Steth_MainTube', curve_data)
    bpy.context.collection.objects.link(tube_obj)
    steth_parts.append(tube_obj)
    
    # ── 4c: Left earpiece tube (neck split to left ear) ──
    left_curve = bpy.data.curves.new('StethLeftCurve', type='CURVE')
    left_curve.dimensions = '3D'
    left_curve.bevel_depth = tube_thickness * 0.8
    left_curve.bevel_resolution = 4
    
    left_spline = left_curve.splines.new('BEZIER')
    left_points = [
        (chest_center.x, neck_pos.y - avatar_scale * 0.1, body_front_z + 0.02),
        (chest_center.x - avatar_scale * 0.08, neck_pos.y, body_front_z + 0.01),
        (chest_center.x - avatar_scale * 0.06, neck_pos.y + avatar_scale * 0.25, body_front_z - 0.02),
    ]
    left_spline.bezier_points.add(len(left_points) - 1)
    for i, pt in enumerate(left_points):
        bp = left_spline.bezier_points[i]
        bp.co = Vector(pt)
        bp.handle_type_left = 'AUTO'
        bp.handle_type_right = 'AUTO'
    
    left_tube = bpy.data.objects.new('Steth_LeftTube', left_curve)
    bpy.context.collection.objects.link(left_tube)
    steth_parts.append(left_tube)
    
    # ── 4d: Right earpiece tube ──
    right_curve = bpy.data.curves.new('StethRightCurve', type='CURVE')
    right_curve.dimensions = '3D'
    right_curve.bevel_depth = tube_thickness * 0.8
    right_curve.bevel_resolution = 4
    
    right_spline = right_curve.splines.new('BEZIER')
    right_points = [
        (chest_center.x, neck_pos.y - avatar_scale * 0.1, body_front_z + 0.02),
        (chest_center.x + avatar_scale * 0.08, neck_pos.y, body_front_z + 0.01),
        (chest_center.x + avatar_scale * 0.06, neck_pos.y + avatar_scale * 0.25, body_front_z - 0.02),
    ]
    right_spline.bezier_points.add(len(right_points) - 1)
    for i, pt in enumerate(right_points):
        bp = right_spline.bezier_points[i]
        bp.co = Vector(pt)
        bp.handle_type_left = 'AUTO'
        bp.handle_type_right = 'AUTO'
    
    right_tube = bpy.data.objects.new('Steth_RightTube', right_curve)
    bpy.context.collection.objects.link(right_tube)
    steth_parts.append(right_tube)
    
    # ── 4e: Earpiece tips (small spheres) ──
    for side_name, pts in [('Left', left_points), ('Right', right_points)]:
        tip_pos = pts[-1]
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=tube_thickness * 1.5,
            segments=12,
            ring_count=8,
            location=tip_pos
        )
        tip = bpy.context.active_object
        tip.name = f"Steth_{side_name}Tip"
        steth_parts.append(tip)
    
    # ── 4f: Apply dark material to all stethoscope parts ──
    steth_mat = bpy.data.materials.new(name="StethoscopeMetal")
    steth_mat.use_nodes = True
    bsdf_s = steth_mat.node_tree.nodes.get("Principled BSDF")
    if bsdf_s:
        bsdf_s.inputs['Base Color'].default_value = (0.15, 0.15, 0.15, 1.0)  # dark grey
        bsdf_s.inputs['Roughness'].default_value = 0.3
        bsdf_s.inputs['Metallic'].default_value = 0.8
    
    # Silver material for chest piece
    silver_mat = bpy.data.materials.new(name="StethoscopeSilver")
    silver_mat.use_nodes = True
    bsdf_sv = silver_mat.node_tree.nodes.get("Principled BSDF")
    if bsdf_sv:
        bsdf_sv.inputs['Base Color'].default_value = (0.75, 0.75, 0.78, 1.0)
        bsdf_sv.inputs['Roughness'].default_value = 0.2
        bsdf_sv.inputs['Metallic'].default_value = 0.9
    
    for part in steth_parts:
        if part.type == 'MESH':
            part.data.materials.clear()
            if 'ChestPiece' in part.name:
                part.data.materials.append(silver_mat)
            else:
                part.data.materials.append(steth_mat)
        elif part.type == 'CURVE':
            part.data.materials.clear()
            part.data.materials.append(steth_mat)
    
    # ── 4g: Convert curves to mesh for GLB export ──
    print("  Converting curves to meshes...")
    for part in steth_parts:
        if part.type == 'CURVE':
            bpy.context.view_layer.objects.active = part
            part.select_set(True)
            bpy.ops.object.convert(target='MESH')
            part.select_set(False)
    
    # ── 4h: Join all stethoscope parts into one mesh ──
    print("  Joining stethoscope parts...")
    bpy.ops.object.select_all(action='DESELECT')
    for part in steth_parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = steth_parts[0]
    bpy.ops.object.join()
    stethoscope = bpy.context.active_object
    stethoscope.name = "Stethoscope"
    
    # ── 4i: Parent stethoscope to Spine2 bone ──
    print("  Parenting stethoscope to Spine2_04 bone...")
    stethoscope.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    
    # Set parent to bone
    bpy.ops.object.parent_set(type='BONE', keep_transform=True)
    
    # Find which bone it got parented to - we want Spine2_04
    stethoscope.parent = armature
    stethoscope.parent_bone = 'Spine2_04'
    stethoscope.parent_type = 'BONE'
    
    # Store the inverse matrix so it stays in place
    bone = armature.data.bones['Spine2_04']
    stethoscope.matrix_parent_inverse = (armature.matrix_world @ Matrix.Translation(bone.tail_local)).inverted()
    
    print(f"  Stethoscope: {len(stethoscope.data.vertices)} verts, parented to Spine2_04")
    
    bpy.ops.object.select_all(action='DESELECT')
else:
    print("  WARNING: Could not find bone positions, skipping stethoscope")


# ── Step 5: Verify everything ──
print("\n[Step 5] Verifying...")
mesh_count = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mesh_count += 1
        skinned = "skinned" if obj.vertex_groups else "static"
        print(f"  Mesh: {obj.name} ({len(obj.data.vertices)} verts, {skinned})")
    elif obj.type == 'ARMATURE':
        print(f"  Armature: {obj.name} ({len(obj.data.bones)} bones)")

# Verify morph targets are intact
morph_count = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.data.shape_keys:
        keys = [k.name for k in obj.data.shape_keys.key_blocks]
        morph_count += len(keys)
        print(f"  Morphs on {obj.name}: {len(keys)} targets")

print(f"  Total meshes: {mesh_count}, morph targets: {morph_count}")


# ── Step 6: Export ──
print("\n[Step 6] Exporting GLB...")
bpy.ops.export_scene.gltf(
    filepath=OUTPUT_GLB,
    export_format='GLB',
    export_apply=False,           # Don't apply modifiers (keeps morph targets)
    export_animations=True,
    export_skins=True,
    export_morph=True,
    export_morph_normal=True,
    export_tangents=False,
    export_materials='EXPORT',
    export_texture_dir='',
    export_yup=True,
)

import os
size_mb = os.path.getsize(OUTPUT_GLB) / (1024 * 1024)
print(f"\n[Export] Saved to {OUTPUT_GLB} ({size_mb:.1f} MB)")

print("\n" + "=" * 60)
print(f"  Done! Output: {OUTPUT_GLB}")
print("=" * 60)
