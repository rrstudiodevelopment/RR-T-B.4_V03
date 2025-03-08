
import bpy
import collections

layout_mode = "COLUMN"  # Bisa diubah menjadi "ROW" atau "COLUMN"
bpy.types.Scene.show_bone_collections = bpy.props.BoolProperty(name="Show Bone Collections", default=False)

def get_bone_collections(armature):
    """Mendapatkan daftar Bone Collections dari armature."""
    if hasattr(armature, "collections"):
        return armature.collections
    return []

class RigLayersPopup(bpy.types.Operator):
    bl_idname = "view3d.rig_layers_popup"
    bl_label = "Bone Collections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        armature = obj.data
        scene = context.scene

        row_table = collections.defaultdict(list)
        
        for coll in get_bone_collections(armature):
            row_id = coll.get('rigify_ui_row', 0)
            row_table[row_id].append(coll)
        
        if row_table:
            if layout_mode == "ROW":
                row = layout.row(align=True)
                row.scale_y = 1.2
            else:
                row = layout.column(align=True)
                row.scale_y = 1.0

            for row_id in sorted(row_table.keys()):
                row_buttons = row_table[row_id]
                
                for coll in row_buttons:
                    title = coll.get('rigify_ui_title') or coll.name
                    row.prop(coll, 'is_visible', toggle=True, text=title, translate=False)
        else:
            layout.label(text="No Bone Collections Found")

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)

class RigLayersHeader(bpy.types.Header):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.rig_layers_popup", text="Bone Collections", icon='GROUP_BONE')

classes = [RigLayersPopup, RigLayersHeader]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_HT_tool_header.append(RigLayersHeader.draw)

def unregister():
    for cls in reversed(classes):
        RigLayersHeader
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_HT_tool_header.remove(RigLayersHeader.draw)

if __name__ == "__main__":
    register()
