"""
Doctor Lab Coat & Stethoscope — Blender Script
================================================
Based on exact specifications:

1. Reference: AvatarBody (Object_7, 3276 verts, upper body mesh)
2. Duplicate torso verts → 'Lab_Coat', Shrinkwrap offset 0.02m
3. Delete center-front faces (open coat), Solidify 0.01m, SubSurf
4. Stethoscope: Bezier curve from Neck2_07 down chest, bevel 0.008m
5. Parent Lab_Coat to Armature with Automatic Weights
6. Material: white cotton (#FFFFFF, roughness 0.8)
7. Mask Modifier on AvatarBody to hide skin under coat

Avatar measurements (from probe):
  - Z is vertical: Hips=1.72, Spine=2.00, Neck=2.70, Head=2.87
  - X is left/right: ±1.58 full arms, ±0.78 forearms
  - Y is front/back: front is negative Y
  - AvatarBody Z range: 1.96 to 2.70 (upper body only)

Usage:
  /Applications/Blender.app/Contents/MacOS/Blender --background \
    --python scripts/doctor_coat_v2.py
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

INPUT_GLB  = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_lipsync.glb'
OUTPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_final.glb'

print("=" * 60)
print("  Doctor Lab Coat Builder v2")
print("=" * 60)

# ─────────────────────────────────────────────
# Step 0: Clean scene
# ─────────────────────────────────────────────
print("\n[Step 0] Cleaning scene...")
bpy.ops.wm.read_factory_settings(use_empty=True)
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ─────────────────────────────────────────────
# Step 1: Import avatar
# ─────────────────────────────────────────────
print("\n[Step 1] Importing avatar...")
bpy.ops.import_scene.gltf(filepath=INPUT_GLB)

armature = None
avatar_body = None
outfit = None

for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        armature = obj
    elif obj.type == 'MESH':
        n = (obj.name + ' ' + (obj.data.name if obj.data else '')).lower()
        if 'avatarbody' in n or obj.name == 'Object_7':
            avatar_body = obj
        if 'outfit' in n or obj.name == 'Object_17':
            outfit = obj

if not armature:
    raise RuntimeError("No armature found!")
if not avatar_body:
    raise RuntimeError("No AvatarBody mesh found!")

print(f"  Armature: {armature.name} ({len(armature.data.bones)} bones)")
print(f"  AvatarBody: {avatar_body.name} ({len(avatar_body.data.vertices)} verts)")
if outfit:
    print(f"  Outfit: {outfit.name} ({len(outfit.data.vertices)} verts)")

# Get bone world positions
def bone_pos(name):
    b = armature.data.bones.get(name)
    return armature.matrix_world @ b.head_local if b else None

hips_z   = bone_pos('Hips_01').z       # 1.72
neck_z   = bone_pos('Neck_05').z       # 2.70
forearm_x = abs(bone_pos('LeftForeArm_014').x)  # 0.78

print(f"  Hips Z: {hips_z:.3f}, Neck Z: {neck_z:.3f}, Forearm |X|: {forearm_x:.3f}")


# ─────────────────────────────────────────────
# Step 2: Duplicate torso FACES → Lab_Coat
# ─────────────────────────────────────────────
print("\n[Step 2] Selecting torso faces from AvatarBody...")

bpy.ops.object.select_all(action='DESELECT')
avatar_body.select_set(True)
bpy.context.view_layer.objects.active = avatar_body

# The coat should have sleeves that end near the wrists
sleeve_end_x = forearm_x + 0.15

# Go to edit mode, FACE select mode
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type='FACE')
bpy.ops.mesh.select_all(action='DESELECT')

bm = bmesh.from_edit_mesh(avatar_body.data)
bm.faces.ensure_lookup_table()

# Select faces where the face center is in the torso region
selected_faces = 0
for face in bm.faces:
    center = avatar_body.matrix_world @ face.calc_center_median()
    # Torso + arms: below neck, within sleeve range
    if abs(center.x) <= sleeve_end_x and center.z <= neck_z + 0.02:
        face.select = True
        selected_faces += 1

bmesh.update_edit_mesh(avatar_body.data)
print(f"  Selected {selected_faces}/{len(bm.faces)} torso+arm faces")

# Duplicate selected faces and separate into new object
bpy.ops.mesh.duplicate()
bpy.ops.mesh.separate(type='SELECTED')

bpy.ops.object.mode_set(mode='OBJECT')

# Find the newly created object
lab_coat = None
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj != avatar_body and obj != outfit:
        name = obj.name.lower()
        if ('object_7' in name or obj.name.startswith('Object_7')) and obj.name != avatar_body.name:
            lab_coat = obj
            break

if not lab_coat:
    # Fallback: find the new mesh with faces
    for obj in sorted(bpy.data.objects, key=lambda o: o.name, reverse=True):
        if obj.type == 'MESH' and obj != avatar_body and obj != outfit:
            if len(obj.data.polygons) > 10:
                lab_coat = obj
                break

if not lab_coat:
    raise RuntimeError("Failed to separate Lab_Coat mesh!")

lab_coat.name = "Lab_Coat"
lab_coat.data.name = "Lab_Coat_mesh"
print(f"  Lab_Coat created: {len(lab_coat.data.vertices)} verts, {len(lab_coat.data.polygons)} faces")


# ─────────────────────────────────────────────
# Step 3a: Shrinkwrap (offset 0.02m from AvatarBody)
# ─────────────────────────────────────────────
print("\n[Step 3a] Shrinkwrap Lab_Coat to AvatarBody (offset 0.02m)...")

bpy.ops.object.select_all(action='DESELECT')
lab_coat.select_set(True)
bpy.context.view_layer.objects.active = lab_coat

shrink = lab_coat.modifiers.new(name="ShrinkToBody", type='SHRINKWRAP')
shrink.target = avatar_body
shrink.wrap_method = 'NEAREST_SURFACEPOINT'
shrink.wrap_mode = 'OUTSIDE_SURFACE'
shrink.offset = 0.02  # 2cm offset — pushes coat away from body

bpy.ops.object.modifier_apply(modifier=shrink.name)
print(f"  Shrinkwrapped with 0.02m offset")


# ─────────────────────────────────────────────
# Step 3b: Delete center-front faces (open coat)
# ─────────────────────────────────────────────
print("\n[Step 3b] Deleting center-front faces for open coat...")

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')

bm = bmesh.from_edit_mesh(lab_coat.data)
bm.faces.ensure_lookup_table()
bm.verts.ensure_lookup_table()

# Find center-front faces:
# Front = negative Y (based on probe data)
# Center = X near 0
# Only in the torso area (not collar/neck)
deleted_count = 0
collar_z = neck_z - 0.08  # leave collar intact

for face in bm.faces:
    # Get face center in world space
    center = lab_coat.matrix_world @ face.calc_center_median()
    
    # Center-front strip: |X| < 0.04m, Y < -0.05 (front), Z below collar
    if (abs(center.x) < 0.04 and 
        center.y < -0.05 and 
        center.z < collar_z and
        center.z > hips_z + 0.1):  # not too low
        face.select = True
        deleted_count += 1

bmesh.update_edit_mesh(lab_coat.data)

if deleted_count > 0:
    bpy.ops.mesh.delete(type='FACE')
    print(f"  Deleted {deleted_count} center-front faces (open coat)")
else:
    print(f"  No center-front faces found (coat may already be open)")

bpy.ops.object.mode_set(mode='OBJECT')


# ─────────────────────────────────────────────
# Step 3c: Solidify modifier (0.01m thickness)
# ─────────────────────────────────────────────
print("\n[Step 3c] Adding Solidify modifier (0.01m)...")

bpy.ops.object.select_all(action='DESELECT')
lab_coat.select_set(True)
bpy.context.view_layer.objects.active = lab_coat

solidify = lab_coat.modifiers.new(name="CoatThickness", type='SOLIDIFY')
solidify.thickness = 0.01   # 1cm thickness
solidify.offset = 1.0       # push outward only
solidify.use_even_offset = True
solidify.use_quality_normals = True

bpy.ops.object.modifier_apply(modifier=solidify.name)
print(f"  Solidified: {len(lab_coat.data.vertices)} verts")


# ─────────────────────────────────────────────
# Step 3d: Subdivision Surface for smoothness
# ─────────────────────────────────────────────
print("\n[Step 3d] Adding Subdivision Surface...")

subsurf = lab_coat.modifiers.new(name="SubSurf", type='SUBSURF')
subsurf.levels = 1          # viewport
subsurf.render_levels = 1   # render — keep low for mobile perf

bpy.ops.object.modifier_apply(modifier=subsurf.name)
print(f"  Subdivided: {len(lab_coat.data.vertices)} verts")


# ─────────────────────────────────────────────
# Step 3e: Recalculate normals
# ─────────────────────────────────────────────
print("\n[Step 3e] Recalculating normals...")

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
print("  Normals fixed (outside)")


# ─────────────────────────────────────────────
# Step 4: Stethoscope — Bezier Curve from Neck
# ─────────────────────────────────────────────
print("\n[Step 4] Creating stethoscope...")

neck2 = bone_pos('Neck2_07')  # back of neck
spine2 = bone_pos('Spine2_04')  # upper chest

if neck2 and spine2:
    # Stethoscope hangs from back of neck, over shoulders, down the chest
    front_y = -0.12  # front of body

    # ── 4a: Main tube — Bezier curve ──
    curve_data = bpy.data.curves.new('StethCurve', 'CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.008  # 8mm tube diameter (per spec)
    curve_data.bevel_resolution = 6

    spline = curve_data.splines.new('BEZIER')

    # Path: back of neck → over left shoulder → down front of chest
    path_points = [
        Vector((0.0, neck2.y + 0.02, neck2.z)),                    # back of neck
        Vector((-0.12, neck2.y, neck2.z - 0.02)),                  # left side of neck
        Vector((-0.10, front_y, spine2.z + 0.10)),                 # left front shoulder area
        Vector((-0.06, front_y - 0.02, spine2.z - 0.05)),          # down left chest
        Vector((0.0, front_y - 0.03, spine2.z - 0.15)),            # center chest (chest piece)
    ]

    spline.bezier_points.add(len(path_points) - 1)
    for i, pt in enumerate(path_points):
        bp = spline.bezier_points[i]
        bp.co = pt
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    # Also add the right side tube (from neck over right shoulder)
    spline2 = curve_data.splines.new('BEZIER')
    path_points2 = [
        Vector((0.0, neck2.y + 0.02, neck2.z)),                   # back of neck
        Vector((0.12, neck2.y, neck2.z - 0.02)),                   # right side of neck
        Vector((0.10, front_y, spine2.z + 0.10)),                  # right front shoulder
        Vector((0.06, front_y - 0.02, spine2.z - 0.05)),           # down right chest
        Vector((0.0, front_y - 0.03, spine2.z - 0.15)),            # center chest
    ]
    spline2.bezier_points.add(len(path_points2) - 1)
    for i, pt in enumerate(path_points2):
        bp = spline2.bezier_points[i]
        bp.co = pt
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    steth_curve_obj = bpy.data.objects.new('Stethoscope_Tube', curve_data)
    bpy.context.collection.objects.link(steth_curve_obj)

    # ── 4b: Chest piece (flat cylinder at bottom of tube) ──
    chest_piece_pos = path_points[-1]
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.025,  # 2.5cm radius
        depth=0.008,   # thin disc
        location=chest_piece_pos,
        rotation=(math.pi / 2, 0, 0),  # flat against chest
        vertices=24
    )
    chest_piece = bpy.context.active_object
    chest_piece.name = "Steth_ChestPiece"

    # ── 4c: Stethoscope material — dark grey ──
    steth_mat = bpy.data.materials.new("StethDarkGrey")
    steth_mat.use_nodes = True
    bsdf_s = steth_mat.node_tree.nodes.get("Principled BSDF")
    if bsdf_s:
        bsdf_s.inputs['Base Color'].default_value = (0.15, 0.15, 0.15, 1.0)
        bsdf_s.inputs['Roughness'].default_value = 0.35  # rubbery
        bsdf_s.inputs['Metallic'].default_value = 0.0

    steth_metal_mat = bpy.data.materials.new("StethSilver")
    steth_metal_mat.use_nodes = True
    bsdf_m = steth_metal_mat.node_tree.nodes.get("Principled BSDF")
    if bsdf_m:
        bsdf_m.inputs['Base Color'].default_value = (0.7, 0.7, 0.73, 1.0)
        bsdf_m.inputs['Roughness'].default_value = 0.15
        bsdf_m.inputs['Metallic'].default_value = 1.0

    # Apply materials
    steth_curve_obj.data.materials.append(steth_mat)
    chest_piece.data.materials.clear()
    chest_piece.data.materials.append(steth_metal_mat)

    # ── 4d: Convert curve to mesh for GLB export ──
    bpy.ops.object.select_all(action='DESELECT')
    steth_curve_obj.select_set(True)
    bpy.context.view_layer.objects.active = steth_curve_obj
    bpy.ops.object.convert(target='MESH')

    # ── 4e: Join tube + chest piece ──
    bpy.ops.object.select_all(action='DESELECT')
    steth_curve_obj.select_set(True)
    chest_piece.select_set(True)
    bpy.context.view_layer.objects.active = steth_curve_obj
    bpy.ops.object.join()
    stethoscope = bpy.context.active_object
    stethoscope.name = "Stethoscope"

    # ── 4f: Parent stethoscope to Neck2_07 bone ──
    print("  Parenting stethoscope to Neck2_07 bone...")
    bpy.ops.object.select_all(action='DESELECT')
    stethoscope.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature

    stethoscope.parent = armature
    stethoscope.parent_bone = 'Neck2_07'
    stethoscope.parent_type = 'BONE'

    bone = armature.data.bones['Neck2_07']
    stethoscope.matrix_parent_inverse = (
        armature.matrix_world @ Matrix.Translation(bone.tail_local)
    ).inverted()

    print(f"  Stethoscope: {len(stethoscope.data.vertices)} verts, parented to Neck2_07")
    bpy.ops.object.select_all(action='DESELECT')
else:
    print("  WARNING: Missing neck/spine bones — skipping stethoscope")


# ─────────────────────────────────────────────
# Step 5: Parent Lab_Coat to Armature (Automatic Weights)
# ─────────────────────────────────────────────
print("\n[Step 5] Parenting Lab_Coat to Armature with Automatic Weights...")

bpy.ops.object.select_all(action='DESELECT')
lab_coat.select_set(True)
armature.select_set(True)
bpy.context.view_layer.objects.active = armature

bpy.ops.object.parent_set(type='ARMATURE_AUTO')

print(f"  Lab_Coat parented to {armature.name} with automatic weights")
print(f"  Vertex groups on coat: {len(lab_coat.vertex_groups)}")


# ─────────────────────────────────────────────
# Step 6: White cotton material
# ─────────────────────────────────────────────
print("\n[Step 6] Applying white cotton material to Lab_Coat...")

coat_mat = bpy.data.materials.new(name="WhiteCotton")
coat_mat.use_nodes = True
bsdf = coat_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)  # #FFFFFF per spec
    bsdf.inputs['Roughness'].default_value = 0.8                      # cotton look
    bsdf.inputs['Metallic'].default_value = 0.0

lab_coat.data.materials.clear()
lab_coat.data.materials.append(coat_mat)
print("  White cotton material applied (#FFFFFF, roughness 0.8)")


# ─────────────────────────────────────────────
# Step 7: Mask Modifier on AvatarBody
# ─────────────────────────────────────────────
print("\n[Step 7] Adding Mask Modifier to AvatarBody...")

# Create vertex group for torso skin to hide under coat
# Only hide the core torso — not face, hands, or legs
bpy.ops.object.select_all(action='DESELECT')
avatar_body.select_set(True)
bpy.context.view_layer.objects.active = avatar_body

mask_vg = avatar_body.vertex_groups.new(name="UnderCoat")

hidden = 0
for v in avatar_body.data.vertices:
    vw = avatar_body.matrix_world @ v.co
    # Only hide torso core: within sleeve range, below collar, above hips
    if (abs(vw.x) < sleeve_end_x - 0.05 and  # smaller than coat to avoid edge gaps
        vw.z < neck_z - 0.05 and              # below collar
        vw.z > hips_z + 0.15):                # above hip area
        mask_vg.add([v.index], 1.0, 'REPLACE')
        hidden += 1

mask_mod = avatar_body.modifiers.new(name="HideUnderCoat", type='MASK')
mask_mod.vertex_group = "UnderCoat"
mask_mod.invert_vertex_group = True  # SHOW everything except UnderCoat group

print(f"  Will hide {hidden}/{len(avatar_body.data.vertices)} body verts under coat")

# Apply the mask
bpy.ops.object.modifier_apply(modifier=mask_mod.name)
print(f"  AvatarBody after mask: {len(avatar_body.data.vertices)} verts remaining")

# Also mask the outfit (saree) torso to reduce clipping
if outfit:
    bpy.ops.object.select_all(action='DESELECT')
    outfit.select_set(True)
    bpy.context.view_layer.objects.active = outfit

    outfit_mask_vg = outfit.vertex_groups.new(name="UnderCoat")
    outfit_hidden = 0
    for v in outfit.data.vertices:
        vw = outfit.matrix_world @ v.co
        # More conservative: only hide outfit torso that's clearly under the coat
        if (abs(vw.x) < sleeve_end_x - 0.10 and
            vw.z < neck_z - 0.10 and
            vw.z > hips_z + 0.20):
            outfit_mask_vg.add([v.index], 1.0, 'REPLACE')
            outfit_hidden += 1

    outfit_mask = outfit.modifiers.new(name="HideUnderCoat", type='MASK')
    outfit_mask.vertex_group = "UnderCoat"
    outfit_mask.invert_vertex_group = True

    print(f"  Will hide {outfit_hidden}/{len(outfit.data.vertices)} outfit verts under coat")
    bpy.ops.object.modifier_apply(modifier=outfit_mask.name)
    print(f"  Outfit after mask: {len(outfit.data.vertices)} verts remaining")


# ─────────────────────────────────────────────
# Step 8: Verify
# ─────────────────────────────────────────────
print("\n[Step 8] Verification...")

total_morphs = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        vg = f"{len(obj.vertex_groups)} groups" if obj.vertex_groups else "static"
        morph = ""
        if obj.data.shape_keys:
            n = len(obj.data.shape_keys.key_blocks)
            total_morphs += n
            morph = f", {n} morphs"
        print(f"  {obj.name}: {len(obj.data.vertices)} verts ({vg}{morph})")
    elif obj.type == 'ARMATURE':
        print(f"  {obj.name}: {len(obj.data.bones)} bones")

print(f"\n  Total morph targets: {total_morphs}")


# ─────────────────────────────────────────────
# Step 9: Export GLB
# ─────────────────────────────────────────────
print("\n[Step 9] Exporting GLB...")

bpy.ops.export_scene.gltf(
    filepath=OUTPUT_GLB,
    export_format='GLB',
    export_apply=False,
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
print(f"\n  Saved: {OUTPUT_GLB} ({size_mb:.1f} MB)")

print("\n" + "=" * 60)
print("  Done!")
print("=" * 60)
