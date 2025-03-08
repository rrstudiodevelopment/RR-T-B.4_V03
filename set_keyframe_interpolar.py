bl_info = {
    "name": "Graph Editor Keyframe Interpolation",
    "blender": (3, 0, 0),
    "category": "Animation",
}

import bpy

class GRAPH_PT_interpolation_panel(bpy.types.Panel):
    """Panel untuk mengubah interpolation keyframe di Graph Editor"""
    bl_label = "Keyframe Interpolation"
    bl_idname = "GRAPH_PT_interpolation"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Raha Keyframe Editor"

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Set Keyframe Interpolation")
        
        layout.label(text="Interpolation")
        row = layout.row()
        row.operator("graph.set_interpolation", text="", icon='IPO_CONSTANT').interpolation = 'CONSTANT'
        row.operator("graph.set_interpolation", text="", icon='IPO_LINEAR').interpolation = 'LINEAR'
        row.operator("graph.set_interpolation", text="", icon='IPO_BEZIER').interpolation = 'BEZIER'
        
        layout.label(text="Easing (by strength)")
        row = layout.row()
        row.operator("graph.set_interpolation", text="", icon='IPO_SINE').interpolation = 'SINE'
        row.operator("graph.set_interpolation", text="", icon='IPO_QUAD').interpolation = 'QUAD'
        row.operator("graph.set_interpolation", text="", icon='IPO_CUBIC').interpolation = 'CUBIC'

        row.operator("graph.set_interpolation", text="", icon='IPO_QUART').interpolation = 'QUART'
        row.operator("graph.set_interpolation", text="", icon='IPO_QUINT').interpolation = 'QUINT'
        row.operator("graph.set_interpolation", text="", icon='IPO_EXPO').interpolation = 'EXPO'
        row = layout.row()
        row.operator("graph.set_interpolation", text="", icon='IPO_CIRC').interpolation = 'CIRC'
        
        layout.label(text="Dynamic Effects")
        row = layout.row()
        row.operator("graph.set_interpolation", text="", icon='IPO_BACK').interpolation = 'BACK'
        row.operator("graph.set_interpolation", text="", icon='IPO_BOUNCE').interpolation = 'BOUNCE'
        row.operator("graph.set_interpolation", text="", icon='IPO_ELASTIC').interpolation = 'ELASTIC'

class GRAPH_OT_set_interpolation(bpy.types.Operator):
    """Mengatur interpolasi keyframe di Graph Editor"""
    bl_idname = "graph.set_interpolation"
    bl_label = "Set Keyframe Interpolation"
    bl_options = {'REGISTER', 'UNDO'}

    interpolation: bpy.props.EnumProperty(
        items=[
            ('CONSTANT', "Constant", "No interpolation"),
            ('LINEAR', "Linear", "Linear interpolation"),
            ('BEZIER', "Bezier", "Smooth interpolation"),
            ('SINE', "Sinusoidal", "Sinusoidal easing"),
            ('QUAD', "Quadratic", "Quadratic easing"),
            ('CUBIC', "Cubic", "Cubic easing"),
            ('QUART', "Quartic", "Quartic easing"),
            ('QUINT', "Quintic", "Quintic easing"),
            ('EXPO', "Exponential", "Exponential easing"),
            ('CIRC', "Circular", "Circular easing"),
            ('BACK', "Back", "Back effect"),
            ('BOUNCE', "Bounce", "Bounce effect"),
            ('ELASTIC', "Elastic", "Elastic effect"),
        ]
    )

    def execute(self, context):
        obj = context.object
        if not obj or not obj.animation_data:
            self.report({'WARNING'}, "No active object with animation data")
            return {'CANCELLED'}

        action = obj.animation_data.action
        if not action:
            self.report({'WARNING'}, "No action found")
            return {'CANCELLED'}

        for fcurve in action.fcurves:
            for kp in fcurve.keyframe_points:
                if kp.select_control_point:
                    kp.interpolation = self.interpolation
        
        return {'FINISHED'}

classes = [
    GRAPH_PT_interpolation_panel,
    GRAPH_OT_set_interpolation,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()