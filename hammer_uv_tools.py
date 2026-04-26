bl_info = {
    "name": "Hammer-Style Scene + UV Tools",
    "author": "Codex",
    "version": (1, 1, 0),
    "blender": (5, 1, 1),
    "location": "View3D > Sidebar > Hammer",
    "description": "Hammer-inspired blockout + tiled UV tools for faster scene creation",
    "category": "3D View",
}

import bpy
import bmesh
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty
from math import cos, radians, sin
from mathutils import Vector


def _dominant_axis(normal):
    nx, ny, nz = abs(normal.x), abs(normal.y), abs(normal.z)
    if nx >= ny and nx >= nz:
        return "X"
    if ny >= nx and ny >= nz:
        return "Y"
    return "Z"


def _face_uv_from_position(pos, axis):
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


class HAMMER_PG_Settings(bpy.types.PropertyGroup):
    tile_size_u: FloatProperty(name="Tile Size U", min=0.0001, default=1.0)
    tile_size_v: FloatProperty(name="Tile Size V", min=0.0001, default=1.0)
    offset_u: FloatProperty(name="Offset U", default=0.0)
    offset_v: FloatProperty(name="Offset V", default=0.0)
    rotation: FloatProperty(name="Rotation", default=0.0, subtype='ANGLE')
    world_space: BoolProperty(name="World Space", default=True)

    grid_size: FloatProperty(
        name="Grid Size",
        description="Grid and snapping unit in scene units",
        min=0.001,
        default=0.5,
    )
    brush_size_x: FloatProperty(name="Brush X", min=0.001, default=2.0)
    brush_size_y: FloatProperty(name="Brush Y", min=0.001, default=2.0)
    brush_size_z: FloatProperty(name="Brush Z", min=0.001, default=2.0)

    room_size_x: FloatProperty(name="Room X", min=0.1, default=12.0)
    room_size_y: FloatProperty(name="Room Y", min=0.1, default=12.0)
    room_size_z: FloatProperty(name="Room Z", min=0.1, default=5.0)
    wall_thickness: FloatProperty(name="Wall Thickness", min=0.01, default=0.25)

    camera_distance: FloatProperty(name="Camera Distance", min=0.1, default=10.0)
    light_energy: FloatProperty(name="Sun Strength", min=0.0, default=3.0)

    primitive_type: EnumProperty(
        name="Primitive",
        items=(
            ('CUBE', "Cube", "Add cube brush"),
            ('CYLINDER', "Cylinder", "Add cylinder brush"),
            ('PLANE', "Plane", "Add plane brush"),
        ),
        default='CUBE',
    )
    cylinder_verts: IntProperty(name="Cylinder Verts", min=3, max=128, default=16)


class HAMMER_OT_project_tiled(bpy.types.Operator):
    bl_idname = "uv.hammer_project_tiled"
    bl_label = "Hammer Tiled Project"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        settings = context.scene.hammer_settings

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


class HAMMER_OT_reset_uv_settings(bpy.types.Operator):
    bl_idname = "hammer.reset_uv_settings"
    bl_label = "Reset UV"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.hammer_settings
        s.tile_size_u = 1.0
        s.tile_size_v = 1.0
        s.offset_u = 0.0
        s.offset_v = 0.0
        s.rotation = 0.0
        s.world_space = True
        return {'FINISHED'}


class HAMMER_OT_apply_grid_setup(bpy.types.Operator):
    bl_idname = "hammer.apply_grid_setup"
    bl_label = "Apply Hammer Grid"
    bl_description = "Configure scene units and snap settings for Hammer-like blockout"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.hammer_settings
        ts = context.scene.tool_settings

        context.scene.unit_settings.system = 'METRIC'
        context.scene.unit_settings.scale_length = 1.0

        ts.use_snap = True
        ts.snap_elements = {'INCREMENT'}
        ts.snap_target = 'CLOSEST'

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.grid_scale = s.grid_size

        self.report({'INFO'}, f"Grid configured to {s.grid_size:g} units")
        return {'FINISHED'}


class HAMMER_OT_add_brush(bpy.types.Operator):
    bl_idname = "hammer.add_brush"
    bl_label = "Add Brush Primitive"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.hammer_settings
        loc = context.scene.cursor.location.copy()

        if s.primitive_type == 'CUBE':
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
            obj = context.active_object
            obj.scale = Vector((s.brush_size_x / 2.0, s.brush_size_y / 2.0, s.brush_size_z / 2.0))
        elif s.primitive_type == 'CYLINDER':
            r = min(s.brush_size_x, s.brush_size_y) / 2.0
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=s.cylinder_verts,
                radius=r,
                depth=s.brush_size_z,
                location=loc,
            )
            obj = context.active_object
            obj.scale.x *= s.brush_size_x / max(s.brush_size_y, 0.001)
        else:
            bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc)
            obj = context.active_object
            obj.scale = Vector((s.brush_size_x / 2.0, s.brush_size_y / 2.0, 1.0))

        obj.name = f"Brush_{s.primitive_type.title()}"
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return {'FINISHED'}


class HAMMER_OT_make_room_shell(bpy.types.Operator):
    bl_idname = "hammer.make_room_shell"
    bl_label = "Build Room Shell"
    bl_description = "Create a quick room shell for scene blockout"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.hammer_settings
        loc = context.scene.cursor.location.copy()

        bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
        obj = context.active_object
        obj.name = "RoomShell"
        obj.scale = Vector((s.room_size_x / 2.0, s.room_size_y / 2.0, s.room_size_z / 2.0))
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        solidify = obj.modifiers.new(name="RoomWall", type='SOLIDIFY')
        solidify.thickness = -abs(s.wall_thickness)
        solidify.offset = -1.0
        solidify.use_even_offset = True

        bpy.ops.object.modifier_apply(modifier=solidify.name)
        return {'FINISHED'}


class HAMMER_OT_add_scene_rig(bpy.types.Operator):
    bl_idname = "hammer.add_scene_rig"
    bl_label = "Add Camera + Sun Rig"
    bl_description = "Create a fast camera/light setup focused on the 3D cursor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.hammer_settings
        target_loc = context.scene.cursor.location.copy()

        empty = bpy.data.objects.new("SceneTarget", None)
        empty.location = target_loc
        context.collection.objects.link(empty)

        cam_loc = target_loc + Vector((-s.camera_distance, -s.camera_distance, s.camera_distance * 0.7))
        bpy.ops.object.camera_add(location=cam_loc)
        cam = context.active_object
        cam.name = "SceneCamera"

        track = cam.constraints.new(type='TRACK_TO')
        track.target = empty
        track.track_axis = 'TRACK_NEGATIVE_Z'
        track.up_axis = 'UP_Y'

        sun_loc = target_loc + Vector((s.camera_distance * 0.5, -s.camera_distance * 0.5, s.camera_distance))
        bpy.ops.object.light_add(type='SUN', location=sun_loc)
        sun = context.active_object
        sun.name = "SceneSun"
        sun.data.energy = s.light_energy

        self.report({'INFO'}, "Added camera, target, and sun")
        return {'FINISHED'}


class HAMMER_PT_tools_panel(bpy.types.Panel):
    bl_label = "Hammer Tools"
    bl_idname = "HAMMER_PT_tools_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Hammer'

    def draw(self, context):
        s = context.scene.hammer_settings
        layout = self.layout

        box = layout.box()
        box.label(text="Scene/Grid", icon='GRID')
        box.prop(s, "grid_size")
        box.operator("hammer.apply_grid_setup", icon='SNAP_GRID')

        box = layout.box()
        box.label(text="Brush Builder", icon='MESH_CUBE')
        box.prop(s, "primitive_type")
        box.prop(s, "brush_size_x")
        box.prop(s, "brush_size_y")
        box.prop(s, "brush_size_z")
        if s.primitive_type == 'CYLINDER':
            box.prop(s, "cylinder_verts")
        box.operator("hammer.add_brush", icon='ADD')

        box = layout.box()
        box.label(text="Room Shell", icon='MOD_SOLIDIFY')
        box.prop(s, "room_size_x")
        box.prop(s, "room_size_y")
        box.prop(s, "room_size_z")
        box.prop(s, "wall_thickness")
        box.operator("hammer.make_room_shell", icon='HOME')

        box = layout.box()
        box.label(text="Scene Rig", icon='CAMERA_DATA')
        box.prop(s, "camera_distance")
        box.prop(s, "light_energy")
        box.operator("hammer.add_scene_rig", icon='OUTLINER_OB_CAMERA')

        box = layout.box()
        box.label(text="Hammer UV Tiling", icon='GROUP_UVS')
        box.prop(s, "tile_size_u")
        box.prop(s, "tile_size_v")
        box.prop(s, "offset_u")
        box.prop(s, "offset_v")
        box.prop(s, "rotation")
        box.prop(s, "world_space")
        row = box.row(align=True)
        row.operator("uv.hammer_project_tiled", icon='GROUP_UVS')
        row.operator("hammer.reset_uv_settings", icon='LOOP_BACK')


classes = (
    HAMMER_PG_Settings,
    HAMMER_OT_project_tiled,
    HAMMER_OT_reset_uv_settings,
    HAMMER_OT_apply_grid_setup,
    HAMMER_OT_add_brush,
    HAMMER_OT_make_room_shell,
    HAMMER_OT_add_scene_rig,
    HAMMER_PT_tools_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.hammer_settings = bpy.props.PointerProperty(type=HAMMER_PG_Settings)


def unregister():
    del bpy.types.Scene.hammer_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
