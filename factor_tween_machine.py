

import bpy


def apply_pose_breakdowner(context, factor):
    obj = context.object
    if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
        for bone in context.selected_pose_bones:
            action = obj.animation_data.action
            if action:
                fcurves = action.fcurves
                for fcurve in fcurves:
                    if fcurve.data_path.startswith(f'pose.bones["{bone.name}"]'):
                        prev_key, next_key = None, None
                        for keyframe in fcurve.keyframe_points:
                            if keyframe.co[0] < context.scene.frame_current:
                                prev_key = keyframe
                            elif keyframe.co[0] > context.scene.frame_current:
                                next_key = keyframe
                                break

                        if prev_key and next_key:
                            prev_value = prev_key.co[1]
                            next_value = next_key.co[1]
                            new_value = (1 - factor) * prev_value + factor * next_value
                            fcurve.keyframe_points.insert(context.scene.frame_current, new_value, options={'FAST'})
                            fcurve.update()


class ApplyPoseBreakdownerOperator(bpy.types.Operator):
    """Apply Pose Breakdowner"""
    bl_idname = "pose.apply_breakdowner"
    bl_label = "Apply Breakdowner"

    def execute(self, context):
        factor = context.scene.pose_breakdowner_factor
        apply_pose_breakdowner(context, factor)
        return {'FINISHED'}


def register():
    bpy.types.Scene.pose_breakdowner_factor = bpy.props.FloatProperty(
        name="Pose Breakdowner Factor",
        description="Factor for interpolating poses",
        default=0.5,
        min=0.0,
        max=1.0,
        update=lambda self, context: bpy.ops.pose.apply_breakdowner()  # Otomatis terupdate
    )


    bpy.utils.register_class(ApplyPoseBreakdownerOperator)


def unregister():
    del bpy.types.Scene.pose_breakdowner_factor
    bpy.utils.unregister_class(PoseBreakdownerPanel)
    bpy.utils.unregister_class(ApplyPoseBreakdownerOperator)


if __name__ == "__main__":
    register()
