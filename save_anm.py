import bpy
import math
import os
# Tambahkan properti ke scene
bpy.types.Scene.use_custom_frame_range = bpy.props.BoolProperty(
    name="Gunakan Rentang Bingkai Kustom",
    description="Start - end frame export",
    default=False  # Nilai default properti
)

bpy.types.Scene.custom_start_frame = bpy.props.IntProperty(
    name="Bingkai Mulai",
    description="Bingkai awal untuk ekspor",
    default=1
)

bpy.types.Scene.custom_end_frame = bpy.props.IntProperty(
    name="Bingkai Selesai",
    description="Start - end frame",
    default=250
)

bpy.types.Scene.insert_missing_keyframes = bpy.props.BoolProperty(
    name="Perbaiki Keyframe",
    description="Scan and fix your keyframe",
    default=False
)

        
#================================ DEF insert_missing_keyframes =============================
def insert_missing_keyframes():
    obj = bpy.context.active_object

    # Pastikan objek adalah Armature dan dalam Pose Mode
    if obj is None or obj.type != 'ARMATURE' or obj.mode != 'POSE':
        print("Pilih objek Armature dalam Pose Mode.")
        return
    
    action = obj.animation_data.action if obj.animation_data else None
    if action is None:
        print("Objek tidak memiliki action (data animasi).")
        return
    
    scene = bpy.context.scene
    original_start_frame = scene.frame_start
    original_end_frame = scene.frame_end

    try:
        if scene.use_custom_frame_range:
            scene.frame_start = scene.custom_start_frame
            scene.frame_end = scene.custom_end_frame

        # Ambil semua keyframe yang ada pada action
        keyframes = set()  # Set untuk menyimpan frame-frame unik
        for fcurve in action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframes.add(int(keyframe.co.x))  # Masukkan frame sebagai integer

        # Iterasi melalui keyframe yang ada
        for current_frame in sorted(keyframes):
            bpy.context.scene.frame_set(current_frame)  # Set frame saat ini

            # Iterasi setiap bone yang dipilih
            for bone in obj.pose.bones:
                keyframe_status_euler = [False, False, False]  # Status keyframe untuk Rotation Euler (X, Y, Z)
                keyframe_status_quat = [False, False, False, False]  # Status keyframe untuk Quaternion (W, X, Y, Z)
                keyframe_status_loc = [False, False, False]  # Status keyframe untuk Location (X, Y, Z)
                keyframe_status_scale = [False, False, False]  # Status keyframe untuk Scale (X, Y, Z)

                # Periksa keyframe hanya pada frame saat ini
                for fcurve in action.fcurves:
                    if fcurve.data_path == f'pose.bones["{bone.name}"].rotation_euler':
                        for keyframe in fcurve.keyframe_points:
                            if int(keyframe.co.x) == current_frame:
                                keyframe_status_euler[fcurve.array_index] = True

                    elif fcurve.data_path == f'pose.bones["{bone.name}"].rotation_quaternion':
                        for keyframe in fcurve.keyframe_points:
                            if int(keyframe.co.x) == current_frame:
                                keyframe_status_quat[fcurve.array_index] = True

                    elif fcurve.data_path == f'pose.bones["{bone.name}"].location':
                        for keyframe in fcurve.keyframe_points:
                            if int(keyframe.co.x) == current_frame:
                                keyframe_status_loc[fcurve.array_index] = True

                    elif fcurve.data_path == f'pose.bones["{bone.name}"].scale':
                        for keyframe in fcurve.keyframe_points:
                            if int(keyframe.co.x) == current_frame:
                                keyframe_status_scale[fcurve.array_index] = True

                # Hitung jumlah sumbu yang memiliki keyframe
                keyframe_count_euler = sum(keyframe_status_euler)
                keyframe_count_quat = sum(keyframe_status_quat)
                keyframe_count_loc = sum(keyframe_status_loc)
                keyframe_count_scale = sum(keyframe_status_scale)

                # Tambahkan keyframe yang hilang jika hanya sebagian ada
                if 0 < keyframe_count_euler < 3:
                    if not keyframe_status_euler[0]: bone.keyframe_insert(data_path="rotation_euler", index=0)  # X
                    if not keyframe_status_euler[1]: bone.keyframe_insert(data_path="rotation_euler", index=1)  # Y
                    if not keyframe_status_euler[2]: bone.keyframe_insert(data_path="rotation_euler", index=2)  # Z
                    print(f"Keyframe rotation_euler ditambahkan untuk bone {bone.name} pada frame {current_frame}.")

                if 0 < keyframe_count_loc < 3:
                    if not keyframe_status_loc[0]: bone.keyframe_insert(data_path="location", index=0)  # X
                    if not keyframe_status_loc[1]: bone.keyframe_insert(data_path="location", index=1)  # Y
                    if not keyframe_status_loc[2]: bone.keyframe_insert(data_path="location", index=2)  # Z
                    print(f"Keyframe location ditambahkan untuk bone {bone.name} pada frame {current_frame}.")

                if 0 < keyframe_count_scale < 3:
                    if not keyframe_status_scale[0]: bone.keyframe_insert(data_path="scale", index=0)  # X
                    if not keyframe_status_scale[1]: bone.keyframe_insert(data_path="scale", index=1)  # Y
                    if not keyframe_status_scale[2]: bone.keyframe_insert(data_path="scale", index=2)  # Z
                    print(f"Keyframe scale ditambahkan untuk bone {bone.name} pada frame {current_frame}.")

    finally:
        # Kembalikan nilai asli frame_start dan frame_end
        scene.frame_start = original_start_frame
        scene.frame_end = original_end_frame
#========================================= EKPORT BONE ================================================
def get_value_type(bone, prop_name, value):
    # Periksa tipe data properti di Blender
    if prop_name in bone and isinstance(bone[prop_name], int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "str"
    elif isinstance(value, (list, tuple)):
        return "list"
    else:
        return "unknown"

def export_bone_keyframe_data(context, filepath):
    armature_obj = context.object
    if not armature_obj or armature_obj.type != 'ARMATURE':
        return {'CANCELLED'}   
    
    scene = bpy.context.scene
    
    # Simpan nilai asli frame_start dan frame_end
    original_start_frame = scene.frame_start
    original_end_frame = scene.frame_end

    try:
        # Gunakan custom frame range jika diaktifkan
        if scene.use_custom_frame_range:
            scene.frame_start = scene.custom_start_frame
            scene.frame_end = scene.custom_end_frame
                 
        selected_bones = [bone.name for bone in bpy.context.selected_pose_bones]
        
        matched_bones = {}            

        # Tentukan path folder ANIM_DATA dan Preview
        base_folder = os.path.dirname(filepath)
        anim_data_folder = os.path.join(base_folder, "ANIM_DATA")
        preview_folder = os.path.join(base_folder, "Preview")

        # Pastikan folder ANIM_DATA dan Preview ada
        if not os.path.exists(anim_data_folder):
            os.makedirs(anim_data_folder)
        if not os.path.exists(preview_folder):
            os.makedirs(preview_folder)

        # Tentukan path untuk file script, video, dan screenshot
        file_name = os.path.splitext(os.path.basename(filepath))[0]
        script_path = os.path.join(anim_data_folder, f"{file_name}.py")
        playblast_path = os.path.join(preview_folder, f"{file_name}.mp4")
        screenshot_path = os.path.join(base_folder, f"{file_name}.png")
        
        # Mendapatkan data keyframe dari bone yang dipilih
        bone_data = {}
        for bone in armature_obj.pose.bones:
            if bone.bone.select:
                bone_data[bone.name] = {}

                # Pastikan armature_obj memiliki animation_data dan action
                if armature_obj.animation_data:
                    action = armature_obj.animation_data.action
                    
                    # Periksa apakah action ada dan memiliki fcurves
                    if action and hasattr(action, 'fcurves') and action.fcurves:
                        for fcurve in action.fcurves:
                            if fcurve.data_path.startswith(f'pose.bones["{bone.name}"]'):
                                for keyframe in fcurve.keyframe_points:
                                    frame = int(keyframe.co[0])
                                    
                                    # Filter keyframe berdasarkan rentang frame yang ditentukan
                                    if scene.use_custom_frame_range:
                                        if frame < scene.custom_start_frame or frame > scene.custom_end_frame:
                                            continue  # Skip keyframe di luar rentang
                                    
                                    if frame not in bone_data[bone.name]:
                                        bone_data[bone.name][frame] = {}

                                    # Simpan data_path dan nilai keyframe
                                    data_path = fcurve.data_path.split('"]')[-1][1:]  # Ambil properti (misal: ".location")
                                    if data_path not in bone_data[bone.name][frame]:
                                        bone_data[bone.name][frame][data_path] = {}

                                    # Simpan nilai sesuai dengan indeks sumbu (0: X, 1: Y, 2: Z)
                                    bone_data[bone.name][frame][data_path][fcurve.array_index] = keyframe.co[1]

                    else:
                        print(f"No fcurves or action found for bone: {bone.name}")

                # Simpan custom properties jika ada
                if bone.keys():
                    for frame in bone_data[bone.name]:
                        bone_data[bone.name][frame]["custom_props"] = {}

                    for prop_name in bone.keys():
                        if prop_name not in "_RNA_UI":  # Abaikan properti internal Blender
                            # Pastikan action dan fcurves ada sebelum mengaksesnya
                            if armature_obj.animation_data and armature_obj.animation_data.action:
                                action = armature_obj.animation_data.action
                                if hasattr(action, 'fcurves'):
                                    for fcurve in action.fcurves:
                                        if fcurve.data_path == f'pose.bones["{bone.name}"]["{prop_name}"]':
                                            for keyframe in fcurve.keyframe_points:
                                                frame = int(keyframe.co[0])

                                                # Filter keyframe berdasarkan rentang frame yang ditentukan
                                                if scene.use_custom_frame_range:
                                                    if frame < scene.custom_start_frame or frame > scene.custom_end_frame:
                                                        continue  # Skip keyframe di luar rentang

                                                # Ambil nilai keyframe
                                                value = keyframe.co[1]

                                                # Simpan custom property dengan tipe data
                                                bone_data[bone.name][frame]["custom_props"][prop_name] = {
                                                    "value": value,
                                                    "type": get_value_type(bone, prop_name, value)
                                                }

        if not bone_data:
            return {'CANCELLED'}

        # Menulis data ke file .py
        with open(script_path, 'w') as file:
            file.write("import bpy\n")
            file.write("import math\n\n")
            file.write("# Mendapatkan scene aktif\n")
            file.write("scene = bpy.context.scene\n\n")
            file.write("# Mendapatkan daftar tulang yang dipilih\n")
            file.write("selected_pose_bones = bpy.context.selected_pose_bones\n")
            file.write("if not selected_pose_bones:\n")  
            file.write("    print('Tidak ada tulang yang dipilih.')\n")  
            file.write("else:\n") 
            file.write("    armature_obj = selected_pose_bones[0].id_data\n")  
            file.write("    selected_bones = [bone.name for bone in selected_pose_bones]\n")                                  
            file.write("# Menyiapkan dictionary untuk menyimpan bone yang cocok\n")
            file.write("matched_bones = {}\n\n")

            # Gabungkan semua frame dari semua bone
            all_frames = set()
            for bone_name, frames in bone_data.items():
                all_frames.update(frames.keys())
            all_frames = sorted(all_frames)

            prev_frame = None
            for frame in all_frames:
                file.write(f"# Frame {frame}\n")
                if prev_frame is None:
                    file.write("frame_current = scene.frame_current\n")
                    file.write("scene.frame_set(frame_current)\n")
                    file.write("bpy.ops.anim.keyframe_insert()\n")

                else:
                    frame_distance = frame - prev_frame
                    file.write(f"frame_target = frame_current + {frame_distance}\n")
                    file.write("scene.frame_set(frame_target)\n")
                    file.write("frame_current = frame_target\n")
                
                for bone_name, frames in bone_data.items():
                    if frame in frames:
                        file.write(f"if '{bone_name}' in selected_bones:\n")
                        file.write(f"    bone = armature_obj.pose.bones['{bone_name}']\n")
                        data = frames[frame]
                        for data_path, value in data.items():
                            if data_path == "location":
                                # Ambil nilai untuk X, Y, Z. Gunakan nilai default jika tidak ada keyframe.
                                x = value.get(0, bone.location[0])  # Gunakan nilai saat ini untuk X jika tidak ada keyframe
                                y = value.get(1, bone.location[1])  # Gunakan nilai saat ini untuk Y jika tidak ada keyframe
                                z = value.get(2, bone.location[2])  # Gunakan nilai saat ini untuk Z jika tidak ada keyframe
                                
                                # Menulis data lokasi dengan nilai yang sudah disinkronisasi
                                file.write(f"    bone.location = ({x}, {y}, {z})\n")
                                file.write(f"    bone.keyframe_insert(data_path='location')\n")


                            elif data_path == "rotation_quaternion":
                                # Pastikan semua sumbu (W, X, Y, Z) memiliki keyframe
                                w = value.get(0, bone.rotation_quaternion[0])
                                x = value.get(1, bone.rotation_quaternion[1])
                                y = value.get(2, bone.rotation_quaternion[2])
                                z = value.get(3, bone.rotation_quaternion[3])
                                file.write(f"    bone.rotation_quaternion = ({w}, {x}, {y}, {z})\n")
                                file.write(f"    bone.keyframe_insert(data_path='rotation_quaternion')\n")
                            elif data_path == "rotation_euler":
                                # Pastikan semua sumbu (X, Y, Z) memiliki keyframe
                                x = value.get(0, bone.rotation_euler[0])
                                y = value.get(1, bone.rotation_euler[1])
                                z = value.get(2, bone.rotation_euler[2])
                                file.write(f"    bone.rotation_euler = ({x}, {y}, {z})\n")
                                file.write(f"    bone.keyframe_insert(data_path='rotation_euler')\n")
                            elif data_path == "scale":
                                # Pastikan semua sumbu (X, Y, Z) memiliki keyframe
                                x = value.get(0, bone.scale[0])
                                y = value.get(1, bone.scale[1])
                                z = value.get(2, bone.scale[2])
                                file.write(f"    bone.scale = ({x}, {y}, {z})\n")
                                file.write(f"    bone.keyframe_insert(data_path='scale')\n")
                                    
                            elif data_path == "custom_props":
                                for prop_name, prop_data in value.items():
                                    prop_value = prop_data["value"]
                                    prop_type = prop_data["type"]
                                    
                                    if prop_type == "int":
                                        file.write(f'    bone["{prop_name}"] = int({prop_value})\n')
                                    elif prop_type == "float":
                                        file.write(f'    bone["{prop_name}"] = float({prop_value})\n')
                                    elif prop_type == "str":
                                        file.write(f'    bone["{prop_name}"] = "{prop_value}"\n')
                                    elif prop_type == "list":
                                        file.write(f'    bone["{prop_name}"] = {list(prop_value)}\n')
                                    else:
                                        file.write(f'    bone["{prop_name}"] = {prop_value}\n')
                                    
                                    # Tambahkan keyframe
                                    file.write(f'    bone.keyframe_insert(data_path=\'["{prop_name}"]\')\n')

                                    
                prev_frame = frame
                file.write("\n")
                
        # Playblast viewport dalam format MP4
        bpy.context.scene.render.filepath = playblast_path
        bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
        bpy.context.scene.render.ffmpeg.format = 'MPEG4'
        bpy.context.scene.render.ffmpeg.codec = 'H264'
        bpy.context.scene.render.ffmpeg.audio_codec = 'AAC'
        bpy.ops.render.opengl(animation=True)  # Render playblast

        # Ambil screenshot dari frame pertama
        scene.frame_set(scene.frame_start)  # Set frame ke frame pertama

        # Simpan pengaturan format file asli
        original_file_format = bpy.context.scene.render.image_settings.file_format

        # Set format file ke PNG untuk screenshot
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.filepath = screenshot_path  # Set filepath untuk screenshot
        bpy.ops.render.opengl(write_still=True)  # Ambil screenshot

        # Kembalikan format file ke pengaturan asli (untuk playblast)
        bpy.context.scene.render.image_settings.file_format = original_file_format
        
    finally:
        # Kembalikan nilai asli frame_start dan frame_end
        scene.frame_start = original_start_frame
        scene.frame_end = original_end_frame
            
    return {'FINISHED'}

#================================= DEF import_bone_keyframe_data ========================
def import_bone_keyframe_data(context, filepath):
    directory, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)

    anim_data_dir = os.path.join(directory, "ANIM_DATA")

    if not os.path.exists(anim_data_dir):
        print(f"Folder ANIM_DATA tidak ditemukan di: {directory}")
        return {'CANCELLED'}

    script_filepath = os.path.join(anim_data_dir, f"{name}.py")  # Asumsi file script berekstensi .py

    if not os.path.exists(script_filepath):
        print(f"File script {name}.py tidak ditemukan di: {anim_data_dir}")
        return {'CANCELLED'}
    
    try:
        with open(script_filepath, 'r') as file:
            exec(file.read())
        print(f"Data keyframe dari {script_filepath} berhasil diimpor.")
        return {'FINISHED'}
    except Exception as e:  # Tangani potensi error saat membaca atau mengeksekusi script
        print(f"Terjadi error saat mengimpor script: {e}")
        return {'CANCELLED'}
    
def preview_video(filepath):
    if not os.path.exists(filepath):
        print(f"File video tidak ditemukan: {filepath}")
        return {'CANCELLED'}

    try:
        # Menggunakan subprocess untuk membuka video dengan default player di Windows
        subprocess.Popen([filepath], shell=True)  # shell=True lebih fleksibel
        print(f"Membuka video: {filepath}")
        return {'FINISHED'}
    except Exception as e:
        print(f"Gagal membuka video: {e}")
        return {'CANCELLED'}    

#==================================== ANIMImportBoneKeyframeData ==========================
class ANIMImportBoneKeyframeData(bpy.types.Operator):
    bl_idname = "object.import_bone_keyframe_data"
    bl_label = "Import Data"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        return import_bone_keyframe_data(context, self.filepath)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# #========================================= OPERATOR ANIMExportBoneKeyframeData ===================
class ANIMExportBoneKeyframeData(bpy.types.Operator):
    bl_idname = "object.export_bone_keyframe_data"
    bl_label = "Export Bone Keyframe Data"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    insert_missing_keyframes: bpy.props.BoolProperty(
        name="Insert Missing Keyframes",
        description="Insert missing keyframes before exporting",
        default=False
    )

    def execute(self, context):
        if self.insert_missing_keyframes:
            insert_missing_keyframes()
        return export_bone_keyframe_data(context, self.filepath)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

#=============================================  Panel UI ====================================
    
class ANIMBoneKeyframePanel(bpy.types.Panel):
    bl_label = "SAVE ANIMATION"
    bl_idname = "OBJECT_PT_bone_keyframe"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 10
    

    def draw(self, context):
        layout = self.layout
        scene = context.scene                
                
        layout = self.layout     
        layout.prop(scene, "use_custom_frame_range", text="Use Custom Frame Range")
        if scene.use_custom_frame_range:
            layout.prop(scene, "custom_start_frame", text="Start Frame")
            layout.prop(scene, "custom_end_frame", text="End Frame")        
           
        layout.prop(context.scene, "insert_missing_keyframes", text="let's fix your keyframe")
        export_op = layout.operator("object.export_bone_keyframe_data", text="Export Animation")
        export_op.insert_missing_keyframes = context.scene.insert_missing_keyframes      
        layout.operator("object.export_bone_keyframe_data_pose", text="Export (Pose)") 
        
        layout.separator()        
                                             
#       layout.operator("object.import_bone_keyframe_data", text="Import")

      
            
class ANIMExportBoneSettings(bpy.types.PropertyGroup):
    use_custom_frame_range: bpy.props.BoolProperty(
        name="Custom Frame Range",
        description="Enable custom frame range for playblast",
        default=False
    )
    custom_start_frame: bpy.props.IntProperty(  # Corrected property name
        name="Start Frame",
        default=1
    )
    custom_end_frame: bpy.props.IntProperty(  # Corrected property name
        name="End Frame",
        default=250
    )               
        

# Registrasi addon
def register():
    print("Anim Lib Registered")
    bpy.utils.register_class(ANIMExportBoneKeyframeData)
    bpy.utils.register_class(ANIMImportBoneKeyframeData)
    bpy.utils.register_class(ANIMExportBoneSettings) 
    bpy.utils.register_class(ANIMBoneKeyframePanel)

    # Definisi property dengan format yang benar
    use_custom_frame_range: bpy.props.BoolProperty(
        name="Custom Frame Range",
        description="Enable custom frame range for playblast",
        default=False
    )

    bpy.types.Scene.custom_start_frame = bpy.props.IntProperty(
        name="Custom Start Frame",
        default=1
    )

    bpy.types.Scene.custom_end_frame = bpy.props.IntProperty(
        name="Custom End Frame",
        default=250
    )

def unregister():
    print("Anim Lib Unregistered")
    bpy.utils.unregister_class(ANIMExportBoneKeyframeData)
    bpy.utils.unregister_class(ANIMImportBoneKeyframeData)
    bpy.utils.unregister_class(ANIMExportBoneSettings) 
    bpy.utils.unregister_class(ANIMBoneKeyframePanel)

    # Menghapus properti dari bpy.types.Scene dengan benar
    del bpy.types.Scene.insert_missing_keyframes
    del bpy.types.Scene.custom_start_frame
    del bpy.types.Scene.custom_end_frame
    

if __name__ == "__main__":
    register()
