import bpy
import os
import requests
import zipfile
import base64
import shutil
import sys
from io import BytesIO

class RAHA_OT_InfoPopup(bpy.types.Operator):
    """Menampilkan informasi Raha Tools"""
    bl_idname = "raha.info_popup"
    bl_label = "Info"

    def execute(self, context):
        def draw_popup(self, context):
            layout = self.layout
            
            col = layout.column()
            col.label(text="Tools ini dibuat untuk mempermudah animasi di Blender 3D,")
            col.label(text="meningkatkan efisiensi kerja, dan mendukung kreativitas para animator.")
            col.separator()
            col.label(text="Tools ini gratis untuk latihan, proyek personal, dan komersial.")
            col.label(text="Namun, dilarang menyebarluaskan di luar link resmi serta dilarang")
            col.label(text="memodifikasi tanpa izin dari Raha Realistis Studio sebagai pemilik resmi.")
            col.separator()
            col.label(text="Saat ini, tools ini masih dalam tahap pengembangan dan akan terus diperbarui")
            col.label(text="dengan fitur-fitur baru. Saya juga memiliki banyak daftar tools lain")
            col.label(text="yang akan dibagikan secara gratis.")
            col.separator()
            col.label(text="Namun, agar proyek ini dapat terus berkembang, saya sangat mengharapkan")
            col.label(text="donasi dari semua pengguna sebagai modal pengembangan.")
            col.label(text="Dukungan Anda akan mempercepat pembaruan tools, pembuatan fitur baru,")
            col.label(text="dan program Free Learning di website saya.")
            col.separator()
            col.label(text="Mari bersama membangun ekosistem kreatif ini.")
            col.label(text="Terima kasih atas apresiasi dan kontribusinya!")
            
            col.separator()
            col.operator("raha.pb_tool", text="How to Use")            
            col.operator("raha.pb_tool", text="Report A Bug")          
        
        bpy.context.window_manager.popup_menu(draw_popup, title="Info", icon='INFO')
        return {'FINISHED'}

# Gunakan direktori cache sementara Blender
CACHE_DIR = bpy.app.tempdir
PY_FOLDER_V3 = os.path.join(CACHE_DIR, 'raha_tools', 'v3')
PY_FOLDER_V4 = os.path.join(CACHE_DIR, 'raha_tools', 'v4')

VERSION_FOLDERS = {
    "3": PY_FOLDER_V3,
    "4": PY_FOLDER_V4
}

for path in VERSION_FOLDERS.values():
    if path not in sys.path:
        sys.path.append(path)

# URL dalam Base64
VERSIONS_ENCODED = {
    "3": "aHR0cHM6Ly9naXRodWIuY29tL3Jyc3R1ZGlvZGV2ZWxvcG1lbnQvZG93bmxvYWRfYWxsX3NjcmlwdF9SUi1ULUIuMy9hcmNoaXZlL3JlZnMvaGVhZHMvbWFpbi56aXA=",
    "4": "aHR0cHM6Ly9naXRodWIuY29tL3Jyc3R1ZGlvZGV2ZWxvcG1lbnQvZG93bmxvYWRfYWxsX3NjcmlwdF9SUi1ULUIuNC9hcmNoaXZlL3JlZnMvaGVhZHMvbWFpbi56aXA="
}

executed_scripts = set()

def decode_url(encoded_url):
    return base64.b64decode(encoded_url).decode("utf-8")

def rename_folder_to_spyc(folder_path):
    """Mengubah nama folder menjadi _S_pyc"""
    parent_dir = os.path.dirname(folder_path)
    new_folder_name = "_S_pyc"
    new_folder_path = os.path.join(parent_dir, new_folder_name)
    
    if os.path.exists(new_folder_path):
        shutil.rmtree(new_folder_path)  # Hapus folder lama jika sudah ada
    
    os.rename(folder_path, new_folder_path)
    print(f"[INFO] Folder di-rename menjadi: {new_folder_path}")
    return new_folder_path

def download_and_extract(version):
    url = decode_url(VERSIONS_ENCODED.get(version, ""))  
    target_folder = VERSION_FOLDERS.get(version, "")
    
    if not url or not target_folder:
        print("[ERROR] Versi tidak valid!")
        return False
    
    os.makedirs(target_folder, exist_ok=True)
    
    try:
        print(f"[INFO] Mengunduh dari: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            with zipfile.ZipFile(BytesIO(response.content), 'r') as zip_ref:
                zip_ref.extractall(target_folder)
            print(f"[INFO] Raha Tools {version} berhasil diunduh dan diekstrak ke {target_folder}")
            
            # Rename folder setelah ekstraksi
            renamed_folder = rename_folder_to_spyc(target_folder)
            execute_all_scripts(renamed_folder)
            return True
        else:
            print(f"[ERROR] Gagal mengunduh Raha tools, status code: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Saat mengunduh repository: {e}")
    return False

def execute_all_scripts(folder_path):
    if os.path.exists(folder_path):
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".py"):
                    script_path = os.path.join(root, file)
                    execute_script(script_path)

def execute_script(script_path):
    global executed_scripts
    if script_path in executed_scripts:
        return
    if os.path.exists(script_path):
        try:
            bpy.ops.script.python_file_run(filepath=script_path)
            executed_scripts.add(script_path)
        except Exception as e:
            print(f"[ERROR] Gagal menjalankan {script_path}: {e}")

class DOWNLOAD_OT_RunScript(bpy.types.Operator):
    bl_idname = "wm.download_run_all_scripts"
    bl_label = "Select version"
    
    version: bpy.props.EnumProperty(
        name="Version",
        items=[("3", "Blender 3+", "Download Raha Tools for Blender 3+"),
               ("4", "Blender 4+", "Download Raha Tools for Blender 4+")],
        default="3"
    )

    def execute(self, context):
        download_and_extract(self.version)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class DOWNLOAD_OT_RepairScripts(bpy.types.Operator):
    bl_idname = "wm.repair_scripts"
    bl_label = "Repair Scripts"

    def execute(self, context):
        for version, folder in VERSION_FOLDERS.items():
            if os.path.exists(folder):
                print(f"[INFO] Memperbaiki script untuk versi {version}...")
                shutil.rmtree(folder)  # Hapus folder versi yang ada
                download_and_extract(version)  # Unduh dan ekstrak ulang
        return {'FINISHED'}

class DOWNLOAD_PT_Panel(bpy.types.Panel):
    bl_label = "Call Script Raha_Tools"
    bl_idname = "DOWNLOAD_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Raha_Tools"

    def draw(self, context):
        layout = self.layout        
        row = layout.row()
        row.alignment = 'RIGHT'
        row.operator("raha.info_popup", text="WARNING", icon='ERROR')
                
        layout = self.layout
        layout.label(text="Make sure there is an internet connection")
        layout.operator("wm.download_run_all_scripts")
#        layout.operator("wm.repair_scripts")

def register():
    bpy.utils.register_class(DOWNLOAD_OT_RunScript)
    bpy.utils.register_class(DOWNLOAD_OT_RepairScripts)
    bpy.utils.register_class(DOWNLOAD_PT_Panel)
    bpy.utils.register_class(RAHA_OT_InfoPopup)    
    

def unregister():
    bpy.utils.unregister_class(DOWNLOAD_OT_RunScript)
    bpy.utils.unregister_class(DOWNLOAD_OT_RepairScripts)
    bpy.utils.unregister_class(DOWNLOAD_PT_Panel)
    bpy.utils.unregister_class(RAHA_OT_InfoPopup)     

if __name__ == "__main__":
    register()
