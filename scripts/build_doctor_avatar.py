"""
Doctor Avatar Builder — Blender Script
=======================================
Following proper 3D character workflow (Gemini recommendations):

1. Import existing avatar (has bones, lip sync morphs, vertex groups)
2. Duplicate outfit mesh → coat base (inherits all weights instantly)
3. Solidify modifier outward → coat thickness
4. Shrinkwrap to body → prevent clipping
5. White Principled BSDF material (off-white, high roughness = cotton)
6. Stethoscope from Bezier curves + simple meshes
7. Parent stethoscope to Spine2 bone
8. Mask modifier on body → hide skin under coat
9. Export GLB with all morphs/bones intact

Usage:
  /Applications/Blender.app/Contents/MacOS/Blender --background \
    --python scripts/build_doctor_avatar.py
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

INPUT_GLB  = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_lipsync.glb'
OUTPUT_GLB = '/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor_final.glb'

print("=" * 60)
print("  Doctor Avatar Builder")
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
outfit_mesh = None
body_mesh = None
all_meshes = []

for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        armature = obj
    elif obj.type == 'MESH':
        all_meshes.append(obj)
        name = (obj.name + ' ' + (obj.data.name if obj.data else '')).lower()
        if 'outfit' in name or obj.name == 'Object_17':
            outfit_mesh = obj
        if 'avatarbody' in name or obj.name == 'Object_7':
            body_mesh = obj

if not armature:
    raise RuntimeError("No armature found!")
if not outfit_mesh:
    raise RuntimeError("No outfit mesh found!")

print(f"  Armature: {armature.name} ({len(armature.data.bones)} bones)")
print(f"  Outfit: {outfit_mesh.name} ({len(outfit_mesh.data.vertices)} verts, {len(outfit_mesh.data.polygons)} faces)")
if body_mesh:
    print(f"  Body: {body_mesh.name} ({len(body_mesh.data.vertices)} verts)")

# Check morph targets
morph_meshes = []
for obj in all_meshes:
    if obj.data.shape_keys:
        keys = [k.name for k in obj.data.shape_keys.key_blocks]
        morph_meshes.append((obj.name, len(keys)))
        print(f"  Morphs on {obj.name}: {len(keys)} ({', '.join(keys[:5])}...)")

# ─────────────────────────────────────────────
# Step 2: Duplicate outfit → lab coat base
# ─────────────────────────────────────────────
print("\n[Step 2] Duplicating outfit mesh as coat base...")

# Deselect all, select outfit, duplicate
bpy.ops.object.select_all(action='DESELECT')
outfit_mesh.select_set(True)
bpy.context.view_layer.objects.active = outfit_mesh
bpy.ops.object.duplicate(linked=False)

coat = bpy.context.active_object
coat.name = "LabCoat"
coat.data.name = "LabCoat_mesh"

print(f"  Created: {coat.name} ({len(coat.data.vertices)} verts)")
print(f"  Vertex groups: {len(coat.vertex_groups)} (inherited from outfit)")

# ─────────────────────────────────────────────
# Step 3: Solidify modifier → coat thickness
# ─────────────────────────────────────────────
print("\n[Step 3] Adding Solidify modifier for coat thickness...")

bpy.context.view_layer.objects.active = coat
coat.select_set(True)

# Recalculate normals outside before solidifying
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
print("  Normals recalculated (outside)")

solidify = coat.modifiers.new(name="CoatThickness", type='SOLIDIFY')
solidify.thickness = 0.005        # 5mm outward — visible coat layer
solidify.offset = 1.0             # push outward only
solidify.use_even_offset = True   # even thickness
solidify.use_quality_normals = True

# Apply the modifier so the mesh is baked
bpy.ops.object.modifier_apply(modifier=solidify.name)
print(f"  Solidified: {len(coat.data.vertices)} verts after apply")

# Skip Shrinkwrap — it was collapsing front faces into the body

# ─────────────────────────────────────────────
# Step 4: White lab coat material (Principled BSDF)
# ─────────────────────────────────────────────
print("\n[Step 5] Applying white lab coat material...")

coat_mat = bpy.data.materials.new(name="WhiteLabCoat")
coat_mat.use_nodes = True
bsdf = coat_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    # Off-white — pure white looks fake (Gemini tip)
    bsdf.inputs['Base Color'].default_value = (0.92, 0.92, 0.90, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.8     # cotton/polyester look
    bsdf.inputs['Metallic'].default_value = 0.0
    if 'Subsurface Weight' in bsdf.inputs:
        bsdf.inputs['Subsurface Weight'].default_value = 0.01

coat.data.materials.clear()
coat.data.materials.append(coat_mat)
print("  Off-white cotton material applied (roughness=0.8)")

# ─────────────────────────────────────────────
# Step 6: Build stethoscope from Bezier curves
# ─────────────────────────────────────────────
print("\n[Step 6] Building stethoscope...")

# Get bone world positions for placement
def bone_head(name):
    b = armature.data.bones.get(name)
    return armature.matrix_world @ b.head_local if b else None

def bone_tail(name):
    b = armature.data.bones.get(name)
    return armature.matrix_world @ b.tail_local if b else None

neck = bone_head('Neck_05')
spine2 = bone_head('Spine2_04')
head = bone_head('Head_08')

if neck and spine2:
    chest_mid = (neck + spine2) / 2
    scale = abs(neck.y - spine2.y)  # neck-to-chest distance for proportional sizing
    front_z = chest_mid.z + 0.08    # in front of body
    tube_r = scale * 0.025          # tube radius

    steth_parts = []

    # ── 6a: Chest piece (flattened cylinder with inset) ──
    cp_pos = (chest_mid.x, chest_mid.y - scale * 0.2, front_z + 0.015)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=scale * 0.10,
        depth=scale * 0.025,
        location=cp_pos,
        rotation=(math.pi / 2, 0, 0),
        vertices=24
    )
    chest_piece = bpy.context.active_object
    chest_piece.name = "Steth_ChestPiece"
    steth_parts.append(chest_piece)

    # ── 6b: Main tube — Bezier curve from chest piece up to neck ──
    main_curve = bpy.data.curves.new('StethMainCurve', 'CURVE')
    main_curve.dimensions = '3D'
    main_curve.bevel_depth = tube_r
    main_curve.bevel_resolution = 4

    sp = main_curve.splines.new('BEZIER')
    pts = [
        Vector(cp_pos),                                                          # at chest piece
        Vector((chest_mid.x, chest_mid.y, front_z + 0.02)),                     # mid chest
        Vector((chest_mid.x, neck.y - scale * 0.15, front_z + 0.015)),          # below neck
    ]
    sp.bezier_points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        bp = sp.bezier_points[i]
        bp.co = p
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    main_tube = bpy.data.objects.new('Steth_MainTube', main_curve)
    bpy.context.collection.objects.link(main_tube)
    steth_parts.append(main_tube)

    # ── 6c: Left ear tube — curves from neck split to left side ──
    for side, sign in [('Left', -1), ('Right', 1)]:
        ear_curve = bpy.data.curves.new(f'Steth{side}Curve', 'CURVE')
        ear_curve.dimensions = '3D'
        ear_curve.bevel_depth = tube_r * 0.75
        ear_curve.bevel_resolution = 4

        esp = ear_curve.splines.new('BEZIER')
        ear_pts = [
            Vector((chest_mid.x, neck.y - scale * 0.15, front_z + 0.015)),      # from main tube end
            Vector((chest_mid.x + sign * scale * 0.07, neck.y, front_z)),        # around neck
            Vector((chest_mid.x + sign * scale * 0.05, neck.y + scale * 0.28, front_z - 0.03)),  # to ear
        ]
        esp.bezier_points.add(len(ear_pts) - 1)
        for i, p in enumerate(ear_pts):
            bp = esp.bezier_points[i]
            bp.co = p
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'

        ear_tube = bpy.data.objects.new(f'Steth_{side}Tube', ear_curve)
        bpy.context.collection.objects.link(ear_tube)
        steth_parts.append(ear_tube)

        # Ear tips (small UV spheres)
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=tube_r * 1.3,
            segments=12, ring_count=8,
            location=ear_pts[-1]
        )
        tip = bpy.context.active_object
        tip.name = f"Steth_{side}Tip"
        steth_parts.append(tip)

    # ── 6d: Materials ──
    # Rubber tube: dark grey, low roughness (rubbery sheen)
    rubber_mat = bpy.data.materials.new("StethRubber")
    rubber_mat.use_nodes = True
    rb = rubber_mat.node_tree.nodes.get("Principled BSDF")
    if rb:
        rb.inputs['Base Color'].default_value = (0.12, 0.12, 0.12, 1.0)
        rb.inputs['Roughness'].default_value = 0.3
        rb.inputs['Metallic'].default_value = 0.0

    # Metal parts: full metallic
    metal_mat = bpy.data.materials.new("StethMetal")
    metal_mat.use_nodes = True
    mt = metal_mat.node_tree.nodes.get("Principled BSDF")
    if mt:
        mt.inputs['Base Color'].default_value = (0.72, 0.72, 0.75, 1.0)
        mt.inputs['Roughness'].default_value = 0.15
        mt.inputs['Metallic'].default_value = 1.0

    for part in steth_parts:
        if part.type == 'MESH':
            part.data.materials.clear()
            if 'ChestPiece' in part.name:
                part.data.materials.append(metal_mat)
            else:
                part.data.materials.append(rubber_mat)
        elif part.type == 'CURVE':
            part.data.materials.clear()
            part.data.materials.append(rubber_mat)

    # ── 6e: Convert curves → mesh for GLB export ──
    print("  Converting curves to meshes...")
    for part in steth_parts:
        if part.type == 'CURVE':
            bpy.ops.object.select_all(action='DESELECT')
            part.select_set(True)
            bpy.context.view_layer.objects.active = part
            bpy.ops.object.convert(target='MESH')

    # ── 6f: Join all stethoscope parts ──
    print("  Joining stethoscope parts...")
    bpy.ops.object.select_all(action='DESELECT')
    for part in steth_parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = steth_parts[0]
    bpy.ops.object.join()
    stethoscope = bpy.context.active_object
    stethoscope.name = "Stethoscope"

    # ── 6g: Parent stethoscope to Spine2_04 bone ──
    print("  Parenting stethoscope to Spine2_04 bone...")
    bpy.ops.object.select_all(action='DESELECT')
    stethoscope.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature

    stethoscope.parent = armature
    stethoscope.parent_bone = 'Spine2_04'
    stethoscope.parent_type = 'BONE'

    # Set inverse so stethoscope stays in its current world position
    bone = armature.data.bones['Spine2_04']
    stethoscope.matrix_parent_inverse = (
        armature.matrix_world @ Matrix.Translation(bone.tail_local)
    ).inverted()

    print(f"  Stethoscope: {len(stethoscope.data.vertices)} verts, parented to Spine2_04")
    bpy.ops.object.select_all(action='DESELECT')
else:
    print("  WARNING: Could not find neck/spine bones — skipping stethoscope")

# ─────────────────────────────────────────────
# Step 7: Mask body under coat
# ─────────────────────────────────────────────
print("\n[Step 7] Masking body under coat...")

if body_mesh:
    # Create a vertex group for the mask — vertices that are covered by the coat
    bpy.context.view_layer.objects.active = body_mesh
    body_mesh.select_set(True)

    # Get coat bounding box in world space
    coat_verts_world = [coat.matrix_world @ v.co for v in coat.data.vertices]
    if coat_verts_world:
        coat_min_y = min(v.y for v in coat_verts_world)
        coat_max_y = max(v.y for v in coat_verts_world)
        coat_min_x = min(v.x for v in coat_verts_world)
        coat_max_x = max(v.x for v in coat_verts_world)

        # Generous margins to avoid hiding face, hands, legs
        margin_top = (coat_max_y - coat_min_y) * 0.30   # don't hide top 30% (neck/face area)
        margin_bottom = (coat_max_y - coat_min_y) * 0.10  # don't hide bottom 10%
        margin_sides = 0.02                                # 2cm side margin

        hide_min_y = coat_min_y + margin_bottom
        hide_max_y = coat_max_y - margin_top
        hide_min_x = coat_min_x + margin_sides
        hide_max_x = coat_max_x - margin_sides

        # Create vertex group "CoatMask"
        mask_vg = body_mesh.vertex_groups.new(name="CoatMask")

        hidden_count = 0
        for v in body_mesh.data.vertices:
            vw = body_mesh.matrix_world @ v.co
            if (hide_min_y <= vw.y <= hide_max_y and
                hide_min_x <= vw.x <= hide_max_x):
                mask_vg.add([v.index], 1.0, 'REPLACE')
                hidden_count += 1

        # Add Mask modifier — hide vertices in the "CoatMask" group
        mask_mod = body_mesh.modifiers.new(name="HideUnderCoat", type='MASK')
        mask_mod.vertex_group = "CoatMask"
        mask_mod.invert_vertex_group = True  # show everything EXCEPT CoatMask group

        print(f"  Masked {hidden_count}/{len(body_mesh.data.vertices)} body verts under coat")

        # Apply the mask so it's baked into the mesh
        bpy.ops.object.modifier_apply(modifier=mask_mod.name)
        print(f"  Body verts after mask: {len(body_mesh.data.vertices)}")
    else:
        print("  WARNING: No coat vertices found")

    body_mesh.select_set(False)
else:
    print("  WARNING: No body mesh, skipping mask")

# ─────────────────────────────────────────────
# Step 8: Data Transfer — coat weights from body
# ─────────────────────────────────────────────
print("\n[Step 8] Data Transfer: ensuring coat has proper bone weights...")

# The coat was duplicated from outfit, so it already has vertex groups.
# But after Solidify added new verts, we should re-transfer from body to fill gaps.
if body_mesh and coat:
    bpy.ops.object.select_all(action='DESELECT')
    coat.select_set(True)
    bpy.context.view_layer.objects.active = coat

    dt = coat.modifiers.new(name="WeightTransfer", type='DATA_TRANSFER')
    dt.object = outfit_mesh  # transfer from original outfit (better match than body)
    dt.use_vert_data = True
    dt.data_types_verts = {'VGROUP_WEIGHTS'}
    dt.vert_mapping = 'POLYINTERP_NEAREST'

    bpy.ops.object.modifier_apply(modifier=dt.name)
    print(f"  Transferred weights from {outfit_mesh.name} → {coat.name}")
    print(f"  Coat vertex groups: {len(coat.vertex_groups)}")

# ─────────────────────────────────────────────
# Step 9: Verify everything
# ─────────────────────────────────────────────
print("\n[Step 9] Verification...")

mesh_count = 0
total_morphs = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mesh_count += 1
        skinned = f"{len(obj.vertex_groups)} groups" if obj.vertex_groups else "static"
        morph = ""
        if obj.data.shape_keys:
            n = len(obj.data.shape_keys.key_blocks)
            total_morphs += n
            morph = f", {n} morphs"
        print(f"  {obj.name}: {len(obj.data.vertices)} verts ({skinned}{morph})")
    elif obj.type == 'ARMATURE':
        print(f"  {obj.name}: {len(obj.data.bones)} bones")

print(f"\n  Total: {mesh_count} meshes, {total_morphs} morph targets")

# ─────────────────────────────────────────────
# Step 10: Export GLB
# ─────────────────────────────────────────────
print("\n[Step 10] Exporting GLB...")

bpy.ops.export_scene.gltf(
    filepath=OUTPUT_GLB,
    export_format='GLB',
    export_apply=False,       # keep morph targets
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
print(f"  Done! Doctor avatar ready: {OUTPUT_GLB}")
print("=" * 60)
