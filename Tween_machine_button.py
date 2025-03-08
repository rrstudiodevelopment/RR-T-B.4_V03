

import bpy

# Operator untuk menjalankan pose breakdown dengan faktor tertentu
class PoseBreakdownOperator(bpy.types.Operator):
    bl_idname = "pose.breakdown_custom"
    bl_label = "Run Pose Breakdown"

    factor: bpy.props.FloatProperty(default=0.0)

    def execute(self, context):
        current_frame = context.scene.frame_current
        obj = context.active_object

        if obj and obj.type == 'ARMATURE':
            action = obj.animation_data.action
            if action is None:
                self.report({'WARNING'}, "No animation data found.")
                return {'CANCELLED'}

            keyframes = [kp.co.x for fcurve in action.fcurves for kp in fcurve.keyframe_points]
            keyframes = sorted(set(keyframes))

            prev_frame = max([k for k in keyframes if k <= current_frame], default=None)
            next_frame = min([k for k in keyframes if k > current_frame], default=None)

            if prev_frame is None or next_frame is None:
                self.report({'WARNING'}, "No valid keyframes found around the current frame.")
                return {'CANCELLED'}

            bpy.ops.pose.breakdown(factor=self.factor, prev_frame=int(prev_frame), next_frame=int(next_frame))

        return {'FINISHED'}


# Fungsi Registrasi
classes = [
    PoseBreakdownOperator,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
