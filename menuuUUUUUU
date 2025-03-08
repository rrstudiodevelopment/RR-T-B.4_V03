
import bpy
import webbrowser
from bpy.props import FloatVectorProperty


# ======================================= override_and_make_local  LINK  =================================================

def override_and_make_local(self, context):
    selected_objects = context.selected_objects
    
    if not selected_objects:
        self.report({'WARNING'}, "No objects selected")
        return {'CANCELLED'}
    
    for obj in selected_objects:
        bpy.context.view_layer.objects.active = obj  # Set active object
        bpy.ops.object.make_override_library()  # Override Library
        bpy.ops.object.make_local(type='SELECT_OBJECT')  # Make Local
    
    self.report({'INFO'}, "Overrides and Locals Applied")
    return {'FINISHED'}

#operator tombol untuk override
class OBJECT_OT_OverrideLocal(bpy.types.Operator):
    """Convert selected objects to override and make them local"""
    bl_idname = "object.override_local"
    bl_label = "Override & Make Local"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        return override_and_make_local(self, context)   
    
#=======================================================================================================================
 # CURSOR SELECTED 

class OBJECT_OT_CursorToSelected(bpy.types.Operator):
    """Move Cursor to Selected Bone (Shift+S, then 2 on numpad)"""
    bl_idname = "object.cursor_to_selected"
    bl_label = "Cursor to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.active_object and context.active_object.type == 'ARMATURE':
            bpy.ops.view3d.snap_cursor_to_selected()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Please select bones in Pose Mode!")
            return {'CANCELLED'}

class OBJECT_OT_SelectToCursor(bpy.types.Operator):
    """Move Selected Bone to Cursor (Shift+S, then 8 on numpad)"""
    bl_idname = "object.select_to_cursor"
    bl_label = "Select to Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.active_object and context.active_object.type == 'ARMATURE':
            bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Please select bones in Pose Mode!")
            return {'CANCELLED'}
# ======================================================================================================================
#                                  ALLIGN TOOLS

class OBJECT_OT_AlignTool(bpy.types.Operator):
    """Apply Copy Rotation and Location Constraints"""
    bl_idname = "pose.align_tool"
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

        # Apply constraints
        bpy.context.view_layer.update()
        bpy.ops.pose.visual_transform_apply()

        # Remove constraints
        source_bone.constraints.remove(copy_rot_constraint)
        source_bone.constraints.remove(copy_loc_constraint)

        self.report({'INFO'}, f"Applied Align Tool: {target_bone.name} to {source_bone.name}")
        return {'FINISHED'}
 #====================================================================================================================
 
 #                                      COPY ROTATE    
 
 # Operator untuk Auto Copy Rotation Constraint
class OBJECT_OT_CopyRotation(bpy.types.Operator):
    """Copy Rotation from Selected Bone to Active"""
    bl_idname = "pose.auto_copy_rotation_constraint"
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
       

#=========================================================================================================================

#=========================================================================================================================
#                       ADD CONTROLER 

# Script 1: Operator untuk menjalankan Raha Tools
class OBJECT_OT_add_controler(bpy.types.Operator):
    bl_idname = "object.add_controler"
    bl_label = "add controler"
    
    def execute(self, context):
        # Pindah ke Object Mode
        bpy.ops.object.posemode_toggle()

        # Tambahkan curve
        bpy.ops.curve.primitive_bezier_circle_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.context.object.name = "For_add_CTRL_BezierCircle"

        # Tambahkan armature dengan satu bone, pastikan location dan rotation di (0,0,0)
        bpy.ops.object.armature_add(enter_editmode=False, align='WORLD', location=(0, 0, 0))
        armature = bpy.context.object
        armature.location = (0, 0, 0)
        armature.rotation_euler = (0, 0, 0)

        # Pindah ke Edit Mode untuk mengedit bone
        bpy.ops.object.editmode_toggle()

        # Pilih bone pertama dan ubah namanya menjadi 'induk'
        armature_data = bpy.context.object.data
        first_bone = armature_data.edit_bones[0]  # Bone pertama yang ditambahkan
        first_bone.select = True
        first_bone.name = "induk"
        first_bone.head = (0, 0, 0)
        first_bone.tail = (0, 0, 1)

        # Deselect bone yang baru diberi nama
        first_bone.select = False

        # Tambahkan bone kedua (child)
        bpy.ops.armature.bone_primitive_add()

        # Pilih bone kedua dan ubah namanya menjadi 'child'
        second_bone = armature_data.edit_bones[-1]  # Bone terakhir yang ditambahkan
        second_bone.name = "child"
        second_bone.head = (0, 0, 0)
        second_bone.tail = (0, 0, 1)

        #selected child - induk lalu parent keep offset
        bpy.context.object.data.edit_bones["child"].select = True
        bpy.context.object.data.edit_bones["induk"].select = True
        bpy.ops.armature.parent_set(type='OFFSET')
        bpy.context.object.data.edit_bones["child"].select = False
        bpy.context.object.data.edit_bones["induk"].select = False

        # Pindah ke Pose Mode
        bpy.ops.object.posemode_toggle()

        #selected child
        bpy.context.object.pose.bones["child"].bone.select = True
        #ubah ke euler
        bpy.context.object.pose.bones["child"].rotation_mode = 'XYZ'
        #masukan custom display beziercircle
        bpy.context.object.pose.bones["child"].custom_shape = bpy.data.objects["For_add_CTRL_BezierCircle"]
        #rotate x nya 90 derajat
        bpy.context.object.pose.bones["child"].custom_shape_rotation_euler[0] = 1.5708
        #unselect child
        bpy.context.object.pose.bones["child"].bone.select = False

        # Selected induk
        bpy.context.object.pose.bones["induk"].bone.select = True
        #ubah ke euler
        bpy.context.object.pose.bones["induk"].rotation_mode = 'XYZ'
        #masukan custom display beziercircle
        bpy.context.object.pose.bones["induk"].custom_shape = bpy.data.objects["For_add_CTRL_BezierCircle"]
        #rotate x nya 90 derajat
        bpy.context.object.pose.bones["induk"].custom_shape_rotation_euler[0] = 1.5708
        #scale custom shape
        bpy.context.object.pose.bones["induk"].custom_shape_scale_xyz = (1.3, 1.3, 1.3)

        #balik ke object mode
        bpy.ops.object.posemode_toggle()

        #ubah nama add controler
        bpy.context.object.name = "add_ctrl_armature"

        # Nama koleksi tujuan
        collection_name = "ETC"

        # Periksa apakah koleksi sudah ada, jika tidak buat koleksi baru
        if collection_name not in bpy.data.collections:
            new_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(new_collection)
            print(f"Koleksi '{collection_name}' berhasil dibuat.")
        else:
            new_collection = bpy.data.collections[collection_name]
            print(f"Koleksi '{collection_name}' sudah ada.")

        # Pastikan ada objek aktif yang bisa dipindahkan
        active_object = bpy.context.active_object
        if active_object:
            # Hapus objek dari koleksi saat ini
            for collection in active_object.users_collection:
                collection.objects.unlink(active_object)

            # Pindahkan objek ke koleksi "ETC"
            new_collection.objects.link(active_object)
            print(f"Objek '{active_object.name}' telah dipindahkan ke koleksi '{collection_name}'.")
        else:
            print("Tidak ada objek aktif untuk dipindahkan.")

        #deselect all
        bpy.ops.object.select_all(action='DESELECT')

        # Pastikan berada di Object Mode
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect semua objek terlebih dahulu
        bpy.ops.object.select_all(action='DESELECT')

        # Loop untuk memilih objek yang namanya diawali dengan "For_add_CTRL_BezierCircle"
        for obj in bpy.data.objects:
            if obj.name.startswith("For_add_CTRL_BezierCircle") and obj.visible_get():
                obj.select_set(True)

        print("Object dengan nama awal 'For_add_CTRL_BezierCircle' berhasil dipilih.")

        #hapus curve        
        bpy.ops.object.delete()

        return {'FINISHED'}
#==========================================================================================
   
 
#=====================================================================================================================  

#  ======================================================  TOMBOL ============================================== 
class VIEW3D_PT_MiniTools(bpy.types.Panel):
    bl_label = "Raha Mini Tools"
    bl_idname = "VIEW3D_PT_mini_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'    
    bl_ui_units_x = 10

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager   
                
        layout.label(text="Tutorial")
        
#======================================================================================================        
        layout.separator()
        layout.label(text="LINK:")
        layout.operator("object.override_local", text="Make & local Ovveride", icon="LINKED")  
#======================================================================================================                    
        layout.separator()                        
        layout.label(text="Alignment Tools for Bones")
        layout.operator("object.cursor_to_selected", text="Cursor to Selected", icon="CURSOR")
        layout.operator("object.select_to_cursor", text="Select to Cursor", icon="CURSOR")
        layout.operator("pose.align_tool", text="Align Tool", icon="CON_TRANSFORM")
        layout.operator("pose.auto_copy_rotation_constraint", text="Copy Rotation", icon="CON_ROTLIKE")
        
        layout.label(text="Add-Controler")
        layout.operator("object.add_controler", text="Add-Controler", icon="BONE_DATA")        
          
#=========================================================================================================================
#                                               REGISTER     
   
# Daftar operator dan panel untuk registrasi
def register():
    
    
    bpy.utils.register_class(OBJECT_OT_OverrideLocal)
    
    bpy.utils.register_class(OBJECT_OT_CursorToSelected)
    bpy.utils.register_class(OBJECT_OT_SelectToCursor)
    bpy.utils.register_class(OBJECT_OT_AlignTool)
    bpy.utils.register_class(OBJECT_OT_CopyRotation)       
              
    bpy.utils.register_class(VIEW3D_PT_MiniTools)    
    bpy.utils.register_class(OBJECT_OT_add_controler)

    
   

        
# Fungsi untuk menghapus pendaftaran class dari Blender
def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_MiniTools)  
        
    bpy.utils.unregister_class(OBJECT_OT_OverrideLocal)        
    
    bpy.utils.unregister_class(OBJECT_OT_add_controler)        
    bpy.utils.unregister_class(OBJECT_OT_CursorToSelected)
    bpy.utils.unregister_class(OBJECT_OT_SelectToCursor)
    bpy.utils.unregister_class(OBJECT_OT_AlignTool)
  
    bpy.utils.unregister_class(OBJECT_OT_CopyRotation)        
   
    del bpy.types.Scene.capsulman_tools_rotation

if __name__ == "__main__":
    register()


#update tombol parent dan minitools dipisah
#sudah menambahkan enable bake dan clear keys