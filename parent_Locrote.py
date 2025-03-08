

import bpy
import webbrowser
from bpy.props import FloatVectorProperty

       


#===================================================== DISABLE NEW =======================================================

def get_rotation_mode(obj):
    if obj.rotation_mode in ("euler", "AXIS_ANGLE"):
        return obj.rotation_mode.lower()
    return "euler"


def get_selected_objects(context):
    if context.mode not in ("OBJECT", "POSE"):
        return

    if context.mode == "OBJECT":
        active = context.active_object
        selected = [obj for obj in context.selected_objects if obj != active]

    if context.mode == "POSE":
        active = context.active_pose_bone
        selected = [bone for bone in context.selected_pose_bones if bone != active]

    selected.append(active)
    return selected


def get_last_raha_parent_constraint(obj):
    if not obj.constraints:
        return
    const = obj.constraints[-1]
    if const.name.startswith("parent_child") and const.influence == 1:
        return const


def insert_keyframe(obj, frame):
    rotation_mode = get_rotation_mode(obj)
    data_paths = (
        "location",
        f"rotation_{rotation_mode}",
        "scale",
    )
    for data_path in data_paths:
        obj.keyframe_insert(data_path=data_path, frame=frame)


def insert_keyframe_constraint(constraint, frame):
    constraint.keyframe_insert(data_path="influence", frame=frame)


def dp_keyframe_insert_obj(obj):
    obj.keyframe_insert(data_path="location")
    if obj.rotation_mode == "QUATERNION":
        obj.keyframe_insert(data_path="rotation_quaternion")
    elif obj.rotation_mode == "AXIS_ANGLE":
        obj.keyframe_insert(data_path="rotation_axis_angle")
    else:
        obj.keyframe_insert(data_path="rotation_euler")
    obj.keyframe_insert(data_path="scale")


def dp_keyframe_insert_pbone(arm, pbone):
    arm.keyframe_insert(data_path='pose.bones["' + pbone.name + '"].location')
    if pbone.rotation_mode == "QUATERNION":
        arm.keyframe_insert(
            data_path='pose.bones["' + pbone.name + '"].rotation_quaternion'
        )
    elif pbone.rotation_mode == "AXIS_ANGLE":
        arm.keyframe_insert(
            data_path='pose.bones["' + pbone.name + '"].rotation_axis_angel'
        )
    else:
        arm.keyframe_insert(data_path='pose.bones["' + pbone.name + '"].rotation_euler')
    arm.keyframe_insert(data_path='pose.bones["' + pbone.name + '"].scale')


def dp_create_raha_parent_obj(op):
    obj = bpy.context.active_object
    scn = bpy.context.scene
    list_selected_obj = bpy.context.selected_objects

    if len(list_selected_obj) == 2:
        i = list_selected_obj.index(obj)
        list_selected_obj.pop(i)
        parent_obj = list_selected_obj[0]

        dp_keyframe_insert_obj(obj)
        bpy.ops.object.constraint_add_with_targets(type="CHILD_OF")
        last_constraint = obj.constraints[-1]

        if parent_obj.type == "ARMATURE":
            last_constraint.subtarget = parent_obj.data.bones.active.name
            last_constraint.name = (
                "parent_child" + last_constraint.target.name + "." + last_constraint.subtarget
            )
        else:
            last_constraint.name = "parent_child" + last_constraint.target.name

        C = bpy.context.copy()
        C["constraint"] = last_constraint
        bpy.ops.constraint.childof_set_inverse(
            constraint=last_constraint.name, owner="OBJECT"
        )

        current_frame = scn.frame_current
        scn.frame_current = current_frame - 1
        obj.constraints[last_constraint.name].influence = 0
        obj.keyframe_insert(
            data_path='constraints["' + last_constraint.name + '"].influence'
        )

        scn.frame_current = current_frame
        obj.constraints[last_constraint.name].influence = 1
        obj.keyframe_insert(
            data_path='constraints["' + last_constraint.name + '"].influence'
        )

        for ob in list_selected_obj:
            ob.select_set(False)

        obj.select_set(True)
    else:
        op.report({"ERROR"}, "Two objects must be selected")


def dp_create_raha_parent_pbone(op):
    arm = bpy.context.active_object
    pbone = bpy.context.active_pose_bone
    scn = bpy.context.scene
    list_selected_obj = bpy.context.selected_objects

    if len(list_selected_obj) == 2 or len(list_selected_obj) == 1:
        if len(list_selected_obj) == 2:
            i = list_selected_obj.index(arm)
            list_selected_obj.pop(i)
            parent_obj = list_selected_obj[0]
            if parent_obj.type == "ARMATURE":
                parent_obj_pbone = parent_obj.data.bones.active
                if not parent_obj_pbone.select:
                    op.report({"ERROR"}, "At least two bones must be selected")
                    return
        else:
            parent_obj = arm
            selected_bones = bpy.context.selected_pose_bones
            selected_bones.remove(pbone)
            if not selected_bones:
                op.report({"ERROR"}, "At least two bones must be selected")
                return
            parent_obj_pbone = selected_bones[0]

        dp_keyframe_insert_pbone(arm, pbone)
        bpy.ops.pose.constraint_add_with_targets(type="CHILD_OF")
        last_constraint = pbone.constraints[-1]

        if parent_obj.type == "ARMATURE":
            last_constraint.subtarget = parent_obj_pbone.name
            last_constraint.name = (
                "parent_child" + last_constraint.target.name + "." + last_constraint.subtarget
            )
        else:
            last_constraint.name = "parent_child" + last_constraint.target.name

        C = bpy.context.copy()
        C["constraint"] = last_constraint
        bpy.ops.constraint.childof_set_inverse(
            constraint=last_constraint.name, owner="BONE"
        )

        current_frame = scn.frame_current
        scn.frame_current = current_frame - 1
        pbone.constraints[last_constraint.name].influence = 0
        arm.keyframe_insert(
            data_path='pose.bones["'
            + pbone.name
            + '"].constraints["'
            + last_constraint.name
            + '"].influence'
        )

        scn.frame_current = current_frame
        pbone.constraints[last_constraint.name].influence = 1
        arm.keyframe_insert(
            data_path='pose.bones["'
            + pbone.name
            + '"].constraints["'
            + last_constraint.name
            + '"].influence'
        )
    else:
        op.report({"ERROR"}, "Two objects must be selected")

def dp_clear(obj, pbone):
    dp_curves = []
    dp_keys = []
    for fcurve in obj.animation_data.action.fcurves:
        if "constraints" in fcurve.data_path and "parent_child" in fcurve.data_path:
            dp_curves.append(fcurve)

    for f in dp_curves:
        for key in f.keyframe_points:
            dp_keys.append(key.co[0])

    dp_keys = list(set(dp_keys))
    dp_keys.sort()

    for fcurve in obj.animation_data.action.fcurves[:]:
        if fcurve.data_path.startswith("constraints") and "parent_child" in fcurve.data_path:
            obj.animation_data.action.fcurves.remove(fcurve)
        else:
            for frame in dp_keys:
                for key in fcurve.keyframe_points[:]:
                    if key.co[0] == frame:
                        fcurve.keyframe_points.remove(key)
            if not fcurve.keyframe_points:
                obj.animation_data.action.fcurves.remove(fcurve)



#======================================================= DISABLE ================================================

def disable_constraint(obj, const, frame):
    if isinstance(obj, bpy.types.PoseBone):
        matrix_final = obj.matrix
    else:
        matrix_final = obj.matrix_world

    insert_keyframe(obj, frame=frame - 1)
    insert_keyframe_constraint(const, frame=frame - 1)

    const.influence = 0
    if isinstance(obj, bpy.types.PoseBone):
        obj.matrix = matrix_final
    else:
        obj.matrix_world = matrix_final

    insert_keyframe(obj, frame=frame)
    insert_keyframe_constraint(const, frame=frame)
    return

class raha_parent_OT_disable(bpy.types.Operator):
    """Disable the current animated Child Of constraint"""

    bl_idname = "raha_parent.disable"
    bl_label = "Disable Constraint"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode in ("OBJECT", "POSE")

    def execute(self, context):
        frame = context.scene.frame_current
        objects = get_selected_objects(context)
        counter = 0

        if not objects:
            self.report({"ERROR"}, "Nothing selected.")
            return {"CANCELLED"}

        for obj in objects:
            const = get_last_raha_parent_constraint(obj)
            if const is None:
                continue
            disable_constraint(obj, const, frame)
            counter += 1

        self.report({"INFO"}, f"{counter} constraints were disabled.")
        return {"FINISHED"}
    
#============================================================================================================================

#                          DEF   CONSTRAINT
# Fungsi untuk mendapatkan constraint 'Copy Rotation' dan 'Copy Location'
def get_copy_constraints(bone):
    copy_rot = None
    copy_loc = None
    for constraint in bone.constraints:
        if constraint.type == 'COPY_ROTATION' and constraint.name.startswith("CopasRot"):
            copy_rot = constraint
        if constraint.type == 'COPY_LOCATION' and constraint.name.startswith("CopasPos"):
            copy_loc = constraint
    return copy_rot, copy_loc

# Fungsi untuk mendapatkan constraint 'Copy Rotation' dengan awalan 'CopasRot'
def get_copy_rotation_constraint(bone):
    for constraint in bone.constraints:
        if constraint.type == 'COPY_ROTATION' and constraint.name.startswith("CopasRot"):
            return constraint
    return None

# Fungsi untuk mendapatkan constraint 'Copy Location' dengan awalan 'CopasPos'
def get_copy_location_constraint(bone):
    for constraint in bone.constraints:
        if constraint.type == 'COPY_LOCATION' and constraint.name.startswith("CopasPos"):
            return constraint
    return None


#============================================================================================================

#           Apply Constraint Copy Rotation dan Copy Location

# Operator untuk Apply Constraint Copy Rotation dan Copy Location
class ApplyCopyConstraints(bpy.types.Operator):
    bl_idname = "object.apply_copyconstraints"
    bl_label = "Apply Copy Rotation and Location"
    
    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        if obj and obj.pose:
            for bone in obj.pose.bones:
                if bone.bone.select:
                    constraint_rot = get_copy_rotation_constraint(bone)
                    constraint_loc = get_copy_location_constraint(bone)
                    
                    if constraint_rot:
                        # Apply Copy Rotation constraint
                        bpy.ops.object.mode_set(mode='POSE')  # Memastikan dalam mode POSE
                        bpy.ops.constraint.apply(constraint=constraint_rot.name, owner='BONE')
                        insert_keyframe_constraint(constraint_rot, frame)  # Insert keyframe untuk influence

                    if constraint_loc:
                        # Apply Copy Location constraint
                        bpy.ops.object.mode_set(mode='POSE')  # Memastikan dalam mode POSE
                        bpy.ops.constraint.apply(constraint=constraint_loc.name, owner='BONE')
                        insert_keyframe_constraint(constraint_loc, frame)  # Insert keyframe untuk influence
        return {'FINISHED'}

#================================================= Operator untuk Delete Constraint Copy Rotation dan Copy Location
class DeleteCopyConstraints(bpy.types.Operator):
    bl_idname = "object.delete_copyconstraints"
    bl_label = "Delete Copy Rotation and Location"
    
    def execute(self, context):
        obj = context.object
        if obj and obj.pose:
            for bone in obj.pose.bones:
                if bone.bone.select:
                    constraint_rot = get_copy_rotation_constraint(bone)
                    constraint_loc = get_copy_location_constraint(bone)
                    
                    if constraint_rot:
                        bpy.ops.object.mode_set(mode='POSE')  # Memastikan dalam mode POSE
                        bpy.ops.constraint.delete(constraint=constraint_rot.name, owner='BONE')
                    
                    if constraint_loc:
                        bpy.ops.object.mode_set(mode='POSE')  # Memastikan dalam mode POSE
                        bpy.ops.constraint.delete(constraint=constraint_loc.name, owner='BONE')
        return {'FINISHED'}

#========================================= Operator untuk Disable Constraint Copy Rotation dan Copy Location
class DisableCopyConstraints(bpy.types.Operator):
    bl_idname = "object.disable_copyconstraints"
    bl_label = "Disable Copy Rotation and Location"
    
    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        if obj and obj.pose:
            for bone in obj.pose.bones:
                if bone.bone.select:
                    constraint_rot = get_copy_rotation_constraint(bone)
                    constraint_loc = get_copy_location_constraint(bone)
                    
                    if constraint_rot:
                        disable_constraint(bone, constraint_rot, frame)
                    
                    if constraint_loc:
                        disable_constraint(bone, constraint_loc, frame)
        return {'FINISHED'}

#=========================================================================================================================  
       
#========================================================================================================================

#                 CREATE   PARENT LOC ROTATE

class PARENT_LOCROTE(bpy.types.Operator):
    """Apply Copy Rotation and Location Constraints"""
    bl_idname = "pose.parent_locrote"
    bl_label = "Align Tool"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'WARNING'}, "Please switch to Pose Mode!")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        active_bone = context.active_pose_bone

        if len(selected_bones) < 2 or active_bone is None:
            self.report({'WARNING'}, "Please select at least 2 bones and ensure one is active!")
            return {'CANCELLED'}

        target_bone = active_bone
        source_bone = next((bone for bone in selected_bones if bone != target_bone), None)

        if not source_bone:
            self.report({'ERROR'}, "Unable to determine the source bone!")
            return {'CANCELLED'}

        # Add Copy Rotation and Copy Location Constraints
        copy_rot_constraint = source_bone.constraints.new(type='COPY_ROTATION')
        copy_rot_constraint.name = "CopasRot"
        copy_rot_constraint.target = context.object
        copy_rot_constraint.subtarget = target_bone.name

        copy_loc_constraint = source_bone.constraints.new(type='COPY_LOCATION')
        copy_loc_constraint.name = "CopasPos"
        copy_loc_constraint.target = context.object
        copy_loc_constraint.subtarget = target_bone.name       
        
        self.report({'INFO'}, f"Applied Align Tool: {target_bone.name} to {source_bone.name}")
        return {'FINISHED'}
    
#=====================================================================================================================

#                   SLIDE INFLUENCE    Copy location dan rotation
    
# Fungsi untuk memperbarui influence kedua constraint
def update_constraints_influence(self, context):
    bone = self
    constraint_rot = next((c for c in bone.constraints if c.type == 'COPY_ROTATION' and c.name.startswith("CopasRot")), None)
    constraint_loc = next((c for c in bone.constraints if c.type == 'COPY_LOCATION' and c.name.startswith("CopasPos")), None)
    
    if constraint_rot:
        constraint_rot.influence = bone.copy_constraints_influence
        constraint_rot.keyframe_insert("influence", frame=bpy.context.scene.frame_current)
    
    if constraint_loc:
        constraint_loc.influence = bone.copy_constraints_influence
        constraint_loc.keyframe_insert("influence", frame=bpy.context.scene.frame_current)

# Pastikan property di bone sudah ada agar bisa diubah di UI
bpy.types.PoseBone.copy_constraints_influence = bpy.props.FloatProperty(
    name="Constraints Influence",
    default=1.0,
    min=0.0,
    max=1.0,
    update=update_constraints_influence
)


#========================================================================================================================

#                                           APPLY CONSTRAINT ROtation


 # Operator untuk Apply constraint
class APPLY_CONSTRAINT (bpy.types.Operator):
    """Copy Rotation from Selected Bone to Active"""
    bl_idname = "pose.apply_constraint"
    bl_label = "Auto Copy Rotation Constraint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Ensure the operator is run in Pose Mode with at least two bones selected
        if not context.mode == 'POSE':
            self.report({'WARNING'}, "Please switch to Pose Mode!")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        active_bone = context.active_pose_bone

        if len(selected_bones) < 2 or active_bone is None:
            self.report({'WARNING'}, "Please select at least 2 bones and ensure one is active!")
            return {'CANCELLED'}

        # Active bone as target (second selected bone)
        target_bone = active_bone

        # Determine the source bone (the other bone in the selection)
        source_bone = next((bone for bone in selected_bones if bone != target_bone), None)

        if not source_bone:
            self.report({'ERROR'}, "Unable to determine the source bone!")
            return {'CANCELLED'}

        # Add a Copy Rotation Constraint to the source bone
        constraint = source_bone.constraints.new(type='COPY_ROTATION')
        constraint.name = "CopasRot"
        constraint.target = context.object  # Armature object
        constraint.subtarget = target_bone.name  # Set target to the active bone

        # Update the scene to ensure constraints are applied correctly
        bpy.context.view_layer.update()

        # Apply the constraint (Ctrl + A equivalent in Blender for pose transforms)
        bpy.ops.pose.visual_transform_apply()

        # Remove the constraint after applying (to bake the transformation)
        source_bone.constraints.remove(constraint)

        self.report({'INFO'}, f"Copy Rotation Constraint applied from {target_bone.name} to {source_bone.name}.")
        return {'FINISHED'}
 
 
       
   
#  ======================================================  TOMBOL PARENT ==============================================  
    
class VIEW3D_PT_Raha_Parents_Locrote(bpy.types.Panel):
    bl_label = "Raha Parent Tools"
    bl_idname = "VIEW3D_PT_Raha_Parents_Locrote"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'    
    bl_ui_units_x = 10 

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager   

        layout.separator()
        layout.label(text="Parent locrote")
        layout.operator("pose.parent_locrote", text="Parent_locrote", icon="CON_TRANSFORM") 
        row = layout.row()
        row.operator("object.apply_copyconstraints", text="Apply Copy Rotation and Location")
        row.operator("object.delete_copyconstraints", text="Delete Copy Rotation and Location")
        layout.operator("object.disable_copyconstraints", text="Disable Copy Rotation and Location")                   
          
#========================================================================================================================  
                    
#influence LOCROTAE
        obj = context.object
        if obj and obj.pose:
            for bone in obj.pose.bones:
                if bone.bone.select:
                    # Mendapatkan constraint Copy Rotation dan Copy Location
                    constraint_rot, constraint_loc = get_copy_constraints(bone)

                    if constraint_rot or constraint_loc:
                        # Menambahkan kontrol bersama untuk influence
                        row = layout.row()
                        row.prop(bone, "copy_constraints_influence", slider=True, text=" LOCROTE")

                        # Set influence untuk kedua constraint sekaligus
                        if constraint_rot:
                            constraint_rot.influence = bone.copy_constraints_influence
                        if constraint_loc:
                            constraint_loc.influence = bone.copy_constraints_influence
        
#=========================================================================================================================

#                                               REGISTER     
   
# Daftar operator dan panel untuk registrasi
def register():
    bpy.types.PoseBone.copy_constraints_influence = bpy.props.FloatProperty(
        name="Copy Constraints Influence",
        description="Control the influence of both Copy Location and Copy Rotation constraints",
        default=1.0,
        min=0.0,
        max=1.0,
        update=update_constraints_influence
    
    )                
    bpy.utils.register_class(ApplyCopyConstraints)
    bpy.utils.register_class(DeleteCopyConstraints)
    bpy.utils.register_class(DisableCopyConstraints)
    bpy.utils.register_class(PARENT_LOCROTE)
    bpy.utils.register_class(VIEW3D_PT_Raha_Parents_Locrote)
        
    bpy.utils.register_class(raha_parent_OT_disable)  
        

        
# Fungsi untuk menghapus pendaftaran class dari Blender
def unregister():
    bpy.utils.unregister_class(ApplyCopyConstraints)
    bpy.utils.unregister_class(DeleteCopyConstraints)
    bpy.utils.unregister_class(DisableCopyConstraints)
    bpy.utils.unregister_class(PARENT_LOCROTE) 
    bpy.utils.unregister_class(VIEW3D_PT_Raha_Parents_Locrote) 
        
    bpy.utils.register_class(raha_parent_OT_disable)  

    
   

    
    
    del bpy.types.Scene.capsulman_tools_rotation

if __name__ == "__main__":
    register()


#update tombol parent dan minitools dipisah
#sudah menambahkan enable bake dan clear keys