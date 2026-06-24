bl_info = {
    "name": "Anime Cloth Fold Generator",
    "author": "Codex",
    "version": (1, 0, 0),
    "blender": (5, 1, 2),
    "location": "View3D > Sidebar > Cloth Folds",
    "description": "Paint-directed procedural anime cloth folds with preview, apply, and fold attributes",
    "category": "Object",
}

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, PointerProperty, StringProperty

FOLD_VERTEX_GROUP = "Cloth Folds Mask"
FOLD_TEXTURE = "Anime Cloth Fold Noise"
FOLD_DISPLACE = "Anime Cloth Folds Preview"
FOLD_ATTRIBUTE = "cloth_folds"


def _active_mesh_object(context):
    obj = context.active_object
    if obj is None or obj.type != 'MESH':
        return None
    return obj


def _ensure_vertex_group(obj):
    group = obj.vertex_groups.get(FOLD_VERTEX_GROUP)
    if group is None:
        group = obj.vertex_groups.new(name=FOLD_VERTEX_GROUP)
    return group


def _vertex_weight(group, vertex_index):
    try:
        return group.weight(vertex_index)
    except RuntimeError:
        return 0.0


def _ensure_fold_attribute(obj, name=FOLD_ATTRIBUTE):
    mesh = obj.data
    attr = mesh.attributes.get(name)
    if attr is None:
        attr = mesh.attributes.new(name=name, type='FLOAT', domain='POINT')
    return attr


def _write_fold_attribute(obj, name=FOLD_ATTRIBUTE):
    group = _ensure_vertex_group(obj)
    attr = _ensure_fold_attribute(obj, name)
    for vertex in obj.data.vertices:
        attr.data[vertex.index].value = _vertex_weight(group, vertex.index)
    obj.data.update()


def _ensure_texture(settings):
    tex = bpy.data.textures.get(FOLD_TEXTURE)
    if tex is None:
        tex = bpy.data.textures.new(FOLD_TEXTURE, type='VORONOI')
    tex.type = settings.noise_type
    if hasattr(tex, "noise_scale"):
        tex.noise_scale = settings.fold_spacing
    if hasattr(tex, "intensity"):
        tex.intensity = settings.contrast
    if hasattr(tex, "contrast"):
        tex.contrast = settings.contrast
    if hasattr(tex, "nabla"):
        tex.nabla = settings.sharpness
    return tex


def _ensure_preview_modifier(obj, settings):
    group = _ensure_vertex_group(obj)
    tex = _ensure_texture(settings)
    mod = obj.modifiers.get(FOLD_DISPLACE)
    if mod is None:
        mod = obj.modifiers.new(FOLD_DISPLACE, 'DISPLACE')
    mod.texture = tex
    mod.vertex_group = group.name
    mod.strength = settings.strength
    mod.mid_level = settings.mid_level
    mod.direction = settings.direction
    mod.show_viewport = settings.preview_enabled
    mod.show_render = settings.preview_enabled
    return mod


class ANIMEFOLDS_PG_Settings(bpy.types.PropertyGroup):
    preview_enabled: BoolProperty(
        name="Preview",
        description="Show non-destructive fold displacement in the viewport and render",
        default=True,
    )
    strength: FloatProperty(
        name="Fold Strength",
        description="Height of generated folds; use negative values for inward creases",
        default=0.035,
        min=-1.0,
        max=1.0,
        precision=3,
    )
    fold_spacing: FloatProperty(
        name="Fold Spacing",
        description="Distance between procedural fold ridges",
        default=0.65,
        min=0.01,
        max=20.0,
        precision=3,
    )
    contrast: FloatProperty(
        name="Fold Contrast",
        description="How strongly folds separate from flat fabric",
        default=3.0,
        min=0.1,
        max=10.0,
        precision=2,
    )
    sharpness: FloatProperty(
        name="Crease Sharpness",
        description="Small values create sharper anime-style crease lines",
        default=0.03,
        min=0.001,
        max=1.0,
        precision=3,
    )
    mid_level: FloatProperty(
        name="Mid Level",
        description="Texture value treated as no displacement",
        default=0.48,
        min=0.0,
        max=1.0,
        precision=3,
    )
    direction: EnumProperty(
        name="Direction",
        description="Displacement direction for the folds",
        items=(
            ('NORMAL', "Normal", "Push folds along vertex normals"),
            ('X', "X", "Push folds along local X"),
            ('Y', "Y", "Push folds along local Y"),
            ('Z', "Z", "Push folds along local Z"),
        ),
        default='NORMAL',
    )
    noise_type: EnumProperty(
        name="Fold Pattern",
        description="Procedural texture used to create fold lines",
        items=(
            ('VORONOI', "Anime Ridges", "Sharper broken ridges for stylized folds"),
            ('CLOUDS', "Soft Cloth", "Softer cloudy folding"),
            ('STUCCI', "Wrinkles", "Fine wrinkle-like bumps"),
        ),
        default='VORONOI',
    )
    attribute_name: StringProperty(
        name="Attribute Name",
        description="Mesh point attribute written from the fold paint mask for materials or selection",
        default=FOLD_ATTRIBUTE,
    )


class ANIMEFOLDS_OT_setup_mask(bpy.types.Operator):
    bl_idname = "object.anime_folds_setup_mask"
    bl_label = "Create / Select Fold Paint Mask"
    bl_description = "Create the Cloth Folds Mask vertex group and switch to Weight Paint so folds can be drawn"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _active_mesh_object(context) is not None

    def execute(self, context):
        obj = _active_mesh_object(context)
        group = _ensure_vertex_group(obj)
        obj.vertex_groups.active_index = group.index
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        self.report({'INFO'}, "Paint white where anime cloth folds should appear")
        return {'FINISHED'}


class ANIMEFOLDS_OT_preview(bpy.types.Operator):
    bl_idname = "object.anime_folds_preview"
    bl_label = "Preview Cloth Folds"
    bl_description = "Create or update the non-destructive procedural cloth fold preview"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _active_mesh_object(context) is not None

    def execute(self, context):
        obj = _active_mesh_object(context)
        settings = context.scene.anime_folds_settings
        _ensure_preview_modifier(obj, settings)
        _write_fold_attribute(obj, settings.attribute_name)
        self.report({'INFO'}, "Anime cloth fold preview updated")
        return {'FINISHED'}


class ANIMEFOLDS_OT_apply(bpy.types.Operator):
    bl_idname = "object.anime_folds_apply"
    bl_label = "Apply Cloth Folds"
    bl_description = "Apply the preview modifier to the mesh and keep the cloth fold attribute"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _active_mesh_object(context) is not None

    def execute(self, context):
        obj = _active_mesh_object(context)
        settings = context.scene.anime_folds_settings
        mod = _ensure_preview_modifier(obj, settings)
        _write_fold_attribute(obj, settings.attribute_name)
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.modifier_apply(modifier=mod.name)
        self.report({'INFO'}, "Applied anime cloth folds and wrote fold attribute")
        return {'FINISHED'}


class ANIMEFOLDS_OT_create_attribute(bpy.types.Operator):
    bl_idname = "object.anime_folds_create_attribute"
    bl_label = "Create / Refresh Fold Attribute"
    bl_description = "Write a float point attribute from the fold weight paint mask for materials or texture selection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _active_mesh_object(context) is not None

    def execute(self, context):
        obj = _active_mesh_object(context)
        settings = context.scene.anime_folds_settings
        _write_fold_attribute(obj, settings.attribute_name)
        self.report({'INFO'}, f"Wrote fold attribute '{settings.attribute_name}'")
        return {'FINISHED'}


class ANIMEFOLDS_OT_remove_preview(bpy.types.Operator):
    bl_idname = "object.anime_folds_remove_preview"
    bl_label = "Remove Preview"
    bl_description = "Remove the non-applied fold preview modifier"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = _active_mesh_object(context)
        return obj is not None and obj.modifiers.get(FOLD_DISPLACE) is not None

    def execute(self, context):
        obj = _active_mesh_object(context)
        obj.modifiers.remove(obj.modifiers[FOLD_DISPLACE])
        self.report({'INFO'}, "Removed anime cloth fold preview")
        return {'FINISHED'}


class ANIMEFOLDS_PT_panel(bpy.types.Panel):
    bl_label = "Anime Cloth Folds"
    bl_idname = "ANIMEFOLDS_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Cloth Folds'

    @classmethod
    def poll(cls, context):
        return _active_mesh_object(context) is not None

    def draw(self, context):
        layout = self.layout
        settings = context.scene.anime_folds_settings
        obj = context.active_object

        col = layout.column(align=True)
        col.label(text="1) Draw fold mask")
        col.operator("object.anime_folds_setup_mask", icon='WPAINT_HLT')
        col.label(text=f"Vertex Group: {FOLD_VERTEX_GROUP}")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="2) Fold style")
        col.prop(settings, "preview_enabled")
        col.prop(settings, "noise_type")
        col.prop(settings, "strength")
        col.prop(settings, "fold_spacing")
        col.prop(settings, "contrast")
        col.prop(settings, "sharpness")
        col.prop(settings, "mid_level")
        col.prop(settings, "direction")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="3) Preview or apply")
        row = col.row(align=True)
        row.operator("object.anime_folds_preview", icon='MOD_DISPLACE')
        row.operator("object.anime_folds_apply", icon='CHECKMARK')
        col.operator("object.anime_folds_remove_preview", icon='X')

        layout.separator()
        col = layout.column(align=True)
        col.label(text="4) Texture selection attribute")
        col.prop(settings, "attribute_name")
        col.operator("object.anime_folds_create_attribute", icon='GROUP_VERTEX')

        if obj.vertex_groups.get(FOLD_VERTEX_GROUP) is None:
            layout.separator()
            layout.label(text="Tip: create the mask first, then paint white folds.", icon='INFO')


classes = (
    ANIMEFOLDS_PG_Settings,
    ANIMEFOLDS_OT_setup_mask,
    ANIMEFOLDS_OT_preview,
    ANIMEFOLDS_OT_apply,
    ANIMEFOLDS_OT_create_attribute,
    ANIMEFOLDS_OT_remove_preview,
    ANIMEFOLDS_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.anime_folds_settings = PointerProperty(type=ANIMEFOLDS_PG_Settings)


def unregister():
    if hasattr(bpy.types.Scene, "anime_folds_settings"):
        del bpy.types.Scene.anime_folds_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
