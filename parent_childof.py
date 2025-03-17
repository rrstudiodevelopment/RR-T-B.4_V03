

import bpy
import webbrowser
from bpy.props import FloatVectorProperty

#========================================= ENABLE =============================================================
def get_previous_keyframe(bone, current_frame):
    """
    Mencari keyframe sebelumnya dari tulang (bone) yang sedang dipilih.
    """
    keyframes = [int(kp.co.x) for fcurve in bpy.context.object.animation_data.action.fcurves 
                 if fcurve.data_path.startswith(f'pose.bones["{bone.name}"].')
                 for kp in fcurve.keyframe_points]
    keyframes = sorted(set(keyframes))
    prev_key = max([kf for kf in keyframes if kf < current_frame], default=None)
    return prev_key

def copy_paste_keyframes():
    """
    Menyalin keyframe dari frame sebelumnya dan menempelkannya ke frame berikutnya.
    Termasuk lokasi, rotasi (Euler dan Quaternion), serta nilai influence dari constraint "parent_child".
    """
    obj = bpy.context.object
    bone = bpy.context.active_pose_bone
    current_frame = int(bpy.context.scene.frame_current)
    
    if not obj or not bone:
        return
    
    # Periksa apakah objek memiliki data animasi
    anim_data = obj.animation_data
    if not anim_data or not anim_data.action:
        return
    
    # Cari keyframe sebelumnya
    prev_keyframe = get_previous_keyframe(bone, current_frame)
    if prev_keyframe is None:
        return
    
    prev_frame = int(prev_keyframe - 1)
    
    # Set keyframe di frame sekarang
    bpy.context.scene.frame_set(current_frame)
    bone.keyframe_insert(data_path="location")
    bone.keyframe_insert(data_path="rotation_quaternion")
    bone.keyframe_insert(data_path="rotation_euler")
    
    # Simpan nilai influence dari semua constraint yang sesuai
    influence_values = {constraint.name: constraint.influence for constraint in bone.constraints if constraint.name.startswith("parent_child")}
    for constraint in bone.constraints:
        if constraint.name.startswith("parent_child"):
            constraint.influence = 0  # Paksa nilai influence menjadi 1
            constraint.keyframe_insert(data_path="influence")

    # Copy keyframe dari prev_frame
    bpy.context.scene.frame_set(prev_frame)
    loc = bone.location.copy()
    rot_euler = bone.rotation_euler.copy()
    rot_quat = bone.rotation_quaternion.copy()
    
    # Paste keyframe di frame +1
    bpy.context.scene.frame_set(current_frame + 1)
    bone.location = loc
    bone.rotation_euler = rot_euler
    bone.rotation_quaternion = rot_quat
    
    # Set influence menjadi 1 sebelum menyisipkan keyframe
    for constraint in bone.constraints:
        if constraint.name.startswith("parent_child"):
            constraint.influence = 1  # Paksa nilai influence menjadi 1
            constraint.keyframe_insert(data_path="influence")
    
    # Masukkan keyframe untuk transformasi bone
    bone.keyframe_insert(data_path="location")
    bone.keyframe_insert(data_path="rotation_quaternion")
    bone.keyframe_insert(data_path="rotation_euler")

class OBJECT_OT_ENABLE(bpy.types.Operator):
    """
    Operator Blender untuk menyalin keyframe dari frame sebelumnya
    dan menempelkannya ke frame berikutnya.
    """
    bl_idname = "object.enable"
    bl_label = "enable-child-off"
    bl_description = "Copy keyframe from previous frame and paste it to the next frame"
    
    def execute(self, context):
        copy_paste_keyframes()
        return {'FINISHED'}


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


#============================================================== CREATE ===============================================

class raha_parent_OT_create(bpy.types.Operator):
    """Create a new animated Child Of constraint"""

    bl_idname = "raha_parent.create"
    bl_label = "Create Constraint"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        frame = context.scene.frame_current

        if obj.type == "ARMATURE":
            if obj.mode != "POSE":
                self.report({"ERROR"}, "Armature objects must be in Pose mode.")
                return {"CANCELLED"}
            obj = bpy.context.active_pose_bone
            const = get_last_raha_parent_constraint(obj)
            if const:
                disable_constraint(obj, const, frame)
            dp_create_raha_parent_pbone(self)
        else:
            const = get_last_raha_parent_constraint(obj)
            if const:
                disable_constraint(obj, const, frame)
            dp_create_raha_parent_obj(self)

        return {"FINISHED"}
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
#====================================================== CLEAR ========================================================

class raha_parent_OT_clear(bpy.types.Operator):
    """Clear Raha Parent constraints"""

    bl_idname = "raha_parent.clear"
    bl_label = "Clear Raha Parent"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        pbone = None
        obj = bpy.context.active_object
        if obj.type == "ARMATURE":
            pbone = bpy.context.active_pose_bone

        dp_clear(obj, pbone)

        return {"FINISHED"}

#========================================================= BAKE ==========================================================
class raha_parent_OT_bake(bpy.types.Operator):
    """Bake Raha Parent animation"""

    bl_idname = "raha_parent.bake"
    bl_label = "Bake Raha Parent"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = bpy.context.active_object
        scn = bpy.context.scene

        if obj.type == "ARMATURE":
            obj = bpy.context.active_pose_bone
            bpy.ops.nla.bake(
                frame_start=scn.frame_start,
                frame_end=scn.frame_end,
                step=1,
                only_selected=True,
                visual_keying=True,
                clear_constraints=False,
                clear_parents=False,
                bake_types={"POSE"},
            )
            for const in obj.constraints[:]:
                if const.name.startswith("parent_child"):
                    obj.constraints.remove(const)
        else:
            bpy.ops.nla.bake(
                frame_start=scn.frame_start,
                frame_end=scn.frame_end,
                step=1,
                only_selected=True,
                visual_keying=True,
                clear_constraints=False,
                clear_parents=False,
                bake_types={"OBJECT"},
            )
            for const in obj.constraints[:]:
                if const.name.startswith("parent_child"):
                    obj.constraints.remove(const)

        return {"FINISHED"}
    
#============================================================================================================================
#============================================================================================================
#================================ CHILD OFF ===========================================


# Fungsi untuk mendapatkan constraint 'Child Of' dengan awalan 'parent_child'
def get_childof_constraint(bone):
    for constraint in bone.constraints:
        if constraint.type == 'CHILD_OF' and constraint.name.startswith("parent_child"):
            return constraint
    return None

# Fungsi untuk menyisipkan keyframe ke objek
def insert_keyframe(obj, frame):
    obj.keyframe_insert("location", frame=frame)
    obj.keyframe_insert("rotation_quaternion", frame=frame)
    obj.keyframe_insert("scale", frame=frame)

# Fungsi untuk menyisipkan keyframe ke constraint
def insert_keyframe_constraint(const, frame):
    const.keyframe_insert("influence", frame=frame)

# Fungsi untuk menonaktifkan constraint Child-Of
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
    bpy.context.view_layer.update()  # Memastikan Blender memperbarui matriks
    return

# Operator untuk Apply Constraint Child-Of
class ApplyChildOfConstraint(bpy.types.Operator):
    bl_idname = "object.apply_childof"
    bl_label = "Apply Child-Of"
    
    def execute(self, context):
        obj = context.object
        if obj and obj.pose:
            for bone in obj.pose.bones:
                if bone.bone.select:
                    constraint = get_childof_constraint(bone)
                    if constraint:
                        bpy.ops.object.mode_set(mode='POSE')  # Memastikan dalam mode POSE
                        bpy.ops.constraint.apply(constraint=constraint.name, owner='BONE')
        return {'FINISHED'}

# Operator untuk Set Inverse Constraint Child-Of
class SetInverseChildOfConstraint(bpy.types.Operator):
    bl_idname = "object.set_inverse_childof"
    bl_label = "Set Inverse Child-Of"
    
    def execute(self, context):
        obj = context.object
        if obj and obj.pose:
            for bone in obj.pose.bones:
                if bone.bone.select:
                    constraint = get_childof_constraint(bone)
                    if constraint:
                        bpy.ops.object.mode_set(mode='POSE')  # Memastikan dalam mode POSE
                        bpy.ops.constraint.childof_set_inverse(constraint=constraint.name, owner='BONE')
        return {'FINISHED'}

# Operator untuk Menghapus Constraint Child-Of
class DeleteChildOfConstraint(bpy.types.Operator):
    bl_idname = "object.delete_childof"
    bl_label = "Delete Child-Of"
    
    def execute(self, context):
        obj = context.object
        if obj and obj.pose:
            for bone in obj.pose.bones:
                if bone.bone.select:
                    constraint = get_childof_constraint(bone)
                    if constraint:
                        bpy.ops.object.mode_set(mode='POSE')  # Memastikan dalam mode POSE
                        bpy.ops.constraint.delete(constraint=constraint.name, owner='BONE')
        return {'FINISHED'}

# Operator untuk Menonaktifkan Constraint Child-Of
class DisableChildOfConstraint(bpy.types.Operator):
    bl_idname = "object.disable_childof"
    bl_label = "Disable Child-Of"
    
    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        if obj and obj.pose:
            for bone in obj.pose.bones:
                if bone.bone.select:
                    constraint = get_childof_constraint(bone)
                    if constraint:
                        disable_constraint(bone, constraint, frame)
        return {'FINISHED'}

#=======================================================================================================================

#       CREATE PARENT CHILD OFF

# Operator untuk child off 
class PARENT_CHILDOFF(bpy.types.Operator):
    """Copy Rotation from Selected Bone to Active"""
    bl_idname = "pose.parent_child_off"
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
        constraint = source_bone.constraints.new(type='CHILD_OF') 
        constraint.name = "parent_child"
        constraint.target = context.object  # Armature object
        constraint.subtarget = target_bone.name  # Set target to the active bone

        # Update the scene to ensure constraints are applied correctly
        bpy.context.view_layer.update()

        self.report({'INFO'}, f"parent_child_off applied from {target_bone.name} to {source_bone.name}.")
        return {'FINISHED'}
#=====================================================================================================================

#                   SLIDE INFLUENCE    
    
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

#                                           APPLY CONSTRAINT 


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

 
#=====================================================================================================================  
  
#  ======================================================  TOMBOL PARENT ==============================================  
    
class VIEW3D_PT_Raha_Parents(bpy.types.Panel):
    bl_label = "Raha Parent Tools"
    bl_idname = "VIEW3D_PT_Raha_Parents"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'    
    bl_ui_units_x = 10

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager                                          
                          
#pisah tombol khusus child-off  
        layout.separator()  
        layout.label(text="Parent Child off")                                     
        layout.operator("pose.parent_child_off", text="Parent_Child_off") 
        row = layout.row()        
        row.operator("object.apply_childof", text="Apply Child-Of")
        row.operator("object.delete_childof", text="Delete Child-Of")
        layout.operator("object.set_inverse_childof", text="Set Inverse")
        row = layout.row()        
        row.operator("object.enable", text="Enable")        
        row.operator("raha_parent.disable", text="Disable")
        row = layout.row()         
        row.operator("raha_parent.clear", text="Clear Keys")                     
          
#========================================================================================================================

#                                                   SLIDE INFLUENCE   
      
#influence Childof:       
        obj = context.object
        if obj and obj.pose:
            for bone in obj.pose.bones:
                if bone.bone.select:
                    constraints = [constraint for constraint in bone.constraints if constraint.type == 'CHILD_OF' and constraint.name.startswith("parent_child")]
                    for constraint in constraints:
                        # Menampilkan 'influence' untuk setiap 'Child-Of'
                        row = layout.row()
                        row.label(text=f"Parent {constraint.subtarget})")
                        row.prop(constraint, "influence", text="inf")                              
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

    bpy.utils.register_class(VIEW3D_PT_Raha_Parents)
    bpy.utils.register_class(PARENT_CHILDOFF)     
    bpy.utils.register_class(ApplyChildOfConstraint)
    bpy.utils.register_class(SetInverseChildOfConstraint)
    bpy.utils.register_class(DeleteChildOfConstraint)
    bpy.utils.register_class(DisableChildOfConstraint)
    bpy.utils.register_class(OBJECT_OT_ENABLE)   
        
    bpy.utils.register_class(raha_parent_OT_create)  
    bpy.utils.register_class(raha_parent_OT_disable)  
    bpy.utils.register_class(raha_parent_OT_clear)  
    bpy.utils.register_class(raha_parent_OT_bake)           


    
        
# Fungsi untuk menghapus pendaftaran class dari Blender
def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_Raha_Parents)    
    bpy.utils.unregister_class(PARENT_CHILDOFF)     
    bpy.utils.unregister_class(VIEW3D_PT_Raha_Parents)
    bpy.utils.unregister_class(ApplyChildOfConstraint)
    bpy.utils.unregister_class(SetInverseChildOfConstraint)
    bpy.utils.unregister_class(DeleteChildOfConstraint)
    bpy.utils.unregister_class(DisableChildOfConstraint)
    bpy.utils.unregister_class(OBJECT_OT_ENABLE)   
        
    bpy.utils.unregister_class(raha_parent_OT_create)  
    bpy.utils.unregister_class(raha_parent_OT_disable)  
    bpy.utils.unregister_class(raha_parent_OT_clear)  
    bpy.utils.unregister_class(raha_parent_OT_bake)             


if __name__ == "__main__":
    register()


