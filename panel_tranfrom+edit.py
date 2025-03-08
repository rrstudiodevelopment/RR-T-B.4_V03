
import bpy

class TransformPanel(bpy.types.Panel):
    bl_label = "Raha Edit Value"
    bl_idname = "VIEW3D_PT_transform_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Item"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object

        # Ensure we're in Pose Mode and have an armature selected
        if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
            # Location Panel
            box = layout.box()
            box.operator("pose.reset_all", text="Reset ALL")
            box.label(text="Location")
            row = box.row(align=True)
            row.prop(scene, "custom_location", text="Values")
            row = box.row(align=True)
            row.prop(scene, "custom_location_axes", text="Axes")
            box.operator("pose.apply_location", text="Apply Location")

            # Rotation Panel
            box = layout.box()
            box.label(text="Rotation")
            row = box.row(align=True)
            row.prop(scene, "custom_rotation", text="Values")
            row = box.row(align=True)
            row.prop(scene, "custom_rotation_axes", text="Axes")
            box.operator("pose.apply_rotation", text="Apply Rotation")

            # Scale Panel
            box = layout.box()
            box.label(text="Scale")
            row = box.row(align=True)
            row.prop(scene, "custom_scale", text="Values")
            row = box.row(align=True)
            row.prop(scene, "custom_scale_axes", text="Axes")
            box.operator("pose.apply_scale", text="Apply Scale")


class ApplyLocationOperator(bpy.types.Operator):
    bl_idname = "pose.apply_location"
    bl_label = "Apply Location"

    def execute(self, context):
        scene = context.scene
        obj = context.active_object
        for bone in obj.pose.bones:
            if bone.bone.select:
                for i in range(3):
                    if scene.custom_location_axes[i]:
                        bone.location[i] = scene.custom_location[i]
        self.report({'INFO'}, "Applied Location to selected bones")
        return {'FINISHED'}

class ResetLocationOperator(bpy.types.Operator):
    bl_idname = "pose.reset_location"
    bl_label = "Reset Location"

    def execute(self, context):
        obj = context.active_object
        for bone in obj.pose.bones:
            if bone.bone.select:
                bone.location = (0.0, 0.0, 0.0)
        self.report({'INFO'}, "Reset Location to default (0, 0, 0) for selected bones")
        return {'FINISHED'}

class ApplyRotationOperator(bpy.types.Operator):
    bl_idname = "pose.apply_rotation"
    bl_label = "Apply Rotation"

    def execute(self, context):
        scene = context.scene
        obj = context.active_object
        for bone in obj.pose.bones:
            if bone.bone.select:
                for i in range(3):
                    if scene.custom_rotation_axes[i]:
                        bone.rotation_euler[i] = scene.custom_rotation[i]
        self.report({'INFO'}, "Applied Rotation to selected bones")
        return {'FINISHED'}

class ResetRotationOperator(bpy.types.Operator):
    bl_idname = "pose.reset_rotation"
    bl_label = "Reset Rotation"

    def execute(self, context):
        obj = context.active_object
        for bone in obj.pose.bones:
            if bone.bone.select:
                bone.rotation_euler = (0.0, 0.0, 0.0)
        self.report({'INFO'}, "Reset Rotation to default (0, 0, 0) for selected bones")
        return {'FINISHED'}

class ApplyScaleOperator(bpy.types.Operator):
    bl_idname = "pose.apply_scale"
    bl_label = "Apply Scale"

    def execute(self, context):
        scene = context.scene
        obj = context.active_object
        for bone in obj.pose.bones:
            if bone.bone.select:
                for i in range(3):
                    if scene.custom_scale_axes[i]:
                        bone.scale[i] = scene.custom_scale[i]
        self.report({'INFO'}, "Applied Scale to selected bones")
        return {'FINISHED'}

class ResetScaleOperator(bpy.types.Operator):
    bl_idname = "pose.reset_scale"
    bl_label = "Reset Scale"

    def execute(self, context):
        obj = context.active_object
        for bone in obj.pose.bones:
            if bone.bone.select:
                bone.scale = (1.0, 1.0, 1.0)
        self.report({'INFO'}, "Reset Scale to default (1, 1, 1) for selected bones")
        return {'FINISHED'}

class ResetAllOperator(bpy.types.Operator):
    bl_idname = "pose.reset_all"
    bl_label = "Reset all"

    def execute(self, context):
        obj = context.active_object
        for bone in obj.pose.bones:
            if bone.bone.select:
                bone.location = (0.0, 0.0, 0.0)
                bone.scale = (1.0, 1.0, 1.0)
                bone.rotation_euler = (0.0, 0.0, 0.0)

        self.report({'INFO'}, "Reset all transformations to default for selected bones")
        return {'FINISHED'}

#============= PANEL TRANSFORM ==============================================================

class SetTransformForSelectedBonesOperator(bpy.types.Operator):
    """Operator untuk menetapkan nilai transformasi untuk semua bone yang terseleksi"""
    bl_idname = "pose.set_transform_selected_bones"
    bl_label = "Set Transform for Selected Bones"

    transform_type: bpy.props.StringProperty()
    value: bpy.props.FloatProperty()

    def execute(self, context):
        if context.object.mode != 'POSE':
            self.report({'ERROR'}, "Harap berada di Pose Mode")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        if not selected_bones:
            self.report({'ERROR'}, "Tidak ada bone yang terseleksi")
            return {'CANCELLED'}

        for bone in selected_bones:
            if self.transform_type == 'LOCATION_X':
                bone.location.x = self.value
            elif self.transform_type == 'LOCATION_Y':
                bone.location.y = self.value
            elif self.transform_type == 'LOCATION_Z':
                bone.location.z = self.value
            elif self.transform_type == 'ROTATION_X':
                bone.rotation_euler.x = self.value
            elif self.transform_type == 'ROTATION_Y':
                bone.rotation_euler.y = self.value
            elif self.transform_type == 'ROTATION_Z':
                bone.rotation_euler.z = self.value
            elif self.transform_type == 'SCALE_X':
                bone.scale.x = self.value
            elif self.transform_type == 'SCALE_Y':
                bone.scale.y = self.value
            elif self.transform_type == 'SCALE_Z':
                bone.scale.z = self.value

        return {'FINISHED'}

class ResetLocationOperator(bpy.types.Operator):
    bl_idname = "pose.reset_location"
    bl_label = "Reset Location"

    def execute(self, context):
        if context.object.mode != 'POSE':
            self.report({'ERROR'}, "Harap berada di Pose Mode")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        if not selected_bones:
            self.report({'ERROR'}, "Tidak ada bone yang terseleksi")
            return {'CANCELLED'}

        for bone in selected_bones:
            bone.location = (0.0, 0.0, 0.0)

        self.report({'INFO'}, "Reset Location ke default (0, 0, 0)")
        return {'FINISHED'}

class ResetRotationOperator(bpy.types.Operator):
    bl_idname = "pose.reset_rotation"
    bl_label = "Reset Rotation"

    def execute(self, context):
        if context.object.mode != 'POSE':
            self.report({'ERROR'}, "Harap berada di Pose Mode")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        if not selected_bones:
            self.report({'ERROR'}, "Tidak ada bone yang terseleksi")
            return {'CANCELLED'}

        for bone in selected_bones:
            bone.rotation_euler = (0.0, 0.0, 0.0)

        self.report({'INFO'}, "Reset Rotation ke default (0, 0, 0)")
        return {'FINISHED'}

class ResetScaleOperator(bpy.types.Operator):
    bl_idname = "pose.reset_scale"
    bl_label = "Reset Scale"

    def execute(self, context):
        if context.object.mode != 'POSE':
            self.report({'ERROR'}, "Harap berada di Pose Mode")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        if not selected_bones:
            self.report({'ERROR'}, "Tidak ada bone yang terseleksi")
            return {'CANCELLED'}

        for bone in selected_bones:
            bone.scale = (1.0, 1.0, 1.0)

        self.report({'INFO'}, "Reset Scale ke default (1, 1, 1)")
        return {'FINISHED'}

class ResetAllOperator(bpy.types.Operator):
    bl_idname = "pose.reset_all"
    bl_label = "Reset All"

    def execute(self, context):
        if context.object.mode != 'POSE':
            self.report({'ERROR'}, "Harap berada di Pose Mode")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        if not selected_bones:
            self.report({'ERROR'}, "Tidak ada bone yang terseleksi")
            return {'CANCELLED'}

        for bone in selected_bones:
            bone.location = (0.0, 0.0, 0.0)
            bone.scale = (1.0, 1.0, 1.0)
            bone.rotation_euler = (0.0, 0.0, 0.0)

        self.report({'INFO'}, "Reset Semua ke default")
        return {'FINISHED'}

class ConvertRotationToEulerOperator(bpy.types.Operator):
    """Operator untuk mengubah rotasi quaternion ke Euler XYZ"""
    bl_idname = "pose.convert_quaternion_to_euler"
    bl_label = "Convert Quaternion to Euler"

    def execute(self, context):
        if context.object.mode != 'POSE':
            self.report({'ERROR'}, "Harap berada di Pose Mode")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        if not selected_bones:
            self.report({'ERROR'}, "Tidak ada bone yang terseleksi")
            return {'CANCELLED'}

        for bone in selected_bones:
            if bone.rotation_mode == 'QUATERNION':
                bone.rotation_mode = 'XYZ'

        self.report({'INFO'}, "Rotasi berhasil diubah ke Euler XYZ")
        return {'FINISHED'}

class SimpleTransformPanel(bpy.types.Panel):
    """Panel untuk mengubah transformasi bone yang terseleksi dalam Pose Mode"""
    bl_label = "Raha Transform Panel"
    bl_idname = "POSE_PT_transform_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'

    def draw(self, context):
        layout = self.layout
        if context.object.mode != 'POSE':
            layout.label(text="Harap berada di Pose Mode untuk mengedit bone.")
            return

        selected_bones = context.selected_pose_bones
        if selected_bones:
            row = layout.row(align=True)
            col = row.column()
            col.prop(selected_bones[0], "location", text="Location")

            box = layout.box()
            box.operator("pose.reset_location", text="Reset Location")

            row = layout.row(align=True)
            col = row.column()
            col.prop(selected_bones[0], "rotation_euler", text="Rotation")

            box = layout.box()
            box.operator("pose.reset_rotation", text="Reset Rotation")

            box = layout.box()
            box.operator("pose.convert_quaternion_to_euler", text="Quaternion to Euler")

            row = layout.row(align=True)
            col = row.column()
            col.prop(selected_bones[0], "scale", text="Scale")

            box = layout.box()
            box.operator("pose.reset_scale", text="Reset Scale")

            box = layout.box()
            box.operator("pose.reset_all", text="Reset ALL")

        else:
            layout.label(text="Tidak ada bone yang terseleksi.")

#================================================ TOMBOL DI GRAPH EDITOR ========================================================            
class SimpleTransformPanelGraph(bpy.types.Panel):
    """Panel untuk mengubah transformasi bone yang terseleksi dalam Pose Mode"""
    bl_label = "Raha Transform Panel"
    bl_idname = "GRAPH_PT_transform_panel"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Raha Transform Panel'

    def draw(self, context):
        layout = self.layout
        if context.object.mode != 'POSE':
            layout.label(text="Harap berada di Pose Mode untuk mengedit bone.")
            return

        selected_bones = context.selected_pose_bones
        if selected_bones:
            row = layout.row(align=True)
            col = row.column()
            col.prop(selected_bones[0], "location", text="Location")

            box = layout.box()
            box.operator("pose.reset_location", text="Reset Location")

            row = layout.row(align=True)
            col = row.column()
            col.prop(selected_bones[0], "rotation_euler", text="Rotation")

            box = layout.box()
            box.operator("pose.reset_rotation", text="Reset Rotation")

            box = layout.box()
            box.operator("pose.convert_quaternion_to_euler", text="Quaternion to Euler")

            row = layout.row(align=True)
            col = row.column()
            col.prop(selected_bones[0], "scale", text="Scale")

            box = layout.box()
            box.operator("pose.reset_scale", text="Reset Scale")

            box = layout.box()
            box.operator("pose.reset_all", text="Reset ALL")

        else:
            layout.label(text="Tidak ada bone yang terseleksi.")
            

# Registrasi

def register():
    bpy.utils.register_class(SetTransformForSelectedBonesOperator)    
    bpy.utils.register_class(SimpleTransformPanel)
    bpy.utils.register_class(SimpleTransformPanelGraph) 
       
    bpy.utils.register_class(ResetLocationOperator)    
    bpy.utils.register_class(ResetRotationOperator)  
    bpy.utils.register_class(ResetAllOperator)    
    bpy.utils.register_class(ResetScaleOperator)      
    bpy.utils.register_class(ConvertRotationToEulerOperator)         
        
    bpy.utils.register_class(TransformPanel)
    bpy.utils.register_class(ApplyLocationOperator)
    bpy.utils.register_class(ApplyRotationOperator)
    bpy.utils.register_class(ApplyScaleOperator)

    bpy.types.Scene.custom_location = bpy.props.FloatVectorProperty(
        name="Custom Location",
        default=(0.0, 0.0, 0.0),
        subtype='TRANSLATION'
    )
    bpy.types.Scene.custom_rotation = bpy.props.FloatVectorProperty(
        name="Custom Rotation",
        default=(0.0, 0.0, 0.0),
        subtype='EULER'
    )
    bpy.types.Scene.custom_scale = bpy.props.FloatVectorProperty(
        name="Custom Scale",
        default=(1.0, 1.0, 1.0),
        subtype='XYZ'
    )

    bpy.types.Scene.custom_location_axes = bpy.props.BoolVectorProperty(
        name="Location Axes",
        default=(False, False, False),
        subtype='XYZ'
    )
    bpy.types.Scene.custom_rotation_axes = bpy.props.BoolVectorProperty(
        name="Rotation Axes",
        default=(False, False, False),
        subtype='XYZ'
    )
    bpy.types.Scene.custom_scale_axes = bpy.props.BoolVectorProperty(
        name="Scale Axes",
        default=(False, False, False),
        subtype='XYZ'
    )

def unregister():
    bpy.utils.unregister_class(SetTransformForSelectedBonesOperator)    
    bpy.utils.unregister_class(SimpleTransformPanel)  
    bpy.utils.ungister_class(SimpleTransformPanelGraph)     
    bpy.utils.unregister_class(ResetLocationOperator)    
    bpy.utils.unregister_class(ResetRotationOperator)  
    bpy.utils.unregister_class(ResetAllOperator)    
    bpy.utils.unregister_class(ResetScaleOperator)      
    bpy.utils.unregister_class(ConvertRotationToEulerOperator)    
    
    bpy.utils.unregister_class(TransformPanel)
    bpy.utils.unregister_class(ApplyLocationOperator)
    bpy.utils.unregister_class(ResetLocationOperator)
    bpy.utils.unregister_class(ApplyRotationOperator)
    bpy.utils.unregister_class(ResetRotationOperator)
    bpy.utils.unregister_class(ApplyScaleOperator)
    bpy.utils.unregister_class(ResetScaleOperator)
    bpy.utils.unregister_class(ResetAllOperator)

    del bpy.types.Scene.custom_location
    del bpy.types.Scene.custom_rotation
    del bpy.types.Scene.custom_scale
    del bpy.types.Scene.custom_location_axes
    del bpy.types.Scene.custom_rotation_axes
    del bpy.types.Scene.custom_scale_axes

if __name__ == "__main__":
    register()
