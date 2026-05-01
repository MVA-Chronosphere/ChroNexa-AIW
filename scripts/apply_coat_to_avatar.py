"""
Blender script: Extract white coat + stethoscope from physician model,
transfer bone weights from avatar body, and export combined GLB.

Usage:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/apply_coat_to_avatar.py

Steps:
  1. Import avatar GLB (has armature + skinned meshes)
  2. Import physician GLB (static mesh with coat texture)
  3. Sample physician texture → select only coat/stethoscope faces
  4. Separate coat into new object
  5. Scale & align coat to avatar proportions
  6. Data Transfer modifier: copy vertex weights from avatar body → coat
  7. Parent coat to avatar armature with Armature modifier
  8. Mask modifier on avatar body to hide skin under coat
  9. Export combined GLB
"""

import bpy
import bmesh
import os
import sys
import numpy as np
from mathutils import Vector, Matrix

# ─── Config ───
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AVATAR_GLB = os.path.join(PROJECT_ROOT, "frontend", "public", "indian_doctor_lipsync.glb")
PHYSICIAN_GLB = os.path.join(PROJECT_ROOT, "frontend", "public", "avatars",
                              "white-coat-physician-with-stethoscope", "source", "model.glb")
OUTPUT_GLB = os.path.join(PROJECT_ROOT, "frontend", "public", "indian_doctor_coat.glb")

# Texture color thresholds for coat detection
COAT_LUM_MIN = 160       # white coat pixels: luminance > 160
COAT_SAT_MAX = 0.20      # low saturation (white/grey)
STETH_LUM_MAX = 50        # stethoscope: very dark
STETH_SAT_MAX = 0.20
DETAIL_LUM_MIN = 120       # grey coat details (shadows, pockets)
DETAIL_LUM_MAX = 160
DETAIL_SAT_MAX = 0.15
# Skin detection (to exclude)
SKIN_R_MINUS_B_MIN = 20   # warm tone threshold


def clean_scene():
    """Remove all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Clear orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.armatures:
        if block.users == 0:
            bpy.data.armatures.remove(block)


def import_glb(filepath, name_prefix=""):
    """Import a GLB file and return the imported objects."""
    before = set(bpy.data.objects.keys())
    bpy.ops.import_scene.gltf(filepath=filepath)
    after = set(bpy.data.objects.keys())
    new_names = after - before
    new_objects = [bpy.data.objects[n] for n in new_names]
    print(f"[Import] {filepath}: {len(new_objects)} objects: {[o.name for o in new_objects]}")
    return new_objects


def get_pixel_color(image, u, v):
    """Sample a Blender image at UV coordinates. Returns (R, G, B) in 0-255."""
    w, h = image.size
    px = min(int(u * w), w - 1)
    py = min(int(v * h), h - 1)
    # Blender stores pixels as flat array: [R,G,B,A, R,G,B,A, ...]
    idx = (py * w + px) * 4
    pixels = image.pixels
    r = int(pixels[idx] * 255)
    g = int(pixels[idx + 1] * 255)
    b = int(pixels[idx + 2] * 255)
    return r, g, b


def is_coat_pixel(r, g, b):
    """Determine if a pixel color belongs to coat, stethoscope, or coat detail."""
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    sat = (max_c - min_c) / max_c if max_c > 0 else 0

    # Skin detection: warm tones
    is_skin = (r > g and g > b and (r - b) > SKIN_R_MINUS_B_MIN and
               sat > 0.12 and lum > 80 and lum < 220)
    if is_skin:
        return False

    # White coat
    if lum > COAT_LUM_MIN and sat < COAT_SAT_MAX:
        return True
    # Stethoscope (dark metal)
    if lum < STETH_LUM_MAX and sat < STETH_SAT_MAX:
        return True
    # Grey coat details
    if DETAIL_LUM_MIN < lum <= DETAIL_LUM_MAX and sat < DETAIL_SAT_MAX:
        return True

    return False


def select_coat_faces(obj):
    """Select faces on the physician mesh that correspond to coat/stethoscope
    based on their UV-mapped texture color."""

    # Find the base color texture image
    mat = obj.data.materials[0] if obj.data.materials else None
    if not mat or not mat.use_nodes:
        print("[CoatSelect] No material/nodes found")
        return 0

    # Find the Image Texture node
    tex_image = None
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            tex_image = node.image
            break

    if not tex_image:
        print("[CoatSelect] No texture image found in material")
        return 0

    print(f"[CoatSelect] Texture: {tex_image.name} ({tex_image.size[0]}x{tex_image.size[1]})")

    # Cache all pixels for fast access
    w, h = tex_image.size
    all_pixels = list(tex_image.pixels)  # flat RGBA array
    print(f"[CoatSelect] Cached {len(all_pixels)//4} pixels")

    def sample_fast(u, v):
        px = min(int(u * w), w - 1)
        py = min(int(v * h), h - 1)
        idx = (py * w + px) * 4
        return (int(all_pixels[idx] * 255),
                int(all_pixels[idx + 1] * 255),
                int(all_pixels[idx + 2] * 255))

    # Get UV layer
    uv_layer_name = obj.data.uv_layers.active.name if obj.data.uv_layers.active else None
    if not uv_layer_name:
        print("[CoatSelect] No UV layer")
        return 0

    # Enter edit mode and select coat faces
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.active

    if not uv_layer:
        bpy.ops.object.mode_set(mode='OBJECT')
        print("[CoatSelect] No UV layer in bmesh")
        return 0

    # Deselect all first
    for face in bm.faces:
        face.select = False

    coat_faces = 0
    total_faces = len(bm.faces)

    for face in bm.faces:
        # Sample at face centroid UV
        u_sum, v_sum = 0.0, 0.0
        for loop in face.loops:
            uv = loop[uv_layer].uv
            u_sum += uv.x
            v_sum += uv.y
        n = len(face.loops)
        u_avg = u_sum / n
        v_avg = v_sum / n

        r, g, b = sample_fast(u_avg, v_avg)

        if is_coat_pixel(r, g, b):
            face.select = True
            coat_faces += 1

    bmesh.update_edit_mesh(obj.data)
    print(f"[CoatSelect] Selected {coat_faces}/{total_faces} coat faces "
          f"({coat_faces/total_faces*100:.1f}%)")

    bpy.ops.object.mode_set(mode='OBJECT')
    return coat_faces


def separate_coat(physician_obj):
    """Separate selected (coat) faces into a new object."""
    bpy.context.view_layer.objects.active = physician_obj
    bpy.ops.object.mode_set(mode='EDIT')

    # Separate selected faces
    bpy.ops.mesh.separate(type='SELECTED')

    bpy.ops.object.mode_set(mode='OBJECT')

    # The new object is the last selected one that isn't the original
    coat_obj = None
    for obj in bpy.context.selected_objects:
        if obj != physician_obj and obj.type == 'MESH':
            coat_obj = obj
            break

    if coat_obj:
        coat_obj.name = "DoctorCoat"
        print(f"[Separate] Coat object: {coat_obj.name}, "
              f"verts: {len(coat_obj.data.vertices)}, "
              f"faces: {len(coat_obj.data.polygons)}")
    else:
        print("[Separate] ERROR: Could not find separated coat object")

    return coat_obj


def align_coat_to_avatar(coat_obj, avatar_body_obj):
    """Scale and position the coat to match the avatar's proportions."""
    # Get bounding boxes
    avatar_verts = [avatar_body_obj.matrix_world @ v.co for v in avatar_body_obj.data.vertices]
    coat_verts = [coat_obj.matrix_world @ v.co for v in coat_obj.data.vertices]

    if not avatar_verts or not coat_verts:
        print("[Align] No vertices found")
        return

    a_min = Vector((min(v.x for v in avatar_verts),
                     min(v.y for v in avatar_verts),
                     min(v.z for v in avatar_verts)))
    a_max = Vector((max(v.x for v in avatar_verts),
                     max(v.y for v in avatar_verts),
                     max(v.z for v in avatar_verts)))

    c_min = Vector((min(v.x for v in coat_verts),
                     min(v.y for v in coat_verts),
                     min(v.z for v in coat_verts)))
    c_max = Vector((max(v.x for v in coat_verts),
                     max(v.y for v in coat_verts),
                     max(v.z for v in coat_verts)))

    a_size = a_max - a_min
    c_size = c_max - c_min
    a_center = (a_min + a_max) / 2
    c_center = (c_min + c_max) / 2

    # Scale coat to match avatar height, slightly wider for coat-over-body
    COAT_PADDING = 1.04  # 4% larger so coat sits over clothing
    if c_size.y > 0 and c_size.x > 0 and c_size.z > 0:
        scale_x = (a_size.x / c_size.x) * COAT_PADDING
        scale_y = a_size.y / c_size.y
        scale_z = (a_size.z / c_size.z) * COAT_PADDING
        coat_obj.scale = (scale_x, scale_y, scale_z)

    # Apply scale
    bpy.context.view_layer.objects.active = coat_obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # Recalculate after scale apply
    coat_verts_new = [coat_obj.matrix_world @ v.co for v in coat_obj.data.vertices]
    c_min_new = Vector((min(v.x for v in coat_verts_new),
                         min(v.y for v in coat_verts_new),
                         min(v.z for v in coat_verts_new)))
    c_max_new = Vector((max(v.x for v in coat_verts_new),
                         max(v.y for v in coat_verts_new),
                         max(v.z for v in coat_verts_new)))
    c_center_new = (c_min_new + c_max_new) / 2

    # Align centers
    offset = a_center - c_center_new
    coat_obj.location += offset

    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

    print(f"[Align] Avatar size: {a_size}, Coat aligned")


def transfer_weights(coat_obj, avatar_body_obj):
    """Use Data Transfer modifier to copy vertex weights from avatar body to coat."""
    bpy.context.view_layer.objects.active = coat_obj

    # First, ensure coat has all vertex groups that the body has
    for vg in avatar_body_obj.vertex_groups:
        if vg.name not in coat_obj.vertex_groups:
            coat_obj.vertex_groups.new(name=vg.name)

    # Add Data Transfer modifier
    mod = coat_obj.modifiers.new(name="WeightTransfer", type='DATA_TRANSFER')
    mod.object = avatar_body_obj
    mod.use_vert_data = True
    mod.data_types_verts = {'VGROUP_WEIGHTS'}
    mod.vert_mapping = 'POLYINTERP_NEAREST'  # good for different topology

    # Apply the modifier
    bpy.ops.object.modifier_apply(modifier=mod.name)
    print(f"[Weights] Transferred {len(coat_obj.vertex_groups)} vertex groups from body to coat")


def parent_to_armature(coat_obj, armature_obj):
    """Parent coat to armature and add Armature modifier."""
    coat_obj.parent = armature_obj

    # Add Armature modifier
    mod = coat_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = armature_obj

    print(f"[Parent] Coat parented to armature: {armature_obj.name}")


def mask_body_under_coat(avatar_body_obj, coat_obj):
    """Create a vertex group on the body for vertices hidden under the coat,
    then use Mask modifier to hide them (prevents clipping).
    Only masks torso/arm area — NOT face, head, hands, legs."""

    bpy.context.view_layer.objects.active = avatar_body_obj

    # Get coat bounding box (in world space)
    coat_verts = [coat_obj.matrix_world @ v.co for v in coat_obj.data.vertices]
    if not coat_verts:
        return

    c_min = Vector((min(v.x for v in coat_verts),
                     min(v.y for v in coat_verts),
                     min(v.z for v in coat_verts)))
    c_max = Vector((max(v.x for v in coat_verts),
                     max(v.y for v in coat_verts),
                     max(v.z for v in coat_verts)))

    # Shrink the mask box significantly — only hide the torso/upper body area
    # Keep generous margins so face, hands, and legs are never hidden
    coat_height = c_max.y - c_min.y
    margin_top = coat_height * 0.25    # don't mask top 25% (neck/head area)
    margin_bot = coat_height * 0.10    # don't mask bottom 10%
    margin_side = 0.02                 # 2cm inward from edges

    mask_min = Vector((c_min.x + margin_side,
                       c_min.y + margin_bot,
                       c_min.z + margin_side))
    mask_max = Vector((c_max.x - margin_side,
                       c_max.y - margin_top,
                       c_max.z - margin_side))

    # Create vertex group for visible verts
    visible_vg_name = "Visible"
    if visible_vg_name in avatar_body_obj.vertex_groups:
        visible_vg = avatar_body_obj.vertex_groups[visible_vg_name]
    else:
        visible_vg = avatar_body_obj.vertex_groups.new(name=visible_vg_name)

    hidden_count = 0
    visible_indices = []
    for v in avatar_body_obj.data.vertices:
        world_co = avatar_body_obj.matrix_world @ v.co
        if (mask_min.x <= world_co.x <= mask_max.x and
            mask_min.y <= world_co.y <= mask_max.y and
            mask_min.z <= world_co.z <= mask_max.z):
            hidden_count += 1
        else:
            visible_indices.append(v.index)

    # Add visible verts to the group
    visible_vg.add(visible_indices, 1.0, 'REPLACE')

    # Add Mask modifier — show only "Visible" vertex group
    mod = avatar_body_obj.modifiers.new(name="CoatMask", type='MASK')
    mod.vertex_group = visible_vg_name
    mod.invert_vertex_group = False

    print(f"[Mask] Hidden {hidden_count}/{len(avatar_body_obj.data.vertices)} body verts under coat")


def apply_coat_material(coat_obj):
    """Give the coat a clean white material (replacing the physician texture)."""
    # Remove existing materials
    coat_obj.data.materials.clear()

    # Create white coat material
    mat = bpy.data.materials.new(name="WhiteCoat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.94, 0.94, 0.94, 1.0)  # off-white
        bsdf.inputs["Roughness"].default_value = 0.55
        bsdf.inputs["Metallic"].default_value = 0.0

    coat_obj.data.materials.append(mat)
    print("[Material] White coat material applied")


def export_glb(output_path):
    """Export the entire scene as GLB."""
    # Select all mesh objects and the armature
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if obj.type in ('MESH', 'ARMATURE'):
            obj.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        use_selection=True,
        export_animations=True,
        export_skins=True,
        export_morph=True,
        export_morph_normal=True,
        export_materials='EXPORT',
    )
    print(f"[Export] Saved to {output_path}")


def main():
    print("=" * 60)
    print("  Doctor Coat Pipeline — Blender Script")
    print("=" * 60)

    # Validate input files
    if not os.path.exists(AVATAR_GLB):
        print(f"ERROR: Avatar GLB not found: {AVATAR_GLB}")
        sys.exit(1)
    if not os.path.exists(PHYSICIAN_GLB):
        print(f"ERROR: Physician GLB not found: {PHYSICIAN_GLB}")
        sys.exit(1)

    # Step 0: Clean scene
    print("\n[Step 0] Cleaning scene...")
    clean_scene()

    # Step 1: Import avatar
    print("\n[Step 1] Importing avatar...")
    avatar_objects = import_glb(AVATAR_GLB)

    # Find armature and body mesh
    armature = None
    avatar_body = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
        elif obj.type == 'MESH':
            # The outfit mesh has vertex groups (skinned) and covers the torso
            # It's the best source for weight transfer
            mesh_name = obj.data.name if obj.data else ""
            if 'outfit' in mesh_name.lower() or 'outfit' in obj.name.lower():
                avatar_body = obj

    # Fallback: find the skinned mesh with most vertices (excluding hair/eyes/teeth)
    if not avatar_body:
        candidates = []
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.vertex_groups and len(o.data.vertices) > 1000:
                name_lower = (o.name + o.data.name).lower()
                # Skip small parts
                if any(x in name_lower for x in ['eye', 'cornea', 'teeth', 'eyelash']):
                    continue
                candidates.append(o)
        if candidates:
            candidates.sort(key=lambda o: len(o.data.vertices), reverse=True)
            avatar_body = candidates[0]

    if not armature:
        print("ERROR: No armature found in avatar")
        sys.exit(1)
    if not avatar_body:
        print("ERROR: No body mesh found in avatar")
        sys.exit(1)

    print(f"  Armature: {armature.name}")
    print(f"  Body mesh: {avatar_body.name} ({len(avatar_body.data.vertices)} verts)")
    print(f"  Bones: {len(armature.data.bones)}")

    # Step 2: Import physician model
    print("\n[Step 2] Importing physician model...")
    physician_objects = import_glb(PHYSICIAN_GLB)

    physician_mesh = None
    for obj in physician_objects:
        if obj.type == 'MESH':
            physician_mesh = obj
            break

    if not physician_mesh:
        print("ERROR: No mesh found in physician model")
        sys.exit(1)

    print(f"  Physician mesh: {physician_mesh.name} ({len(physician_mesh.data.vertices)} verts)")

    # Step 3: Select coat faces by texture color
    print("\n[Step 3] Selecting coat faces from physician texture...")
    coat_count = select_coat_faces(physician_mesh)
    if coat_count == 0:
        print("ERROR: No coat faces found")
        sys.exit(1)

    # Step 4: Separate coat into new object
    print("\n[Step 4] Separating coat from physician mesh...")
    bpy.ops.object.select_all(action='DESELECT')
    physician_mesh.select_set(True)
    bpy.context.view_layer.objects.active = physician_mesh
    coat_obj = separate_coat(physician_mesh)
    if not coat_obj:
        print("ERROR: Failed to separate coat")
        sys.exit(1)

    # Delete the remaining physician mesh (skin/hair/pants)
    bpy.ops.object.select_all(action='DESELECT')
    physician_mesh.select_set(True)
    bpy.context.view_layer.objects.active = physician_mesh
    bpy.ops.object.delete()

    # Delete any remaining physician objects (armature, empties)
    for obj_name in [o.name for o in physician_objects if o != physician_mesh]:
        if obj_name in bpy.data.objects:
            obj = bpy.data.objects[obj_name]
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.delete()

    # Step 5: Align coat to avatar
    print("\n[Step 5] Aligning coat to avatar proportions...")
    align_coat_to_avatar(coat_obj, avatar_body)

    # Step 6: Transfer bone weights from avatar body to coat
    print("\n[Step 6] Transferring bone weights (Data Transfer modifier)...")
    transfer_weights(coat_obj, avatar_body)

    # Step 7: Parent coat to armature
    print("\n[Step 7] Parenting coat to armature...")
    parent_to_armature(coat_obj, armature)

    # Step 8: Apply white coat material
    print("\n[Step 8] Applying coat material...")
    apply_coat_material(coat_obj)

    # Step 9: Mask body under coat (prevents clipping)
    print("\n[Step 9] Masking body vertices under coat...")
    mask_body_under_coat(avatar_body, coat_obj)

    # Step 10: Export combined GLB
    print("\n[Step 10] Exporting combined GLB...")
    export_glb(OUTPUT_GLB)

    print("\n" + "=" * 60)
    print(f"  Done! Output: {OUTPUT_GLB}")
    print("=" * 60)


if __name__ == "__main__":
    main()
