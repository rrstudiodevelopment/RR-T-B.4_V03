import bpy

def get_selected_keyframes():
    obj = bpy.context.object
    selected_keyframes = []
    
    if not obj:
        return selected_keyframes
    
    # Check for object animation data
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            # Check if the fcurve is related to a bone (pose mode)
            if fcurve.data_path.startswith("pose.bones["):
                for keyframe in fcurve.keyframe_points:
                    if keyframe.select_control_point:
                        selected_keyframes.append((fcurve, keyframe))
            # Check for object-level keyframes (location, rotation, scale)
            else:
                for keyframe in fcurve.keyframe_points:
                    if keyframe.select_control_point:
                        selected_keyframes.append((fcurve, keyframe))
    
    return selected_keyframes

class GRAPH_OT_EditKeyframes(bpy.types.Operator):
    bl_idname = "graph.edit_keyframes"
    bl_label = "Edit Keyframes"

    value: bpy.props.FloatProperty(name="Value")

    def execute(self, context):
        selected_keyframes = get_selected_keyframes()
        obj = context.object
        
        if not obj or not obj.pose:
            self.report({'WARNING'}, "No active object or pose mode detected!")
            return {'CANCELLED'}
        
        active_bone = obj.pose.bones.get(obj.data.bones.active.name) if obj.data.bones.active else None
        
        if not active_bone:
            self.report({'WARNING'}, "No active bone selected!")
            return {'CANCELLED'}
        
        # Filter keyframes to only those related to the active bone
        filtered_keyframes = [(f, k) for f, k in selected_keyframes if f'pose.bones["{active_bone.name}"]' in f.data_path]
        
        if filtered_keyframes:
            for fcurve, keyframe in filtered_keyframes:
                keyframe.co.y = self.value
                fcurve.update()
            context.area.tag_redraw()
        else:
            self.report({'WARNING'}, "No keyframe found for active bone!")
        return {'FINISHED'}


class GRAPH_PT_KeyframeEditor(bpy.types.Panel):
    bl_label = "Raha Keyframe Editor"
    bl_idname = "GRAPH_PT_keyframe_editor"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Raha Keyframe Editor'

    @classmethod
    def poll(cls, context):
        # Ensure the panel only appears in the Graph Editor
        return context.area.type == 'GRAPH_EDITOR'

        
    def draw(self, context):
        layout = self.layout
        selected_keyframes = get_selected_keyframes()
        obj = context.object
        
        if not obj or not obj.pose:
            layout.label(text="No active object or pose mode detected!")
            return
        
        active_bone = obj.pose.bones.get(obj.data.bones.active.name) if obj.data.bones.active else None
        active_bone_name = active_bone.name if active_bone else "None"
        
        layout.label(text="Edit Value")
        layout.label(text=f"Active Bone: {active_bone_name}")
        
        # Filter keyframes to only those related to the active bone
        filtered_keyframes = [(f, k) for f, k in selected_keyframes if active_bone and f'pose.bones["{active_bone.name}"]' in f.data_path]
        
        if filtered_keyframes:
            active_fcurve, active_keyframe = filtered_keyframes[-1]
            
            layout.label(text=f"Frame: {active_keyframe.co.x:.2f}")
            
            data_path = active_fcurve.data_path
            axis = active_fcurve.array_index
            axis_name = ["X", "Y", "Z"][axis]
            
            layout.label(text=f"Type: {data_path}, Axis: {axis_name}")
            layout.prop(active_keyframe, "co", text="Value", index=1)
            
            op = layout.operator("graph.edit_keyframes", text="Apply to selected")
            op.value = active_keyframe.co.y
        else:
            layout.label(text="No keyframe selected or not matching active bone")
            
        layout.label(text="Animation Cycles")           
        layout = self.layout
        layout.operator("anim.add_cycles", text="Add Cycles")
        layout.operator("anim.remove_cycles", text="Delete Cycles")
        layout.separator()
        layout.label(text="Set Cycles Mode")
        col = layout.column()
        col.operator_menu_enum("anim.set_cycles_mode", "mode", text="Before Mode").before = True
        col.operator_menu_enum("anim.set_cycles_mode", "mode", text="After Mode").before = False            


def register():
    bpy.utils.register_class(GRAPH_OT_EditKeyframes)
    bpy.utils.register_class(GRAPH_PT_KeyframeEditor)

def unregister():
    bpy.utils.unregister_class(GRAPH_OT_EditKeyframes)
    bpy.utils.unregister_class(GRAPH_PT_KeyframeEditor)

if __name__ == "__main__":
    register()