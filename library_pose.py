import os
import ast  # Tambahkan ini
import bpy
from bpy.types import Operator

import bpy
import json
import os
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from bpy.types import Operator, Panel
from bpy.utils import previews

# Global variables for image previews
_icons = None
_image_paths = []

# Function to load images from a custom path
def load_images_from_path(path):
    global _image_paths
    _image_paths.clear()
    
    if os.path.exists(path) and os.path.isdir(path):
        for file in os.listdir(path):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                _image_paths.append((file, file, "", load_preview_icon(os.path.join(path, file))))


# Function to load a preview icon
def load_preview_icon(path):
    global _icons
    if path not in _icons:
        if os.path.exists(path):
            _icons.load(path, path, "IMAGE")
        else:
            return 0
    return _icons[path].icon_id

#=================================== rename ================================================
# Enum property for the images 
def sna_images_enum_items(self, context):
    return [(item[0], item[1], item[2], item[3], i) for i, item in enumerate(_image_paths)]

# Update function for the custom path property
def sna_update_custom_path(self, context):
    custom_path = bpy.context.scene.sna_custom_path
    load_images_from_path(custom_path)

class RenameImageAndScript(Operator):
    bl_idname = "wm.rename_image_and_script"
    bl_label = "Rename Image and Script"
    
    new_name: StringProperty(
        name="New Name",
        description="New name for the image and script",
        default=""
    )

    def invoke(self, context, event):
        selected_image = context.scene.sna_images
        if not selected_image:
            self.report({'WARNING'}, "No image selected.")
            return {'CANCELLED'}

        self.new_name = os.path.splitext(selected_image)[0]
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        selected_image = context.scene.sna_images
        if not selected_image:
            self.report({'WARNING'}, "No image selected.")
            return {'CANCELLED'}

        custom_path = context.scene.sna_custom_path
        if not custom_path:
            self.report({'ERROR'}, "No folder selected.")
            return {'CANCELLED'}

        old_name = os.path.splitext(selected_image)[0]
        new_name = self.new_name

        # Path untuk gambar lama dan baru
        old_image_path = os.path.join(custom_path, selected_image)
        new_image_path = os.path.join(custom_path, f"{new_name}.png")

        # Path untuk script lama dan baru
        data_pose_folder = os.path.join(custom_path, "data_pose")
        old_script_path = os.path.join(data_pose_folder, f"{old_name}.py")
        new_script_path = os.path.join(data_pose_folder, f"{new_name}.py")

        # Rename gambar
        if os.path.exists(old_image_path):
            try:
                os.rename(old_image_path, new_image_path)
                self.report({'INFO'}, f"Renamed image: {old_image_path} to {new_image_path}")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to rename image: {str(e)}")
        else:
            self.report({'WARNING'}, f"No matching image found: {old_image_path}")

        # Rename script
        if os.path.exists(old_script_path):
            try:
                os.rename(old_script_path, new_script_path)
                self.report({'INFO'}, f"Renamed script: {old_script_path} to {new_script_path}")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to rename script: {str(e)}")
        else:
            self.report({'WARNING'}, f"No matching script found: {old_script_path}")

        # Refresh daftar gambar
        self.refresh_images(context)

        return {'FINISHED'}

    def refresh_images(self, context):
        """Memuat ulang daftar gambar setelah rename."""
        custom_path = context.scene.sna_custom_path
        
        if custom_path and os.path.isdir(custom_path):
            load_images_from_path(custom_path)  # Reload daftar gambar
            self.report({'INFO'}, "Image list refreshed.")
        else:
            self.report({'ERROR'}, "Invalid or no folder selected.")
                
#===================================================================================================
# Operator to refresh the image list
class WM_OT_RefreshImageList(bpy.types.Operator):
    bl_idname = "wm.refresh_image_list"
    bl_label = "Refresh Image List"
    bl_description = "Refresh the list of images in the selected folder"
    
    def execute(self, context):
        custom_path = context.scene.sna_custom_path
        
        if custom_path and os.path.isdir(custom_path):
            load_images_from_path(custom_path)  # Reload images from the custom path
            self.report({'INFO'}, "Image list refreshed.")
        else:
            self.report({'ERROR'}, "Invalid or no folder selected.")
        
        return {'FINISHED'}
#===============================================================================================    


#===================================================================================================

class DeleteBonePose(Operator):
    bl_idname = "delete.bone_pose"
    bl_label = "Delete Bone Pose"
    filename_ext = ".png"  # Menerima file PNG untuk dipilih
    
    def execute(self, context):        
        selected_image = context.scene.sna_images
        if not selected_image:
            self.report({'WARNING'}, "No image selected.")
            return {'CANCELLED'}

        custom_path = context.scene.sna_custom_path
        if not custom_path:
            self.report({'ERROR'}, "No folder selected.")
            return {'CANCELLED'}

        image_name = os.path.splitext(selected_image)[0]
        data_pose_folder = os.path.join(custom_path, "data_pose")  # Menentukan folder data_pose
        script_path = os.path.join(data_pose_folder, f"{image_name}.py")  # Path skrip
        image_path = os.path.join(custom_path, selected_image)  # Path gambar

        # Hapus file skrip jika ada
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
                self.report({'INFO'}, f"Deleted script: {script_path}")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to delete script: {str(e)}")
        else:
            self.report({'WARNING'}, f"No matching script found for image: {image_name}")

        # Hapus file gambar jika ada
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
                self.report({'INFO'}, f"Deleted image: {image_path}")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to delete image: {str(e)}")
        else:
            self.report({'WARNING'}, f"No matching image found: {image_path}")

        # Refresh daftar gambar
        self.refresh_images(context)  # Panggil metode refresh setelah delete

        return {'FINISHED'}
    
    def refresh_images(self, context):
        """Memuat ulang daftar gambar setelah penghapusan."""
        custom_path = context.scene.sna_custom_path
        
        if custom_path and os.path.isdir(custom_path):
            load_images_from_path(custom_path)  # Reload daftar gambar
            self.report({'INFO'}, "Image list refreshed.")
        else:
            self.report({'ERROR'}, "Invalid or no folder selected.")


#===================================================================================================

def flip_selected_pose(context):
    """Flip the pose for selected bones"""
    try:
        bpy.ops.pose.copy()  # Copy selected pose
        bpy.ops.pose.paste(flipped=True)  # Paste flipped pose
    except RuntimeError:
        context.report({'WARNING'}, "Flip Pose failed. Ensure you're in Pose Mode and bones are selected.")

def serialize_custom_properties(bone):
    custom_props = {}
    for prop_name in bone.keys():
        if prop_name == "rigify_parameters":  # Skip rigify_parameters
            continue

        value = bone[prop_name]

        # Skip Blender internal object references
        if isinstance(value, bpy.types.ID) or "<bpy id prop" in str(value):
            continue

        if isinstance(value, (int, float, str)):
            custom_props[prop_name] = value

    return custom_props if custom_props else None  # Return None if empty

class ExportBonePose(Operator):
    bl_idname = "export.bone_pose"
    bl_label = "Export Bone Pose"
    bl_options = {'REGISTER', 'UNDO'}

    # Add a StringProperty for the file name
    file_name: StringProperty(
        name="File Name",
        description="Name of the exported pose file",
        default="NewPose"
    )

    def invoke(self, context, event):
        # Open a pop-up to ask for the file name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'ARMATURE':
            self.report({'WARNING'}, "Select an armature in pose mode.")
            return {'CANCELLED'}

        bones = context.selected_pose_bones
        if not bones:
            self.report({'WARNING'}, "No bones selected.")
            return {'CANCELLED'}
        
        registered_bones = [bone.name for bone in bones]  # Hanya tulang yang terpilih
        bone_data = {}

        for bone in bones:
            custom_props = serialize_custom_properties(bone)
            bone_info = {
                "location": list(bone.location),
                "rotation_quaternion": list(bone.rotation_quaternion),
                "rotation_euler": list(bone.rotation_euler),
                "scale": list(bone.scale)
            }
            if custom_props:  # Only add if there are custom properties
                bone_info["custom_properties"] = custom_props

            bone_data[bone.name] = bone_info

        custom_path = context.scene.sna_custom_path
        if not custom_path:
            self.report({'ERROR'}, "No folder selected.")
            return {'CANCELLED'}

        # Use the file name provided by the user
        pose_name = self.file_name
        data_pose_folder = os.path.join(custom_path, "data_pose")
        if not os.path.exists(data_pose_folder):
            os.makedirs(data_pose_folder)
        
        script_path = os.path.join(data_pose_folder, f"{pose_name}.py")
        image_path = os.path.join(custom_path, f"{pose_name}.png")

        script_content = f"""
import bpy
import json

def apply_bone_pose():
    obj = bpy.context.object
    if obj is None or obj.type != 'ARMATURE':
        print("No armature selected.")
        return
    
    registered_bones = {json.dumps(registered_bones, indent=4)}
    bone_data = {json.dumps(bone_data, indent=4)}

    selected_bones = [bone.name for bone in bpy.context.selected_pose_bones]
    matched_bones = {{}}

    for bone_name, data in bone_data.items():
        if bone_name in selected_bones:
            matched_bones[bone_name] = data

    if not matched_bones:
        print("No matching bones found.")
        return

    for bone_name, data in matched_bones.items():
        bone = obj.pose.bones.get(bone_name)
        if bone:
            bone.location = data["location"]
            bone.rotation_quaternion = data["rotation_quaternion"]
            bone.rotation_euler = data["rotation_euler"]
            bone.scale = data["scale"]
            if "custom_properties" in data:
                for prop, value in data["custom_properties"].items():
                    bone[prop] = value
                                     

apply_bone_pose()
"""
        script_content = script_content.replace("true", "True").replace("false", "False")

        with open(script_path, 'w') as file:
            file.write(script_content)

        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.filepath = image_path
        bpy.ops.render.view_show()
        bpy.ops.render.opengl(write_still=True)

        self.report({'INFO'}, f"Bone pose exported as script: {script_path} and image: {image_path}")

        return {'FINISHED'}

# Operator to import bone pose
class ImportBonePose(Operator):
    bl_idname = "import.bone_pose"
    bl_label = "Import Bone Pose"

    def execute(self, context):
        selected_image = context.scene.sna_images
        if not selected_image:
            self.report({'WARNING'}, "No image selected.")
            return {'CANCELLED'}

        custom_path = context.scene.sna_custom_path
        if not custom_path:
            self.report({'ERROR'}, "No folder selected.")
            return {'CANCELLED'}

        image_name = os.path.splitext(selected_image)[0]
        script_path = os.path.join(custom_path, "data_pose", f"{image_name}.py")

        if os.path.exists(script_path):
            with open(script_path, "r") as file:
                exec(file.read(), globals())
            self.report({'INFO'}, f"Executed script: {script_path}")
        else:
            self.report({'WARNING'}, f"No matching script found: {script_path}")
            return {'CANCELLED'}
        
        if context.scene.set_keyframes:
            self.insert_keyframes(context)
            self.report({'INFO'}, "Keyframes inserted after importing pose.")
            
        return {'FINISHED'}
    
    def insert_keyframes(self, context):
        obj = context.object
        if obj and obj.type == 'ARMATURE':
            current_frame = context.scene.frame_current
            for bone in context.selected_pose_bones:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.anim.keyframe_insert_by_name(type="LocRotScaleCProp")

    def apply_bone_pose(self):
        obj = bpy.context.object
        if obj is None or obj.type != 'ARMATURE':
            print("No armature selected.")
            return

        bone_data = {json.dumps(bone_data, indent=4)}
        selected_bones = [bone.name for bone in bpy.context.selected_pose_bones]
        matched_bones = {}

        for bone_name, data in bone_data.items():
            if bone_name in selected_bones:
                matched_bones[bone_name] = data

        if not matched_bones:
            print("No matching bones found.")
            return

        for bone_name, data in matched_bones.items():
            bone = obj.pose.bones.get(bone_name)
            if bone:
                # Hindari mengganti rigify_parameters dan properti khusus lainnya
                if 'rigify_parameters' not in data['custom_properties']:
                    bone.location = data["location"]
                    bone.rotation_quaternion = data["rotation_quaternion"]
                    bone.rotation_euler = data["rotation_euler"]
                    bone.scale = data["scale"]
                    for prop, value in data["custom_properties"].items():
                        if prop != 'bbdObject':  # Menghindari mengganti properti ID
                            bone[prop] = value
                else:
                    print(f"Skipping 'rigify_parameters' for bone: {bone_name}")

        return {'FINISHED'}

#=============================================================================================

class SelectBonesFromScript(Operator):
    bl_idname = "pose.select_bones_from_script"
    bl_label = "Select Bones from Script"

    def execute(self, context):
        selected_image = context.scene.sna_images
        if not selected_image:
            self.report({'WARNING'}, "No image selected.")
            return {'CANCELLED'}

        custom_path = context.scene.sna_custom_path
        if not custom_path:
            self.report({'ERROR'}, "No folder selected.")
            return {'CANCELLED'}

        image_name = os.path.splitext(selected_image)[0]
        script_path = os.path.join(custom_path, "data_pose", f"{image_name}.py")

        if not os.path.exists(script_path):
            self.report({'WARNING'}, f"No matching script found: {script_path}")
            return {'CANCELLED'}

        with open(script_path, "r") as file:
            script_content = file.read()

        # Parse script to extract registered_bones
        registered_bones = []
        try:
            tree = ast.parse(script_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "registered_bones":
                            if isinstance(node.value, ast.List):
                                registered_bones = [elt.s for elt in node.value.elts if isinstance(elt, ast.Str)]
        except Exception as e:
            self.report({'ERROR'}, f"Failed to parse script: {str(e)}")
            return {'CANCELLED'}

        if not registered_bones:
            self.report({'WARNING'}, "No registered bones found in the script.")
            return {'CANCELLED'}

        obj = context.object
        if obj is None or obj.type != 'ARMATURE':
            self.report({'WARNING'}, "No armature selected.")
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')

        selected_count = 0
        for bone_name in registered_bones:
            bone = obj.pose.bones.get(bone_name)
            if bone:
                bone.bone.select = True
                self.report({'INFO'}, f"Selected bone: {bone_name}")
                selected_count += 1
            else:
                self.report({'WARNING'}, f"Bone not found: {bone_name}")

        if selected_count == 0:
            self.report({'WARNING'}, "No registered bones found in the armature.")
            return {'CANCELLED'}

        return {'FINISHED'}


#======== Value slider ===================================================================

class ApplyPercentageOperator(bpy.types.Operator):
    bl_idname = "pose.apply_percentage"
    bl_label = "Apply Percentage to Bones"
    
    def execute(self, context):
        armature = context.object
        
        # Pastikan objek adalah armature
        if armature.type != 'ARMATURE':
            self.report({'WARNING'}, "Selected object is not an armature")
            return {'CANCELLED'}
        
        percentage = context.scene.percentage_value / 100  # Konversi persentase menjadi rasio
        calc_location = context.scene.calc_location
        calc_rotation = context.scene.calc_rotation
        calc_scale = context.scene.calc_scale
        calc_custom_property = context.scene.calc_custom_property
        
        # Iterasi setiap bone yang terseleksi
        for bone in armature.pose.bones:
            if bone.bone.select:
                # Kalkulasi dan modifikasi data asli bone (bukan data objek)
                
                if calc_location:
                    # Lokasi bone (transformasi relatif)
                    bone.location.x *= percentage
                    bone.location.y *= percentage
                    bone.location.z *= percentage

                if calc_rotation:
                    # Rotasi bone (Euler)
                    bone.rotation_euler.x *= percentage
                    bone.rotation_euler.y *= percentage
                    bone.rotation_euler.z *= percentage

                    # Rotasi bone (Quaternion)
                    bone.rotation_quaternion.x *= percentage
                    bone.rotation_quaternion.y *= percentage
                    bone.rotation_quaternion.z *= percentage
                    bone.rotation_quaternion.w *= percentage

                if calc_scale:
                    # Skala bone
                    bone.scale.x *= percentage
                    bone.scale.y *= percentage
                    bone.scale.z *= percentage

                if calc_custom_property:
                    # Kalkulasi custom property jika ada
                    for prop_name in bone.keys():
                        if prop_name != "_RNA_UI":  # Menghindari modifikasi metadata internal
                            current_value = bone[prop_name]
                            bone[prop_name] = current_value * percentage
        
        # Set keyframe sesuai dengan kategori yang dipilih
        bpy.ops.anim.keyframe_insert_by_name(type="LocRotScaleCProp")
        
        return {'FINISHED'}

#========================================================================================    
class OBJECT_OT_FlipPoseOperator(bpy.types.Operator):
    """Flip the current pose"""
    bl_idname = "object.flip_pose"
    bl_label = "Flip Pose"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'ARMATURE' or obj.mode != 'POSE':
            self.report({'WARNING'}, "Flip Pose failed. Ensure an armature is selected and you're in Pose Mode.")
            return {'CANCELLED'}
        
        flip_selected_pose(context)
        return {'FINISHED'}

#=====================================================================================================

class Raha_tombol_panel_POSE_LIB(bpy.types.Panel):
    bl_label = "Bone Pose Export/Import"
    bl_idname = "PT_BonePose"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 10

    def draw(self, context):
        layout = self.layout
        layout.label(text="POSE LIBRARY")

        # Image Browser
        layout.prop(context.scene, 'sna_custom_path', text="Folder")
        layout.template_icon_view(context.scene, 'sna_images', show_labels=True, scale=5.0, scale_popup=5.0)
        row = layout.row()
        row.operator("wm.refresh_image_list", text="", icon='FILE_REFRESH')
                    
        row.operator("pose.select_bones_from_script", text="Select Bones") 
        row.operator("delete.bone_pose", text="", icon="TRASH")                


        row = layout.row()              
        row.operator("export.bone_pose", text="Export Pose")      
        row.operator("import.bone_pose", text="Import Pose")
        row = layout.row()         
        row.operator("wm.rename_image_and_script", text="Rename")        
        
        layout.prop(context.scene, "set_keyframes", text="Auto Set Keyframes")      


        row = layout.row()        
        # Menambahkan panel Percentage
        row = layout.row()        
        row.prop(context.scene, "percentage_value", text="Percentage (%)")
        row = layout.row()          
        row.operator("pose.apply_percentage", text="Apply Percentage")         
        
        row = layout.row()
        # Checkbox untuk memilih apakah Location, Rotation, Scale, dan Custom Property yang ingin dihitung
        row.prop(context.scene, "calc_location", text="Location")
        row.prop(context.scene, "calc_rotation", text="Rotation")
        row.prop(context.scene, "calc_scale", text="Scale")
        row.prop(context.scene, "calc_custom_property", text="Custom Properties")
        # Tombol Apply
        layout.operator("object.flip_pose", text="Flip Pose")              

#=====================================================================================================

def register():
    global _icons
    _icons = previews.new()

    bpy.utils.register_class(ExportBonePose)
    bpy.utils.register_class(ImportBonePose)
    bpy.utils.register_class(SelectBonesFromScript)
    bpy.utils.register_class(WM_OT_RefreshImageList)
    bpy.utils.register_class(RenameImageAndScript)
        
#    bpy.utils.register_class(ExportBonePose)
#    bpy.utils.register_class(ImportBonePose)
    bpy.utils.register_class(OBJECT_OT_FlipPoseOperator)    
    bpy.utils.register_class(Raha_tombol_panel_POSE_LIB)
    bpy.utils.register_class(DeleteBonePose)
    bpy.utils.register_class(ApplyPercentageOperator)
#    bpy.utils.register_class(WM_OT_RefreshImageList)
#    bpy.utils.register_class(IMAGE_PT_Browser)
    
    # Menambahkan properti untuk persen
    bpy.types.Scene.percentage_value = bpy.props.FloatProperty(name="Percentage", default=50)
    
    # Menambahkan properti untuk checkbox
    bpy.types.Scene.calc_location = bpy.props.BoolProperty(name="Location", default=True)
    bpy.types.Scene.calc_rotation = bpy.props.BoolProperty(name="Rotation", default=True)
    bpy.types.Scene.calc_scale = bpy.props.BoolProperty(name="Scale", default=True)
    bpy.types.Scene.calc_custom_property = bpy.props.BoolProperty(name="Custom Properties", default=True)    
    bpy.types.Scene.set_keyframes = BoolProperty(name="Set Keyframes")
    
    # Properties
    bpy.types.Scene.sna_custom_path = StringProperty(
        name="Custom Path",
        description="Path to the folder containing images",
        default="",
        subtype='DIR_PATH',
        update=sna_update_custom_path
    )
    
    bpy.types.Scene.sna_images = EnumProperty(
        name="Images",
        description="List of images in the selected folder",
        items=sna_images_enum_items
    )

def unregister():
    global _icons
    previews.remove(_icons)
    
    bpy.utils.unregister_class(ExportBonePose)
    bpy.utils.unregister_class(ImportBonePose)
    bpy.utils.unregister_class(SelectBonesFromScript)
    bpy.utils.unregister_class(WM_OT_RefreshImageList)
    bpy.utils.unregister_class(RenameImageAndScript)    
    bpy.utils.unregister_class(POSE_LIB_PT_Panel)    
    
    bpy.utils.unregister_class(ExportBonePose)
    bpy.utils.unregister_class(ImportBonePose)
    bpy.utils.unregister_class(OBJECT_OT_FlipPoseOperator)      
    bpy.utils.unregister_class(Raha_tombol_panel_POSE_LIB)
    bpy.utils.unregister_class(DeleteBonePose)
    bpy.utils.unregister_class(ApplyPercentageOperator)
    bpy.utils.unregister_class(WM_OT_RefreshImageList)
    bpy.utils.unregister_class(IMAGE_PT_Browser)
    
    del bpy.types.Scene.script_folder_path
    del bpy.types.Scene.set_keyframes
    del bpy.types.Scene.percentage_value
    del bpy.types.Scene.calc_location
    del bpy.types.Scene.calc_rotation
    del bpy.types.Scene.calc_scale
    del bpy.types.Scene.calc_custom_property
    del bpy.types.Scene.sna_custom_path
    del bpy.types.Scene.sna_images

if __name__ == "__main__":
    register()