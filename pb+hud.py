import bpy
import os
import subprocess

from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

def update_temp_resolution(self, context):
    scene = context.scene
    percentage = scene.temporary_resolution_percentage / 100
    scene.temp_res_x = int(scene.render.resolution_x * percentage)
    scene.temp_res_y = int(scene.render.resolution_y * percentage)


class AUDIO_OT_import(bpy.types.Operator, ImportHelper):
    """Import an audio file and set its start position"""
    bl_idname = "audio.import"
    bl_label = "Add Audio"
    
    filter_glob: StringProperty(
        default="*.wav;*.mp3;*.ogg",
        options={'HIDDEN'}
    )
    
    def execute(self, context):
        scene = context.scene
        audio_path = self.filepath
        
        # Remove existing sound strips
        for strip in scene.sequence_editor.sequences_all:
            if strip.type == 'SOUND':
                scene.sequence_editor.sequences.remove(strip)
                
        # Ensure sequence editor exists
        if not scene.sequence_editor:
            scene.sequence_editor_create()
        
        # Add the audio strip
        sound_strip = scene.sequence_editor.sequences.new_sound(
            name=os.path.basename(audio_path), 
            filepath=audio_path, 
            channel=1, 
            frame_start=scene.frame_start
        )
        
        scene.active_audio_name = sound_strip.name
        
        # Activate audio and enable waveform display
        bpy.context.scene.sequence_editor.active_strip = sound_strip
        bpy.context.active_sequence_strip.show_waveform = True
        
        # Set sync mode to AUDIO_SYNC
        bpy.context.scene.sync_mode = 'AUDIO_SYNC'
        
        return {'FINISHED'}

class AUDIO_OT_delete(bpy.types.Operator):
    """Delete the imported audio"""
    bl_idname = "audio.delete"
    bl_label = "Delete Audio"
    
    def execute(self, context):
        scene = context.scene
        
        if scene.sequence_editor:
            for strip in scene.sequence_editor.sequences_all:
                if strip.type == 'SOUND':
                    scene.sequence_editor.sequences.remove(strip)
                    scene.active_audio_name = "No Audio Imported"
                    break
        
        return {'FINISHED'}
    
#================================ HUD ============================================================
# Mengambil path ke direktori addon

# Dapatkan path addons dari Blender secara dinamis
ADDONS_PATH = bpy.utils.user_resource('SCRIPTS', path="addons")
DEFAULT_SAFE_AREA_IMAGE_PATH = os.path.join(ADDONS_PATH, "Raha_Tools_LAUNCHER", "safe_area.png")

class RAHA_OT_ActivateHUD(bpy.types.Operator):
    """Operator to activate HUD settings"""
    bl_idname = "raha.activate_hud"
    bl_label = "Activate HUD"

    def execute(self, context):
        scene = context.scene

        # Jika use_hud tidak dicentang, nonaktifkan background image dan hentikan eksekusi
        if not scene.use_hud:
            camera = bpy.context.scene.camera
            if camera and camera.data.background_images:
                for bg_image in camera.data.background_images:
                    bg_image.show_background_image = False
                                      
                    

            # Nonaktifkan stamp
            scene.render.use_stamp = False
            self.report({'INFO'}, "HUD is disabled. Background image hidden and stamps turned off.")
            return {'FINISHED'}

        bpy.ops.object.select_all(action='DESELECT')

        # Loop melalui semua objek di scene dan seleksi yang merupakan kamera
        for obj in bpy.data.objects:
            if obj.type == 'CAMERA':
                obj.select_set(True)

        # Set active object ke kamera pertama yang ditemukan (opsional)
        cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
        if cameras:
            bpy.context.view_layer.objects.active = cameras[0]

        # Atur stamp render
        scene.render.use_stamp = True
        scene.render.use_stamp_note = True
        scene.render.use_stamp_camera = False
        scene.render.use_stamp_render_time = False
        scene.render.use_stamp_time = False 
        scene.render.use_stamp_filename = False               
        scene.render.use_stamp_lens = True
        scene.render.stamp_font_size = 32

        # Menyembunyikan elemen overlay
        area = next((area for area in bpy.context.screen.areas if area.type == 'VIEW_3D'), None)
        if area:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.overlay.show_bones = False
                    space.overlay.show_cursor = False
                    space.overlay.show_extras = False
                    space.overlay.show_motion_paths = False
                    space.overlay.show_relationship_lines = False

        # Menambahkan background image ke kamera
        camera = bpy.context.scene.camera
        if camera:
            if not camera.data.background_images:
                bg_image = camera.data.background_images.new()
            else:
                bg_image = camera.data.background_images[0]

            # Gunakan path default jika custom path tidak dicentang
            if not scene.use_custom_safe_area_path:
                bg_image.image = bpy.data.images.load(DEFAULT_SAFE_AREA_IMAGE_PATH)
            else:
                # Gunakan custom path jika dicentang
                custom_path = scene.custom_safe_area_path
                if os.path.exists(custom_path):
                    bg_image.image = bpy.data.images.load(custom_path)
                else:
                    self.report({'ERROR'}, "Custom safe area image path does not exist.")
                    return {'CANCELLED'}

            bg_image.show_background_image = True
            bg_image.display_depth = 'FRONT'  # Menetapkan display depth ke 'FRONT'

        # Menampilkan background image pada objek aktif
        obj = bpy.context.object
        if obj and obj.type == 'CAMERA':  
            obj.data.show_background_images = True
            if obj.data.background_images:
                obj.data.background_images[0].display_depth = 'FRONT'  # Pastikan display depth diatur ke 'FRONT'

        self.report({'INFO'}, "HUD activated with specified settings and overlays hidden")
        return {'FINISHED'}


class VIEW3D_OT_ToggleSafeArea(bpy.types.Operator):
    """Toggle the visibility of the safe area overlay"""
    bl_idname = "view3d.toggle_safe_area"
    bl_label = "Toggle Safe Area"
    bl_icon = 'HIDE_OFF'  # Default icon mata terbuka

    def execute(self, context):
        scene = context.scene

        # Jika use_hud tidak dicentang, hentikan eksekusi
        if not scene.use_hud:
            self.report({'INFO'}, "HUD is disabled. No changes applied.")
            return {'FINISHED'}

        camera = bpy.context.scene.camera
        if not camera:
            self.report({'ERROR'}, "No active camera found in the scene.")
            return {'CANCELLED'}

        if camera.data.background_images:
            bg_image = camera.data.background_images[0]
            bg_image.show_background_image = not bg_image.show_background_image

            # Update icon berdasarkan kondisi
            if bg_image.show_background_image:
                self.bl_icon = 'HIDE_OFF'  # Mata terbuka
                # If background image is on, enable render stamp
                scene.render.use_stamp = True
                self.report({'INFO'}, "Render stamp enabled.")
            else:
                self.bl_icon = 'HIDE_ON'  # Mata tertutup
                # If background image is off, disable render stamp
                scene.render.use_stamp = False
                self.report({'INFO'}, "Render stamp disabled.")

            status = "on" if bg_image.show_background_image else "off"
            self.report({'INFO'}, f"Safe area background image turned {status}.")

        else:
            self.report({'ERROR'}, "No background images found on the active camera.")

        return {'FINISHED'}



class VIEW3D_OT_DeleteSafeAreaImage(bpy.types.Operator):
    """Delete the safe area background image from the camera"""
    bl_idname = "view3d.delete_safe_area_image"
    bl_label = "Delete Safe Area Image"
    bl_icon = 'X'  # Icon X

    def execute(self, context):
        camera = bpy.context.scene.camera
        if not camera:
            self.report({'ERROR'}, "No active camera found in the scene.")
            return {'CANCELLED'}

        if camera.data.background_images:
            # Hapus semua background images dari kamera
            camera.data.background_images.clear()
            # Refresh tampilan
            camera.data.show_background_images = False
            camera.data.show_background_images = True
            self.report({'INFO'}, "Safe area background image deleted and view refreshed.")
        else:
            self.report({'ERROR'}, "No background images found on the active camera.")

        return {'FINISHED'}

#================================================== PLAYBLAST ============================================
class VIEW3D_OT_Playblast(bpy.types.Operator):
    """Playblast the viewport with predefined settings"""
    bl_idname = "view3d.playblast"
    bl_label = "Viewport Playblast"

    def switch_workspace(self, workspace_name):
        """Pindah ke workspace yang ditentukan"""
        if workspace_name in bpy.data.workspaces:
            bpy.context.window.workspace = bpy.data.workspaces[workspace_name]
            print(f"Berpindah ke workspace: {workspace_name}")
        else:
            self.report({'WARNING'}, f"Workspace '{workspace_name}' tidak ditemukan! Silakan buat secara manual.")
    
    def execute(self, context):
        scene = context.scene
        
        # Simpan nilai asli start dan end frame
        original_start_frame = scene.frame_start
        original_end_frame = scene.frame_end
        
        # Jika checkbox dicentang, gunakan frame yang diatur
        if scene.use_custom_frame_range:
            scene.frame_start = scene.custom_start_frame
            scene.frame_end = scene.custom_end_frame
        
        self.switch_workspace("Animation")

        output_path = scene.playblast_output_path
        file_name = scene.playblast_file_name

        # Simpan resolusi asli scene
        original_resolution_x = scene.render.resolution_x
        original_resolution_y = scene.render.resolution_y
        original_resolution_percentage = scene.render.resolution_percentage

        # Inisialisasi default (gunakan resolusi asli)
        resolution_x = original_resolution_x
        resolution_y = original_resolution_y
        resolution_percentage = original_resolution_percentage

        # Jika gunakan resolusi sementara, hitung ulang
        if scene.use_temporary_resolution:
            resolution_percentage = scene.temporary_resolution_percentage
            resolution_x = int(original_resolution_x * (resolution_percentage / 100))
            resolution_y = int(original_resolution_y * (resolution_percentage / 100))

        # Jika use_temporary_resolution dicentang, gunakan persentase resolusi sementara
        if scene.use_temporary_resolution:
            bpy.context.scene.render.resolution_percentage = scene.temporary_resolution_percentage
        else:
            bpy.context.scene.render.resolution_percentage = original_resolution_percentage


        if not output_path:
            self.report({'ERROR'}, "Output path is not set. Please specify it in the Scene settings.")
            return {'CANCELLED'}
        if not file_name:
            self.report({'ERROR'}, "File name is not set. Please specify it in the Scene settings.")
            return {'CANCELLED'}
        if resolution_x <= 0 or resolution_y <= 0:
            self.report({'ERROR'}, "Invalid resolution values. Please set both width and height greater than 0.")
            return {'CANCELLED'}

        camera = scene.camera
        if not camera:
            self.report({'ERROR'}, "No active camera found in the scene. Please add and set a camera.")
            return {'CANCELLED'}

        # Atur overlay viewport
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_overlays = True
                        space.overlay.show_bones = False
                        space.overlay.show_object_origins = False
                        space.overlay.show_motion_paths = False
                        space.overlay.show_outline_selected = False
                        space.overlay.show_relationship_lines = False
                        space.overlay.show_extras = False
                        space.show_gizmo = False
                        space.overlay.show_viewer_attribute = False
                        space.show_reconstruction = False
                        space.overlay.show_annotation = False
                        space.overlay.show_cursor = False
                        space.overlay.show_text = False
                        space.region_3d.view_perspective = 'CAMERA'
                        
                        # Atur overlay viewport

        # Nonaktifkan ekstensi file otomatis
        scene.render.use_file_extension = False

        # Tentukan path output
        full_output_path = os.path.join(bpy.path.abspath(output_path), f"{file_name}.mp4")
        render = scene.render
        render.filepath = full_output_path
        render.resolution_x = resolution_x
        render.resolution_y = resolution_y
        render.image_settings.file_format = 'FFMPEG'
        render.ffmpeg.format = 'QUICKTIME'
        render.ffmpeg.audio_codec = 'AAC'

        # Render playblast
        bpy.ops.render.opengl(animation=True)

        # Kembalikan nilai start dan end frame ke aslinya setelah playblast selesai
        scene.frame_start = original_start_frame
        scene.frame_end = original_end_frame

        scene.frame_start = original_start_frame
        scene.frame_end = original_end_frame
        scene.render.resolution_x = original_resolution_x
        scene.render.resolution_y = original_resolution_y
        scene.render.resolution_percentage = original_resolution_percentage
        
        # Buka file yang telah dirender
        try:
            if os.path.exists(full_output_path):
                if os.name == 'nt':  # Windows
                    os.startfile(full_output_path)
                elif os.name == 'posix':  # macOS/Linux
                    subprocess.call(('xdg-open', full_output_path))
                else:
                    self.report({'WARNING'}, "Could not determine OS to open the video file.")
            else:
                self.report({'ERROR'}, f"Rendered file not found at {full_output_path}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open the video file: {e}")
        
        self.report({'INFO'}, f"Playblast saved to {full_output_path}")
        
        return {'FINISHED'}

#============================================== Tombol Panel =============================================
class VIEW3D_PT_PlayblastPanel(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport"""
    bl_label = "Playblast HUD"
    bl_idname = "RAHA_PT_Tools_playblast"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'    
    bl_ui_units_x = 10

    def draw(self, context):
        layout = self.layout
        scene = context.scene
#====================================================== Panel Add Audio ===================================
        # Checkbox untuk mengaktifkan/menonaktifkan HUD
        layout.prop(scene, "add_audio", text="Add Audio")

        # Jika HUD diaktifkan, tampilkan opsi HUD
        if scene.add_audio:
            layout.label(text=f"Active Audio: {scene.active_audio_name}")
            row = layout.row()
            row.operator("audio.import", text="Add Audio")
    #        row.operator("audio.delete", text="Delete Audio")
            row.operator("audio.delete", text="Delete", icon='TRASH')
#===================================================== Panel Hud ========================================            
        # Checkbox untuk mengaktifkan/menonaktifkan HUD
        layout.prop(scene, "use_hud", text="Use HUD")

        # Jika HUD diaktifkan, tampilkan opsi HUD
        if scene.use_hud:
            layout.label(text="HUD ===========") 
            # Input for Scene Name
            layout.prop(scene, "name", text="Scene Name")

            # Input for Animator Name
            layout.prop(scene.render, "stamp_note_text", text="Animator Name")
            
            layout.prop(scene, "use_custom_safe_area_path", text="Use Custom Safe Area Path")
            if scene.use_custom_safe_area_path:
                layout.prop(scene, "custom_safe_area_path", text="Safe Area Image")
            
            # Tombol Activate HUD, Toggle Safe Area, dan Delete Safe Area (berdampingan horizontal)
            row = layout.row()
            row.operator("raha.activate_hud", text="Activate HUD")
            row.operator("view3d.toggle_safe_area", text="", icon='HIDE_OFF')  # Icon mata
            row.operator("view3d.delete_safe_area_image", text="", icon='X')  # Icon X

#============================================ Panel Playblast ==============================================
        layout.prop(scene, "use_pb", text="Use Playblast")
        if scene.use_pb:  # Tetap gunakan scene.use_pb
                # Tampilkan opsi Playblast            
            layout.label(text="Playblast ===========")  
            layout.prop(scene, "playblast_output_path", text="Output Path")
            layout.prop(scene, "playblast_file_name", text="File Name")
            
            # Checkbox untuk menggunakan resolusi sementara
            layout.prop(scene, "use_temporary_resolution", text="Use Temporary Resolution")

            if scene.use_temporary_resolution:
                layout.prop(scene, "temporary_resolution_percentage", text="Resolution Percentage", slider=True)
                layout.label(text=f"Output Resolution: {scene.temp_res_x} x {scene.temp_res_y}")

                        
                layout.separator()
                
            layout.prop(scene, "use_custom_frame_range", text="Use Custom Frame Range")
            if scene.use_custom_frame_range:
                layout.prop(scene, "custom_start_frame", text="Start Frame")
                layout.prop(scene, "custom_end_frame", text="End Frame")
                
            layout.separator()
            layout.operator("view3d.playblast", text="PLAYBLAST")
            layout.separator()
        

classes = [
    VIEW3D_OT_Playblast,
    VIEW3D_PT_PlayblastPanel,
    RAHA_OT_ActivateHUD,
    VIEW3D_OT_ToggleSafeArea,
    AUDIO_OT_import,
    AUDIO_OT_delete,
    VIEW3D_OT_DeleteSafeAreaImage    
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.temporary_resolution_percentage = bpy.props.IntProperty(
    name="Resolution Percentage",
    description="Set temporary resolution percentage for playblast",
    default=100,
    min=1,
    max=100,
    update=update_temp_resolution  # Otomatis update saat nilai berubah
)


    bpy.types.Scene.temp_res_x = bpy.props.IntProperty(name="Temp Res X")
    bpy.types.Scene.temp_res_y = bpy.props.IntProperty(name="Temp Res Y")
    
    bpy.types.Scene.active_audio_name = StringProperty(default="No Audio Imported")        
    bpy.types.Scene.add_audio = bpy.props.BoolProperty(name="Add Audio", default=False)        
    bpy.types.Scene.use_hud = bpy.props.BoolProperty(name="Use HUD", default=False)
    bpy.types.Scene.use_pb = bpy.props.BoolProperty(name="Use Playblast", default=False)      # Default tidak tercentang
    bpy.types.Scene.use_custom_safe_area_path = bpy.props.BoolProperty(name="Use Custom Safe Area Path", default=False)
    bpy.types.Scene.custom_safe_area_path = bpy.props.StringProperty(name="Custom Safe Area Path", subtype='FILE_PATH')
    bpy.types.Scene.playblast_output_path = bpy.props.StringProperty(name="Output Path", subtype='DIR_PATH')
    bpy.types.Scene.playblast_file_name = bpy.props.StringProperty(name="File Name")
    bpy.types.Scene.use_temporary_resolution = bpy.props.BoolProperty(name="Use Temporary Resolution", default=False)
    bpy.types.Scene.temporary_resolution_x = bpy.props.IntProperty(name="Temporary Resolution X", default=1920)
    bpy.types.Scene.temporary_resolution_y = bpy.props.IntProperty(name="Temporary Resolution Y", default=1080)
    bpy.types.Scene.use_custom_frame_range = bpy.props.BoolProperty(name="Use Custom Frame Range", default=False)
    bpy.types.Scene.custom_start_frame = bpy.props.IntProperty(name="Custom Start Frame", default=1)
    bpy.types.Scene.custom_end_frame = bpy.props.IntProperty(name="Custom End Frame", default=250)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.use_hud
    del bpy.types.Scene.playblast_output_path
    del bpy.types.Scene.playblast_file_name
    del bpy.types.Scene.use_temporary_resolution
    del bpy.types.Scene.temporary_resolution_x
    del bpy.types.Scene.temporary_resolution_y
    del bpy.types.Scene.use_custom_frame_range
    del bpy.types.Scene.custom_start_frame
    del bpy.types.Scene.custom_end_frame
    del bpy.types.Scene.active_audio_name
    
if __name__ == "__main__":
    register()
