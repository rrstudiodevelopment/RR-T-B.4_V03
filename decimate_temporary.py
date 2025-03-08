bl_info = {
    "name": "Advanced Decimate Tools",
    "blender": (4, 0, 0),
    "category": "Object",
}

import bpy
from bpy.props import IntProperty, BoolProperty, CollectionProperty
from bpy.types import Operator, Panel, PropertyGroup

class OBJECT_OT_AddDecimate(Operator):
    """Menambahkan Decimate Modifier dengan Un-Subdivide pada semua mesh yang diseleksi"""
    bl_idname = "object.add_decimate"
    bl_label = "Add Decimate Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            print("Tools ini hanya berfungsi di Object Mode")
            return {'CANCELLED'}
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                modifier = obj.modifiers.new(name="Decimate_temporary", type='DECIMATE')
                modifier.decimate_type = 'UNSUBDIV'
                modifier.iterations = context.scene.decimate_iterations  # Menggunakan nilai user
                modifier.show_render = False
        return {'FINISHED'}

class OBJECT_OT_AdjustAllIterations(Operator):
    """Mengatur Iterations untuk semua Decimate_temporary di mesh yang dipilih"""
    bl_idname = "object.adjust_all_iterations"
    bl_label = "Adjust All Iterations"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            print("Tools ini hanya berfungsi di Object Mode")
            return {'CANCELLED'}
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod.name == "Decimate_temporary":
                        mod.iterations = context.scene.decimate_iterations
        return {'FINISHED'}

class OBJECT_OT_DeleteDecimate(Operator):
    """Menghapus modifier Decimate_temporary dari semua mesh yang diseleksi"""
    bl_idname = "object.delete_decimate"
    bl_label = "Delete Decimate Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            print("Tools ini hanya berfungsi di Object Mode")
            return {'CANCELLED'}
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod.name == "Decimate_temporary":
                        obj.modifiers.remove(mod)
        return {'FINISHED'}

class OBJECT_OT_ToggleViewport(Operator):
    """Toggle show_viewport dari Decimate_temporary"""
    bl_idname = "object.toggle_decimate_viewport"
    bl_label = "Toggle Decimate Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            print("Tools ini hanya berfungsi di Object Mode")
            return {'CANCELLED'}
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod.name == "Decimate_temporary":
                        mod.show_viewport = not mod.show_viewport
        return {'FINISHED'} 
    
   

class OBJECT_OT_ToggleParticle(Operator):
    """Toggle show_viewport dari Particle System Modifier"""
    bl_idname = "object.toggle_particle_viewport"
    bl_label = "Toggle Particle System Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            print("Tools ini hanya berfungsi di Object Mode")
            return {'CANCELLED'}
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod.type == 'PARTICLE_SYSTEM':
                        mod.show_viewport = not mod.show_viewport
        return {'FINISHED'}
    
class OBJECT_OT_RegisterMeshes(Operator):
    """Menyeleksi semua mesh yang memiliki Decimate_temporary"""
    bl_idname = "object.register_meshes"
    bl_label = "Select Registered Meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            print("Tools ini hanya berfungsi di Object Mode")
            return {'CANCELLED'}
        
        bpy.ops.object.select_all(action='DESELECT')
        
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and "Decimate_temporary" in [mod.name for mod in obj.modifiers]:
                obj.select_set(True)
        
        return {'FINISHED'}
    

    


class VIEW3D_PT_DecimatePanel(bpy.types.Panel):
    """Panel untuk kontrol Decimate Modifier"""
    bl_label = "Decimate_temporary"
    bl_idname = "VIEW3D_PT_decimate_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'    
    bl_ui_units_x = 10
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.separator()           
        layout.separator()              
        layout.prop(context.scene, "auto_delete_decimate")
        layout.prop(context.scene, "decimate_iterations")       
                
        row = layout.row()
        
        
        # Cek status show_viewport dari Decimate_temporary
        decimate_show_viewport = False
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod.name == "Decimate_temporary":
                        decimate_show_viewport = mod.show_viewport
                        break

        # Tentukan ikon untuk Decimate berdasarkan status show_viewport
        decimate_icon = 'HIDE_OFF' if decimate_show_viewport else 'HIDE_ON'
        
        # Tombol toggle Decimate dengan ikon yang sesuai
        row.operator("object.toggle_decimate_viewport", text="", icon=decimate_icon, depress=decimate_show_viewport)
        
        row.operator("object.add_decimate", text="Add")
        row.operator("object.delete_decimate", text="", icon='TRASH') 
         
        row = layout.row()
        row.operator("object.register_meshes", text="Select Mesh")         
        
        row = layout.row()
        
        # Cek status show_viewport dari Particle System Modifier
        particle_show_viewport = False
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod.type == 'PARTICLE_SYSTEM':
                        particle_show_viewport = mod.show_viewport
                        break
        
        # Tentukan ikon untuk Particle berdasarkan status show_viewport
        particle_icon = 'HIDE_OFF' if particle_show_viewport else 'HIDE_ON'
        
        # Tombol toggle Particle dengan ikon yang sesuai
#        row.operator("object.toggle_particle_viewport", text="Toggle Particle", icon=particle_icon, depress=particle_show_viewport)
               
        # Hanya tampilkan UI Adjust Iterations jika dalam Object Mode dan ada objek terpilih
        if context.selected_objects and context.mode == 'OBJECT':
            layout.label(text="Adjust Iterations:")           
            layout.prop(context.scene, "decimate_iterations", text="Iterations Main")  
            layout.operator("object.adjust_all_iterations", text="Apply All")  
            layout.separator()                                 
            for obj in context.selected_objects:
                if obj.type == 'MESH':  # Pastikan objek adalah mesh
                    for mod in obj.modifiers:
                        if mod.name == "Decimate_temporary":
                            layout.prop(mod, "iterations", text=f"{obj.name}")

class RegisteredMesh(PropertyGroup):
    name: bpy.props.StringProperty()

# Menambahkan properti untuk menyimpan nilai Iterations dan Auto-Delete
def register():
       
    
    bpy.utils.register_class(OBJECT_OT_AddDecimate)
    bpy.utils.register_class(OBJECT_OT_DeleteDecimate)
    bpy.utils.register_class(OBJECT_OT_ToggleViewport)
    bpy.utils.register_class(OBJECT_OT_ToggleParticle)    
    bpy.utils.register_class(OBJECT_OT_RegisterMeshes)
    bpy.utils.register_class(OBJECT_OT_AdjustAllIterations)
    bpy.utils.register_class(VIEW3D_PT_DecimatePanel)
    bpy.utils.register_class(RegisteredMesh)
    bpy.types.Scene.decimate_iterations = IntProperty(
        name="Iterations", 
        description="Jumlah Iterasi Un-Subdivide", 
        default=3,
        min=1,
        max=10
    )
    bpy.types.Scene.auto_delete_decimate = BoolProperty(
        name="Auto Delete on Save",
        description="Hapus semua Decimate_temporary saat menyimpan Blender",
        default=False
    )
    
    def auto_delete_handler(dummy):
        if bpy.context.scene.auto_delete_decimate:
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    for mod in obj.modifiers:
                        if mod.name == "Decimate_temporary":
                            obj.modifiers.remove(mod)

    bpy.app.handlers.save_pre.append(auto_delete_handler)

def unregister():
    bpy.utils.unregister_class(FLOATING_OT_Decimate_Temporary) 
        
    bpy.utils.unregister_class(OBJECT_OT_AddDecimate)
    bpy.utils.unregister_class(OBJECT_OT_DeleteDecimate)
    bpy.utils.unregister_class(OBJECT_OT_ToggleViewport)
    bpy.utils.unregister_class(OBJECT_OT_ToggleParticle)    
    bpy.utils.unregister_class(OBJECT_OT_RegisterMeshes)
    bpy.utils.unregister_class(OBJECT_OT_AdjustAllIterations)
    bpy.utils.unregister_class(VIEW3D_PT_DecimatePanel)
    bpy.utils.unregister_class(RegisteredMesh)
    del bpy.types.Scene.decimate_iterations
    del bpy.types.Scene.auto_delete_decimate

if __name__ == "__main__":
    register()
