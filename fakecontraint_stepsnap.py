

import bpy
import json
import mathutils


stored_matrices = {}

# Operator untuk Smart Bake
class RahaSmartBake(bpy.types.Operator):
    """Melakukan proses smart bake dari start frame hingga end frame untuk semua bone yang dipilih"""
    bl_idname = "object.smart_bake"
    bl_label = "Smart Bake"
    
    def execute(self, context):
        obj = context.object
        scene = context.scene
        start_frame = scene.start_frame
        end_frame = scene.end_frame
        
        # Ambil status checkbox
        bake_location = scene.bake_location
        bake_rotation = scene.bake_rotation
        bake_scale = scene.bake_scale
        bake_custom_props = scene.bake_custom_props
        
        if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
            selected_bones = context.selected_pose_bones  # Ambil semua bone yang dipilih
            if selected_bones:
                # Jika Bake Scale tidak dicentang, nonaktifkan use_scale pada semua constraint Child Of
                if not bake_scale:
                    for bone in selected_bones:
                        for constraint in bone.constraints:
                            if constraint.type == 'CHILD_OF':  # Cek jika constraint adalah Child Of
                                constraint.use_scale_x = False
                                constraint.use_scale_y = False
                                constraint.use_scale_z = False
                                self.report({'INFO'}, f"Nonaktifkan scale pada constraint {constraint.name} di bone {bone.name}.")

                for bone in selected_bones:  # Iterasi pada setiap bone yang dipilih
                    for frame in range(start_frame, end_frame + 1):
                        # Set frame saat ini
                        scene.frame_set(frame)
                        
                        # Simpan matrix beserta scale
                        matrix = obj.matrix_world @ bone.matrix
                        location, rotation, scale = matrix.decompose()  # Dekomposisi matriks
                        stored_matrices[bone.name] = {
                            "matrix": [list(row) for row in matrix],
                            "location": list(location),
                            "rotation": list(rotation),
                            "scale": list(scale)  # Simpan scale
                        }
                        
                        # Maju 1 frame
                        scene.frame_set(frame + 1)
                        
                        # Insert keyframe berdasarkan opsi yang dipilih
                        if bake_location:
                            bone.keyframe_insert(data_path="location", index=-1)
                        if bake_rotation:
                            bone.keyframe_insert(data_path="rotation_quaternion", index=-1)
                            bone.keyframe_insert(data_path="rotation_euler", index=-1)
                        if bake_scale:
                            bone.keyframe_insert(data_path="scale", index=-1)
                        if bake_custom_props:
                            for prop in bone.keys():  
                                if prop not in "_RNA_UI":  # Hindari properti internal Blender
                                    bone.keyframe_insert(data_path=f'["{prop}"]')
                        
                        # Mundur 1 frame
                        scene.frame_set(frame)
                        
                        # Apply matrix beserta scale
                        matrix_data = stored_matrices[bone.name]["matrix"]
                        location_data = stored_matrices[bone.name]["location"]
                        rotation_data = stored_matrices[bone.name]["rotation"]
                        scale_data = stored_matrices[bone.name]["scale"]
                        
                        # Buat matriks baru dengan lokasi, rotasi, dan scale yang disimpan
                        new_matrix = mathutils.Matrix.Translation(location_data) @ rotation.to_matrix().to_4x4()
                        new_matrix = new_matrix @ mathutils.Matrix.Scale(scale_data[0], 4, (1, 0, 0))  # Scale X
                        new_matrix = new_matrix @ mathutils.Matrix.Scale(scale_data[1], 4, (0, 1, 0))  # Scale Y
                        new_matrix = new_matrix @ mathutils.Matrix.Scale(scale_data[2], 4, (0, 0, 1))  # Scale Z
                        
                        bone.matrix = obj.matrix_world.inverted() @ new_matrix
                        
                        # Insert keyframe di frame saat ini berdasarkan opsi yang dipilih
                        if bake_location:
                            bone.keyframe_insert(data_path="location", index=-1)
                        if bake_rotation:
                            bone.keyframe_insert(data_path="rotation_quaternion", index=-1)
                            bone.keyframe_insert(data_path="rotation_euler", index=-1)
                        if bake_scale:
                            bone.keyframe_insert(data_path="scale", index=-1)
                        if bake_custom_props:
                            for prop in bone.keys():  
                                if prop not in "_RNA_UI":  # Hindari properti internal Blender
                                    bone.keyframe_insert(data_path=f'["{prop}"]')
                                
                    # Setelah selesai, maju 1 frame dan hapus keyframe
                    scene.frame_set(end_frame + 1)
                    if bake_location:
                        bone.keyframe_delete(data_path="location")
                    if bake_rotation:
                        bone.keyframe_delete(data_path="rotation_quaternion")
                        bone.keyframe_delete(data_path="rotation_euler")
                    if bake_scale:
                        bone.keyframe_delete(data_path="scale")
                    if bake_custom_props:
                        for prop in bone.keys():  
                            if prop not in "_RNA_UI":  # Hindari properti internal Blender
                                bone.keyframe_delete(data_path=f'["{prop}"]')                    
                    
                    # Deteksi constraint dan set influence ke 0
                    if bone.constraints:
                        for constraint in reversed(bone.constraints):  # Loop dari belakang untuk menghindari masalah index
                            bone.constraints.remove(constraint)  # Hapus constraint satu per satu
                        self.report({'INFO'}, f"Semua constraint pada bone {bone.name} telah dihapus.")

                self.report({'INFO'}, f"Smart Bake selesai untuk {len(selected_bones)} bone.")
            else:
                self.report({'WARNING'}, "Tidak ada bone yang dipilih.")
        else:
            self.report({'WARNING'}, "Harap masuk ke Pose Mode dan pilih bone.")
        return {'FINISHED'}
    

class RahaSaveBoneMatrix(bpy.types.Operator):
    """Menyimpan matrix location dan rotation dalam world space"""
    bl_idname = "object.save_bone_matrix"
    bl_label = "Simpan Matrix"
    
    def execute(self, context):
        obj = context.object
        if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
            bone = obj.pose.bones.get(context.active_pose_bone.name)
            if bone:
                stored_matrices[bone.name] = {
                    "matrix": [list(row) for row in (obj.matrix_world @ bone.matrix)]
                }
                self.report({'INFO'}, f"Matrix bone {bone.name} dalam world space disimpan.")
        else:
            self.report({'WARNING'}, "Harap masuk ke Pose Mode.")
        return {'FINISHED'}

class RahaApplyBoneMatrix(bpy.types.Operator):
    """Menerapkan matrix location dan rotation dalam world space serta membuat keyframe"""
    bl_idname = "object.apply_bone_matrix"
    bl_label = "Setel Matrix & Set Key"
    
    def execute(self, context):
        obj = context.object
        if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
            bone = obj.pose.bones.get(context.active_pose_bone.name)
            if bone and bone.name in stored_matrices:
                matrix_data = stored_matrices[bone.name]["matrix"]
                bone.matrix = obj.matrix_world.inverted() @ mathutils.Matrix(matrix_data)
                bone.keyframe_insert(data_path="location", index=-1)
                bone.keyframe_insert(data_path="rotation_quaternion", index=-1)
                bone.keyframe_insert(data_path="rotation_euler", index=-1)
                self.report({'INFO'}, f"Matrix bone {bone.name} diterapkan dalam world space dan keyframe diset.")
        else:
            self.report({'WARNING'}, "Harap masuk ke Pose Mode.")
        return {'FINISHED'}

class RahaForwardAnimation(bpy.types.Operator):
    """Menyimpan transformasi di frame awal lalu menerapkannya hingga frame akhir dengan keyframe"""
    bl_idname = "object.forward_animation"
    bl_label = "Forward"
    
    def execute(self, context):
        obj = context.object
        scene = context.scene
        start_frame = scene.start_frame
        end_frame = scene.end_frame
        
        if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
            bone = obj.pose.bones.get(context.active_pose_bone.name)
            if bone:
                stored_matrices[bone.name] = {
                    "matrix": [list(row) for row in (obj.matrix_world @ bone.matrix)]
                }
                for frame in range(start_frame, end_frame + 1):
                    scene.frame_set(frame)
                    matrix_data = stored_matrices[bone.name]["matrix"]
                    bone.matrix = obj.matrix_world.inverted() @ mathutils.Matrix(matrix_data)
                    bone.keyframe_insert(data_path="location", index=-1)
                    bone.keyframe_insert(data_path="rotation_quaternion", index=-1)
                    bone.keyframe_insert(data_path="rotation_euler", index=-1)
                self.report({'INFO'}, "Forward animation applied.")
        return {'FINISHED'}

class RahaBackwardAnimationBackwardAnimation(bpy.types.Operator):
    """Menyimpan transformasi di frame akhir lalu menerapkannya secara mundur hingga frame awal dengan keyframe"""
    bl_idname = "object.backward_animation"
    bl_label = "Backward"
    
    def execute(self, context):
        obj = context.object
        scene = context.scene
        start_frame = scene.start_frame
        end_frame = scene.end_frame
        
        if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
            bone = obj.pose.bones.get(context.active_pose_bone.name)
            if bone:
                scene.frame_set(end_frame)
                stored_matrices[bone.name] = {
                    "matrix": [list(row) for row in (obj.matrix_world @ bone.matrix)]
                }
                for frame in range(end_frame, start_frame - 1, -1):
                    scene.frame_set(frame)
                    matrix_data = stored_matrices[bone.name]["matrix"]
                    bone.matrix = obj.matrix_world.inverted() @ mathutils.Matrix(matrix_data)
                    bone.keyframe_insert(data_path="location", index=-1)
                    bone.keyframe_insert(data_path="rotation_quaternion", index=-1)
                    bone.keyframe_insert(data_path="rotation_euler", index=-1)
                self.report({'INFO'}, "Backward animation applied.")
        return {'FINISHED'}

# Panel untuk Smart Bake
class RahaBoneBakePanel(bpy.types.Panel):
    """Panel untuk menyimpan dan menerapkan matrix bone dalam world space"""
    bl_label = "Smart Bake"
    bl_idname = "OBJECT_PT_bone_bake"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'    
    bl_ui_units_x = 10
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene       
        layout.label(text="Bake and delete Constraint")                      
        layout.prop(scene, "start_frame")
        layout.prop(scene, "end_frame")  
        row = layout.row()             
        row.prop(scene, "bake_location", text="Location")  # Checkbox untuk Bake Location
        row.prop(scene, "bake_rotation", text="Rotation")  # Checkbox untuk Bake Rotation
        row = layout.row()  
        row.prop(scene, "bake_scale", text="Scale")       # Checkbox untuk Bake Scale
        row.prop(scene, "bake_custom_props", text="Custom Prop")  # Checkbox untuk Custom Properties
        layout.separator()  
        layout.operator("object.smart_bake", text="SMART BAKE ANIMATION") 

        
class RahaBoneMatrixPanel(bpy.types.Panel):
    """Panel untuk menyimpan dan menerapkan matrix bone dalam world space"""
    bl_label = "Fake constraint N step snap : raha tools"
    bl_idname = "OBJECT_PT_bone_matrix"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'    
    bl_ui_units_x = 10
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene       
        layout.label(text="Fake constraint")
        layout.operator("object.save_bone_matrix", text="Save data fake")
        layout.operator("object.apply_bone_matrix", text="Apply fake constraint")
         
        
        layout.separator()  
        layout.label(text="Step Snap")                       
        layout.prop(scene, "start_frame")
        layout.prop(scene, "end_frame")                
        row = layout.row()
        
        row.operator("object.forward_animation", text="Forward", icon='TRIA_RIGHT')
        row.operator("object.backward_animation", text="Backward", icon='TRIA_LEFT')     
        

classes = [RahaSaveBoneMatrix, RahaApplyBoneMatrix, RahaForwardAnimation, RahaBackwardAnimationBackwardAnimation, RahaSmartBake, RahaBoneMatrixPanel,RahaBoneBakePanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.start_frame = bpy.props.IntProperty(name="Start Frame", default=1)
    bpy.types.Scene.end_frame = bpy.props.IntProperty(name="End Frame", default=10)

    # Tambahkan properties untuk checkbox
    bpy.types.Scene.start_frame = bpy.props.IntProperty(name="Start Frame", default=1)
    bpy.types.Scene.end_frame = bpy.props.IntProperty(name="End Frame", default=250)
    bpy.types.Scene.bake_location = bpy.props.BoolProperty(name="Bake Location", default=True)
    bpy.types.Scene.bake_rotation = bpy.props.BoolProperty(name="Bake Rotation", default=True)
    bpy.types.Scene.bake_scale = bpy.props.BoolProperty(name="Bake Scale", default=True)
    bpy.types.Scene.bake_custom_props = bpy.props.BoolProperty(name="Bake Custom Properties", default=True)
    
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.start_frame
    del bpy.types.Scene.end_frame
    
    del bpy.types.Scene.bake_location
    del bpy.types.Scene.bake_rotation
    del bpy.types.Scene.bake_scale
    del bpy.types.Scene.bake_custom_props
if __name__ == "__main__":
    register()
