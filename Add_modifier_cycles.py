bl_info = {
    "name": "Cycles Anim Modifier",
    "blender": (3, 0, 0),
    "category": "Animation",
}

import bpy

def add_cycles_modifier():
    obj = bpy.context.object
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return
    
    for fcurve in obj.animation_data.action.fcurves:
        if fcurve.select:
            if not any(m.type == 'CYCLES' for m in fcurve.modifiers):
                modifier = fcurve.modifiers.new(type='CYCLES')
                modifier.influence = 1.0  # Pastikan influence diaktifkan
    
    refresh_graph_editor()

def remove_cycles_modifier():
    obj = bpy.context.object
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return
    
    for fcurve in obj.animation_data.action.fcurves:
        if fcurve.select:
            for modifier in list(fcurve.modifiers):  # Hapus modifier satu per satu
                if modifier.type == 'CYCLES':
                    fcurve.modifiers.remove(modifier)
    
    refresh_graph_editor()

def set_cycles_mode(mode, before=True):
    obj = bpy.context.object
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return
    
    for fcurve in obj.animation_data.action.fcurves:
        if fcurve.select:
            for modifier in fcurve.modifiers:
                if modifier.type == 'CYCLES':
                    if before:
                        modifier.mode_before = mode
                    else:
                        modifier.mode_after = mode
    
    refresh_graph_editor()

def refresh_graph_editor():
    bpy.context.scene.frame_set(bpy.context.scene.frame_current + 1)
    bpy.context.scene.frame_set(bpy.context.scene.frame_current - 1)

class ANIM_OT_AddCycles(bpy.types.Operator):
    bl_idname = "anim.add_cycles"
    bl_label = "Add Cycles Modifier"
    bl_description = "Add Cycles modifier to selected F-Curves"
    
    def execute(self, context):
        add_cycles_modifier()
        return {'FINISHED'}

class ANIM_OT_RemoveCycles(bpy.types.Operator):
    bl_idname = "anim.remove_cycles"
    bl_label = "Remove Cycles Modifier"
    bl_description = "Remove Cycles modifier from selected F-Curves"
    
    def execute(self, context):
        remove_cycles_modifier()
        return {'FINISHED'}

class ANIM_OT_SetCyclesMode(bpy.types.Operator):
    bl_idname = "anim.set_cycles_mode"
    bl_label = "Set Cycles Mode"
    bl_description = "Set Before or After Mode for Cycles Modifier"
    before: bpy.props.BoolProperty(default=True)
    mode: bpy.props.EnumProperty(
        items=[
            ('NONE', "No Cycles", "No Cycles"),
            ('REPEAT', "Repeat Motion", "Repeat Motion"),
            ('REPEAT_OFFSET', "Repeat with Offset", "Repeat with Offset"),
            ('MIRROR', "Repeat Mirrored", "Repeat Mirrored")
        ]
    )
    
    def execute(self, context):
        set_cycles_mode(self.mode, before=self.before)
        return {'FINISHED'}

class ANIM_PT_CyclesPanel(bpy.types.Panel):
    bl_label = "Cycles Anim"
    bl_idname = "ANIM_PT_CyclesPanel"
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "UI"
#    bl_category = "Cycles Anim"
    
#    def draw(self, context):
#        layout = self.layout
#       layout.operator("anim.add_cycles", text="Add Cycles")
#        layout.operator("anim.remove_cycles", text="Delete Cycles")
#        layout.separator()
#        layout.label(text="Set Cycles Mode")
#        col = layout.column()
#        col.operator_menu_enum("anim.set_cycles_mode", "mode", text="Before Mode").before = True
#        col.operator_menu_enum("anim.set_cycles_mode", "mode", text="After Mode").before = False

def register():
    bpy.utils.register_class(ANIM_OT_AddCycles)
    bpy.utils.register_class(ANIM_OT_RemoveCycles)
    bpy.utils.register_class(ANIM_OT_SetCyclesMode)
#    bpy.utils.register_class(ANIM_PT_CyclesPanel)

def unregister():
    bpy.utils.unregister_class(ANIM_OT_AddCycles)
    bpy.utils.unregister_class(ANIM_OT_RemoveCycles)
    bpy.utils.unregister_class(ANIM_OT_SetCyclesMode)
    bpy.utils.unregister_class(ANIM_PT_CyclesPanel)

if __name__ == "__main__":
    register()
