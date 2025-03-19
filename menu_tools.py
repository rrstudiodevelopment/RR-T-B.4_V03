
import bpy
import webbrowser
import os
import requests
import bpy.utils.previews
import atexit
import shutil
import getpass
import ctypes

#============================ Download image ===========================
# Konstanta dan variabel global
FOLDER_ID = "1ovu2YSN-rPmvBp7a-G_w1lNS4uEGpEFN"
API_KEY = "AIzaSyD5epC5ofWTgh0PvAbLVy28W34NnwkkNyM"
USERNAME = getpass.getuser()
TEMP_DIR = f"C:\\Users\\{USERNAME}\\AppData\\Local\\Temp"
IMAGE_FOLDER = os.path.join(TEMP_DIR, "download_image")
CACHED_IMAGE_PATH = os.path.join(IMAGE_FOLDER, "google_drive_image.jpg")
IS_DOWNLOADED = False
preview_collections = {}

def remove_readonly(func, path, _):
    """Mengubah atribut file agar bisa dihapus."""
    os.chmod(path, 0o777)
    func(path)

def ensure_image_folder():
    """Hapus folder jika ada, lalu buat ulang."""
    if os.path.exists(IMAGE_FOLDER):
        shutil.rmtree(IMAGE_FOLDER, onerror=remove_readonly)
    os.makedirs(IMAGE_FOLDER)

def get_image_url():
    """Mencari gambar 'news' terlebih dahulu, jika tidak ada cari 'RRS-logo' di Google Drive."""
    url = f"https://www.googleapis.com/drive/v3/files?q='{FOLDER_ID}'+in+parents&key={API_KEY}&fields=files(id,name,mimeType)"
    try:
        response = requests.get(url)
        data = response.json()
        
        if "files" in data and data["files"]:
            for file in data["files"]:
                if "news" in file["name"].lower() and file["mimeType"].startswith("image/"):
                    return f"https://drive.google.com/uc?export=view&id={file['id']}"
            for file in data["files"]:
                if "rrs-logo" in file["name"].lower() and file["mimeType"].startswith("image/"):
                    return f"https://drive.google.com/uc?export=view&id={file['id']}"
    except Exception as e:
        print(f"Error mengambil data dari Google Drive: {e}")
    return None

def download_image():
    """Download gambar hanya jika belum ada."""
    global IS_DOWNLOADED
    ensure_image_folder()
    
    img_url = get_image_url()
    if not img_url:
        return None
    
    try:
        response = requests.get(img_url, stream=True)
        if response.status_code == 200:
            with open(CACHED_IMAGE_PATH, 'wb') as file:
                file.write(response.content)
            print(f"Gambar berhasil diunduh: {CACHED_IMAGE_PATH}")
            IS_DOWNLOADED = True
            return CACHED_IMAGE_PATH
    except Exception as e:
        print(f"Error mengunduh gambar: {e}")
    return None
#=====================================================================================================================

#                   SLIDE INFLUENCE    

def get_copy_constraints(bone):
    constraint_rot = None
    constraint_loc = None

    for constraint in bone.constraints:
        if constraint.type == 'COPY_ROTATION':
            constraint_rot = constraint
        elif constraint.type == 'COPY_LOCATION':
            constraint_loc = constraint

    return constraint_rot, constraint_loc

    
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

#============================================= Panel info ==================================
class RAHA_OT_InfoPopup(bpy.types.Operator):
    """Menampilkan informasi Raha Tools"""
    bl_idname = "raha.info_update"
    bl_label = "Info update"

    def execute(self, context):
        def draw_popup(self, context):
            layout = self.layout
            
            col = layout.column()
            col.label(text="update 19/03/2025 - 20:44")
            col.label(text="Raha Tools v.03")            
            col.separator()            
            col.label(text="- fix bug export animation ")
            col.label(text="- update playblast")
#            col.label(text="- update import animation")
#           col.label(text="- Playblast + HUD")
#            col.separator()
#            col.label(text="- add fitur keyframe editor di graph editor")
#            col.label(text="- update security")        
#            col.separator()
#            col.operator("raha.pb_tool", text="How to Use")            
 #           col.operator("raha.pb_tool", text="Report A Bug")          
        
        bpy.context.window_manager.popup_menu(draw_popup, title="Info", icon='INFO')
        return {'FINISHED'}    
    
#=========================================== Panel Run Script ========================================================
class RAHA_PT_Tools_For_Animation(bpy.types.Panel):
    """Panel tambahan yang muncul setelah Run Tools ditekan"""
    bl_label = "Raha Tools blender 4+"
    bl_idname = "RAHA_PT_For_Animation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Raha_Tools"
    
    preview_collection = None 

    def draw(self, context):
        layout = self.layout
        wm = bpy.context.window_manager  # Pastikan ini ada sebelum digunakan        
        obj = context.object
        scene = context.scene           
        
        preview_collection = None             

        if not IS_DOWNLOADED:  # Download hanya sekali saat pertama kali
            download_image()

        img_path = CACHED_IMAGE_PATH if os.path.exists(CACHED_IMAGE_PATH) else None

        if img_path:
            if RAHA_PT_Tools_For_Animation.preview_collection is None:
                RAHA_PT_Tools_For_Animation.preview_collection = bpy.utils.previews.new()
                RAHA_PT_Tools_For_Animation.preview_collection.load("google_drive_image", img_path, 'IMAGE')

            layout.template_icon(RAHA_PT_Tools_For_Animation.preview_collection["google_drive_image"].icon_id, scale=10)
        else:
            layout.label(text="Gambar tidak ditemukan")
            
        # Tombol Info
        row = layout.row()
        row.alignment = 'RIGHT'
#        row.operator("raha.info_popup", text="WARNIG", icon='ERROR')
        row.operator("raha.info_update", text="info update", icon='ERROR')        
        # Cek apakah preview tersedia

        
        # Tombol Run Tools

        layout.operator("raha.subscribe", text="Subscribe", icon='PLAY')            
        layout.operator("raha.donate", text="Donate", icon='FUND')  
        
                      
        active_keymap = wm.keyconfigs.active.name
        layout.label(text=f"Active Keymap: {active_keymap}")   
        row = layout.row()      
        # Tombol untuk mengganti keymap
        row.operator("wm.set_blender_keymap", text="Blender")
        row.operator("wm.set_maya_keymap", text="Maya")
        
        layout = self.layout 
        layout.label(text="Animation Library")                
        row = layout.row()          
#        row.operator("floating.open_save_animation", text="Save Animation")
        row.operator("floating.open_import_animation", text="Animation Library")          
        layout = self.layout        
        layout.operator("floating.open_panel_pose_lib", text="Library pose") 
        
                    
                
#================================ Menu parent conststraint ==================================================================      
 
        layout.label(text="Parent Constraint")         
        row = layout.row()        
        row.operator("floating.open_childof", text="Child-of")
        row.operator("floating.open_locrote", text="Locrote")  
               
        layout = self.layout
        layout.operator("floating.open_smart_bake", text="Smart Bake")               
        layout.operator("floating.open_fake_step", text="Fake N Step Snap")
        
#========================================================================================================================

                                    
        layout.separator()
        layout.operator("floating.open_mini_tools", text="Mini Tools")  
        
        # Checkbox untuk menampilkan Tween Machine
        layout.prop(scene, "show_tween_machine", text="Show Tween Machine")
        
        # Jika checkbox dicentang, tampilkan tombol Tween Machine
        if scene.show_tween_machine:
            layout.label(text="Tween Machine:")
            layout.prop(scene, "pose_breakdowner_factor", text="Factor")
            layout.separator()
            
            col = layout.column()
            row = col.row()       
            row.operator("pose.breakdown_custom", text="20").factor = 0.1
            row.operator("pose.breakdown_custom", text="50").factor = 0.5
            row.operator("pose.breakdown_custom", text="80").factor = 0.8
            
            row = col.row()
            row.operator("pose.breakdown_custom", text="0").factor = 0.0
            row.operator("pose.breakdown_custom", text="100").factor = 1.0

        layout.label(text="Audio HUD Playblast")
        layout.operator("floating.open_pb_hud", text="A   H    P")  
        
        pcoll = preview_collections.get("raha_previews")     




        #                                                   SLIDE INFLUENCE   
      
#influence Childof        
        obj = context.object
        if obj and obj.pose:
            for bone in obj.pose.bones:
                if bone.bone.select:
                    constraints = [constraint for constraint in bone.constraints if constraint.type == 'CHILD_OF' and constraint.name.startswith("parent_child")]
                    for constraint in constraints:
                        # Menampilkan 'influence' untuk setiap 'Child-Of'
                        layout.label(text="Parent Childof influence")                        
                        row = layout.row()
                        row.label(text=f"Parent {constraint.subtarget})")
                        row.prop(constraint, "influence", text="inf")   
                    
#influence LOCROTAE
        obj = context.object
        if obj and obj.pose:
            for bone in obj.pose.bones:
                if bone.bone.select:
                    # Mendapatkan constraint Copy Rotation dan Copy Location
                    constraint_rot, constraint_loc = get_copy_constraints(bone)

                    if constraint_rot or constraint_loc:
                        # Menambahkan kontrol bersama untuk influence
                        layout.label(text="Parent Locrote influence") 
                        row = layout.row()
                        row.prop(bone, "copy_constraints_influence", slider=True, text=" LOCROTE")

                        # Set influence untuk kedua constraint sekaligus
                        if constraint_rot:
                            constraint_rot.influence = bone.copy_constraints_influence
                        if constraint_loc:
                            constraint_loc.influence = bone.copy_constraints_influence

#========================================= Def Donate Link ===================================================
class RAHA_OT_Donate(bpy.types.Operator):
    """Membuka link donasi"""
    bl_idname = "raha.donate"
    bl_label = "Donate"

    def execute(self, context):
        webbrowser.open("https://saweria.co/rrstudio26")
        return {'FINISHED'}
#========================================= Def Subcribe Link ===================================================    
class RAHA_OT_Subscribe(bpy.types.Operator):
    """Membuka link subscribe"""
    bl_idname = "raha.subscribe"
    bl_label = "subscribe"

    def execute(self, context):
        webbrowser.open("https://www.youtube.com/@RR_STUDIO26")
        return {'FINISHED'}    
    
#================================================ Def untuk memunculkan PANEL Raha Tools For Animation ==========================
class RAHA_OT_RunTools(bpy.types.Operator):
    """Menampilkan tombol alat tambahan dan membuka tautan YouTube"""
    bl_idname = "raha.run_tween_machine"
    bl_label = "Run run machine"

    def execute(self, context):
        self.toggle_tools(context)  # Memanggil fungsi pertama
#        self.open_youtube()         # Memanggil fungsi kedua
        return {'FINISHED'}

    def toggle_tools(self, context):
        """Menampilkan / menyembunyikan alat tambahan"""
        if hasattr(context.window_manager, "show_raha_tools_For_Animation"):
            context.window_manager.show_raha_tools_For_Animation = not context.window_manager.show_raha_tools_For_Animation
        else:
            context.window_manager.show_raha_tools_For_Animation = True  
            

#    def open_youtube(self):
#        """Membuka tautan YouTube"""
#        webbrowser.open("https://www.youtube.com/@RR_STUDIO26")  
            
            
#============================================================================================================    
#                                           KEYMAP


# Fungsi untuk mengganti keymap
def set_keymap(keymap_type):
    keyconfigs = bpy.context.window_manager.keyconfigs
    
    blender_keymap = keyconfigs.get("Blender")
    maya_keymap = keyconfigs.get("maya")  # Pastikan ini adalah keymap Maya
        
    if keymap_type == 'BLENDER' and blender_keymap:
        keyconfigs.active = blender_keymap
    elif keymap_type == 'MAYA' and maya_keymap:
        keyconfigs.active = maya_keymap
    else:
        # Jika keymap yang dipilih tidak ada
        print(f"Keymap '{keymap_type}' tidak ditemukan. Pastikan keymap sudah diinstal.")

# Operator untuk tombol keymap Blender
class SetBlenderKeymapOperator(bpy.types.Operator):
    bl_idname = "wm.set_blender_keymap"
    bl_label = "Set Blender Keymap"
    
    def execute(self, context):
        set_keymap('BLENDER')
        return {'FINISHED'}

# Operator untuk tombol keymap Maya
class SetMayaKeymapOperator(bpy.types.Operator):
    bl_idname = "wm.set_maya_keymap"
    bl_label = "Set Maya Keymap"
    
    def execute(self, context):
        set_keymap('MAYA')
        return {'FINISHED'}   
    
    
#========================================= panggil panel floating Save_Animation=========================== 
    
class FLOATING_OT_Open_Save_Animation(bpy.types.Operator):
    bl_idname = "floating.open_save_animation"
    bl_label = "Open_Save_Animation"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="OBJECT_PT_bone_keyframe", keep_open=True)  # Memanggil panel dari script kedua
        return {'FINISHED'}       
      
 
#========================================= panggil panel floating import animation =========================== 
    
class FLOATING_OT_Open_Import_Animation(bpy.types.Operator):
    bl_idname = "floating.open_import_animation"
    bl_label = "Open_import_Animation"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="VIDEO_PT_Browser", keep_open=True)  # Memanggil panel dari script kedua
        return {'FINISHED'}     
    
#========================================= panggil panel floating Library pose =========================== 
    
class FLOATING_OT_Open_panel_POSE_LIB(bpy.types.Operator):
    bl_idname = "floating.open_panel_pose_lib"
    bl_label = "Open_import_pose_lib"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="PT_BonePose", keep_open=True)  # Memanggil panel dari script kedua
        return {'FINISHED'}  
    
#========================================= panggil panel floating Child-of =========================== 
    
class FLOATING_OT_Open_panel_childof(bpy.types.Operator):
    bl_idname = "floating.open_childof"
    bl_label = "open_Open_childof"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="VIEW3D_PT_Raha_Parents", keep_open=True)  
        return {'FINISHED'}      
    
#========================================= panggil panel floating Locrote =========================== 
    
class FLOATING_OT_Open_panel_Locrote(bpy.types.Operator):
    bl_idname = "floating.open_locrote"
    bl_label = "open_Open_locrote"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="VIEW3D_PT_Raha_Parents_Locrote", keep_open=True)  

        return {'FINISHED'}          

#========================================= panggil panel Smart Bake =========================== 
    
class FLOATING_OT_Open_Smart_Bake(bpy.types.Operator):
    bl_idname = "floating.open_smart_bake"
    bl_label = "open_smart_bake"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="OBJECT_PT_bone_bake", keep_open=True)  
        return {'FINISHED'}   
#========================================= panggil panel Fake constraint - Step Snap =========================== 
    
class FLOATING_OT_Open_Fake_Step(bpy.types.Operator):
    bl_idname = "floating.open_fake_step"
    bl_label = "open_fake_step"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="OBJECT_PT_bone_matrix", keep_open=True)  
        return {'FINISHED'}         
    
#========================================= panggil panel VIEW3D_PT_mini_tools =========================== 
    
class FLOATING_OT_Open_Mini_tools(bpy.types.Operator):
    bl_idname = "floating.open_mini_tools"
    bl_label = "open_mini_tools"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="VIEW3D_PT_mini_tools", keep_open=True)  
        return {'FINISHED'}     
      

#========================================= panggil panel Playblast + HUD =========================== 
    
class FLOATING_OT_Open__Pb_Hud(bpy.types.Operator):
    bl_idname = "floating.open_pb_hud"
    bl_label = "open_pb_hud"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="RAHA_PT_Tools_playblast", keep_open=True)  
        return {'FINISHED'}       
                           
#============================================== Register ========================================    
def register():
    
    global preview_collections
    bpy.types.Scene.show_tween_machine = bpy.props.BoolProperty(
        name="Show Tween Machine", 
        description="Tampilkan tombol Tween Machine", 
        default=False
    )      
    
    bpy.types.PoseBone.copy_constraints_influence = bpy.props.FloatProperty(
        name="Copy Constraints Influence",
        description="Control the influence of both Copy Location and Copy Rotation constraints",
        default=1.0,
        min=0.0,
        max=1.0,
        update=update_constraints_influence
    
    )


    # Pastikan koleksi preview sudah ada
    global preview_collections
    preview_collections["raha_previews"] = bpy.utils.previews.new()

    # Dapatkan path direktori tempat script ini berada
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Path ke ikon dalam folder yang sama dengan script
    icon_path = os.path.join(script_dir, "ICORRSTUDIO.png")

    if os.path.exists(icon_path):
        preview_collections["raha_previews"].load("raha_icon", icon_path, 'IMAGE')


    bpy.utils.register_class(RAHA_OT_InfoPopup)
    bpy.utils.register_class(RAHA_OT_Donate)
    bpy.utils.register_class(RAHA_OT_Subscribe)      
    bpy.utils.register_class(RAHA_OT_RunTools)
    
    bpy.utils.register_class(SetBlenderKeymapOperator)  
    bpy.utils.register_class(SetMayaKeymapOperator)  
#========================== Animation library ===================
    bpy.utils.register_class(FLOATING_OT_Open_Save_Animation)          
    bpy.utils.register_class(FLOATING_OT_Open_Import_Animation) 
    bpy.utils.register_class(FLOATING_OT_Open_panel_POSE_LIB) 
#========================== childof dan locrote =============================    
    bpy.utils.register_class(FLOATING_OT_Open_panel_childof) 
    bpy.utils.register_class(FLOATING_OT_Open_panel_Locrote)

#========================== fake constraint dan step snap =============================      
    bpy.utils.register_class(FLOATING_OT_Open_Smart_Bake )
    bpy.utils.register_class(FLOATING_OT_Open_Fake_Step )    
    
#========================== FLOATING_OT_Open_Mini_tools =============================      
    bpy.utils.register_class(FLOATING_OT_Open_Mini_tools ) 
     
#========================== FLOATING_OT_Open__Pb_Hud =============================      
    bpy.utils.register_class(FLOATING_OT_Open__Pb_Hud )     
           
        
    
         
             
    bpy.utils.register_class(RAHA_PT_Tools_For_Animation)
     
    bpy.types.WindowManager.show_raha_tools_For_Animation = bpy.props.BoolProperty(default=False)
    
    download_image()


def unregister():
  
    
    bpy.utils.unregister_class(RAHA_OT_InfoPopup)
    bpy.utils.unregister_class(RAHA_OT_Donate)
    bpy.utils.unregister_class(RAHA_OT_Subscribe)    
    bpy.utils.unregister_class(RAHA_OT_RunTools)
    
    bpy.utils.unregister_class(SetBlenderKeymapOperator) 
    bpy.utils.unregister_class(SetMayaKeymapOperator)   
#========================== Animation library ====================
    bpy.utils.unregister_class(FLOATING_OT_Open_Save_Animation)  
    bpy.utils.unregister_class(FLOATING_OT_Open_Import_Animation) 
    bpy.utils.unregister_class(FLOATING_OT_Open_panel_POSE_LIB)   
#========================== child-of =============================     
    bpy.utils.unregister_class(FLOATING_OT_Open_panel_childof)  
    bpy.utils.unregister_class(FLOATING_OT_Open_panel_Locrote)     
    
#========================== fake constraint dan step snap =============================      

    bpy.utils.unregister_class(FLOATING_OT_Open_Smart_Bake )
    bpy.utils.unregister_class(FLOATING_OT_Open_Fake_Step )

#========================== FLOATING_OT_Open_Mini_tools =============================      
    bpy.utils.unregister_class(FLOATING_OT_Open_Mini_tools ) 
    
#========================== FLOATING_OT_Open__Pb_Hud =============================      
    bpy.utils.unregister_class(FLOATING_OT_Open__Pb_Hud )        
                      
       
    
    bpy.utils.unregister_class(RAHA_PT_Tools_For_Animation)
    del bpy.types.Scene.show_tween_machine

    if hasattr(bpy.types.WindowManager, "show_raha_tools_For_Animation"):
        delattr(bpy.types.WindowManager, "show_raha_tools_For_Animation")
    
    if "raha_previews" in preview_collections:
        bpy.utils.previews.remove(preview_collections["raha_previews"])
        del preview_collections["raha_previews"]

    if RAHA_PT_Tools_For_Animation.preview_collection:
        bpy.utils.previews.remove(RAHA_PT_Tools_For_Animation.preview_collection)
        RAHA_PT_Tools_For_Animation.preview_collection = None
        
if __name__ == "__main__":
    register()
