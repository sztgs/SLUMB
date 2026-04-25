bl_info = {
    "name": "Hammer-Style UV Tiling",
    "author": "Codex",
    "version": (1, 0, 0),
    "blender": (5, 1, 1),
    "location": "View3D > Sidebar > UV",
    "description": "Fast Hammer-like tiled UV projection that prevents stretching",
    "category": "UV",
}

import bpy
import bmesh
from bpy.props import BoolProperty, FloatProperty
from math import cos, radians, sin


def _dominant_axis(normal):
    nx, ny, nz = abs(normal.x), abs(normal.y), abs(normal.z)
    if nx >= ny and nx >= nz:
        return "X"
    if ny >= nx and ny >= nz:
        return "Y"
    return "Z"


def _face_uv_from_position(pos, axis):
    # Hammer-style planar alignment by dominant face axis.
    # U/V are taken from world/object coordinates, not normalized,
    # so texture tiling remains consistent and does not stretch.
    if axis == "X":
        return pos.y, pos.z
    if axis == "Y":
        return pos.x, pos.z
    return pos.x, pos.y


def _rotate_uv(u, v, angle_deg):
    if angle_deg == 0.0:
        return u, v
    a = radians(angle_deg)
    ca = cos(a)
    sa = sin(a)
    return (u * ca - v * sa), (u * sa + v * ca)


class HAMMERUV_PG_Settings(bpy.types.PropertyGroup):
    tile_size_u: FloatProperty(
        name="Tile Size U",
        description="World/object units covered by one texture tile in U",
        min=0.0001,
        default=1.0,
    )
    tile_size_v: FloatProperty(
        name="Tile Size V",
        description="World/object units covered by one texture tile in V",
        min=0.0001,
        default=1.0,
    )
    offset_u: FloatProperty(
        name="Offset U",
        description="Offset in UV tiles",
        default=0.0,
    )
    offset_v: FloatProperty(
        name="Offset V",
        description="Offset in UV tiles",
        default=0.0,
    )
    rotation: FloatProperty(
        name="Rotation",
        description="UV rotation in degrees",
        default=0.0,
        subtype='ANGLE',
    )
    world_space: BoolProperty(
        name="World Space",
        description="Keep texture scale aligned in world space (like Hammer)",
        default=True,
    )


class HAMMERUV_OT_project_tiled(bpy.types.Operator):
    bl_idname = "uv.hammer_project_tiled"
    bl_label = "Hammer Tiled Project"
    bl_description = "Project selected faces with Hammer-style tiled UVs"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (
            obj is not None
            and obj.type == 'MESH'
            and context.mode == 'EDIT_MESH'
        )

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        settings = context.scene.hammer_uv_settings

        bm = bmesh.from_edit_mesh(mesh)
        uv_layer = bm.loops.layers.uv.verify()

        wm = obj.matrix_world
        selected_faces = [f for f in bm.faces if f.select]
        if not selected_faces:
            self.report({'WARNING'}, "No selected faces")
            return {'CANCELLED'}

        for face in selected_faces:
            face_normal = (wm.to_3x3() @ face.normal).normalized() if settings.world_space else face.normal
            axis = _dominant_axis(face_normal)

            for loop in face.loops:
                co = wm @ loop.vert.co if settings.world_space else loop.vert.co
                u, v = _face_uv_from_position(co, axis)
                u, v = _rotate_uv(u, v, settings.rotation)

                uv = loop[uv_layer].uv
                uv.x = (u / settings.tile_size_u) + settings.offset_u
                uv.y = (v / settings.tile_size_v) + settings.offset_v

        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        self.report({'INFO'}, f"Projected {len(selected_faces)} faces")
        return {'FINISHED'}


class HAMMERUV_OT_reset_settings(bpy.types.Operator):
    bl_idname = "uv.hammer_reset_settings"
    bl_label = "Reset Settings"
    bl_description = "Reset Hammer UV settings to defaults"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.hammer_uv_settings
        s.tile_size_u = 1.0
        s.tile_size_v = 1.0
        s.offset_u = 0.0
        s.offset_v = 0.0
        s.rotation = 0.0
        s.world_space = True
        return {'FINISHED'}


class HAMMERUV_PT_panel(bpy.types.Panel):
    bl_label = "Hammer UV Tiling"
    bl_idname = "HAMMERUV_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UV'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        s = context.scene.hammer_uv_settings

        col = layout.column(align=True)
        col.label(text="Tile scale")
        col.prop(s, "tile_size_u")
        col.prop(s, "tile_size_v")

        col = layout.column(align=True)
        col.label(text="Transform")
        col.prop(s, "offset_u")
        col.prop(s, "offset_v")
        col.prop(s, "rotation")

        layout.prop(s, "world_space")
        row = layout.row(align=True)
        row.operator("uv.hammer_project_tiled", icon='GROUP_UVS')
        row.operator("uv.hammer_reset_settings", icon='LOOP_BACK')

        layout.separator()
        layout.label(text="Usage:")
        layout.label(text="1) Edit Mode, select faces")
        layout.label(text="2) Set tile size")
        layout.label(text="3) Click Hammer Tiled Project")


classes = (
    HAMMERUV_PG_Settings,
    HAMMERUV_OT_project_tiled,
    HAMMERUV_OT_reset_settings,
    HAMMERUV_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.hammer_uv_settings = bpy.props.PointerProperty(type=HAMMERUV_PG_Settings)


def unregister():
    del bpy.types.Scene.hammer_uv_settings

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
