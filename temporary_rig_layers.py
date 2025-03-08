import bpy

#===================== Isolate view ========================================================== 
class VIEW3D_OT_isolate_toggle(bpy.types.Operator):
    bl_idname = "view3d.isolate_toggle"
    bl_label = "Toggle Isolate View"
    bl_description = "Isolate selected object or bone, toggle to reveal"
    bl_options = {'REGISTER', 'UNDO'}

    is_hidden: bpy.props.BoolProperty(default=False)
    
    def execute(self, context):
        obj = context.active_object
        mode = context.object.mode if obj else 'OBJECT'
        
        if mode == 'POSE':  # Pose Mode
            if self.is_hidden:
                bpy.ops.pose.reveal()
            else:
                bpy.ops.pose.hide(unselected=True)
        else:  # Object Mode
            if self.is_hidden:
                bpy.ops.object.hide_view_clear()
            else:
                bpy.ops.object.hide_view_set(unselected=True)
        
        self.is_hidden = not self.is_hidden  # Toggle state
        return {'FINISHED'}

#========== Class untuk menyimpan daftar objek yang disimpan sementara =======================
class TemporaryRigLayer(bpy.types.PropertyGroup):
    """Class untuk menyimpan daftar objek yang disimpan sementara."""
    name: bpy.props.StringProperty(name="Layer Name")
    items: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    is_visible: bpy.props.BoolProperty(name="Is Visible", default=True)
    is_selected: bpy.props.BoolProperty(name="Is Selected", default=False)
    
    def toggle_visibility(self, context):
        self.is_visible = not self.is_visible
        armature = context.object
        
        if armature and armature.type == 'ARMATURE' and context.mode == 'POSE':
            for bone in armature.pose.bones:
                if bone.name in [item.name for item in self.items]:
                    bone.bone.hide = not self.is_visible
        else:
            for obj in context.scene.objects:
                if obj.name in [item.name for item in self.items]:
                    obj.hide_set(not self.is_visible)
    
    def select_items(self, context, extend=False):
        armature = context.object
        
        if armature and armature.type == 'ARMATURE' and context.mode == 'POSE':
            if not extend:
                for bone in armature.pose.bones:
                    bone.bone.select = False
            
            for bone in armature.pose.bones:
                if bone.name in [item.name for item in self.items]:
                    bone.bone.select = True
        else:
            if not extend:
                bpy.ops.object.select_all(action='DESELECT')
            
            for obj in context.scene.objects:
                if obj.name in [item.name for item in self.items]:
                    obj.select_set(True)
                    context.view_layer.objects.active = obj

#============== Menyimpan daftar grup sementara ============================================
class RigLayerManager(bpy.types.PropertyGroup):
    """Menyimpan daftar grup sementara."""
    layers: bpy.props.CollectionProperty(type=TemporaryRigLayer)
    active_layer_index: bpy.props.IntProperty(default=-1)

#============== Menambahkan selection ke dalam layer sementara. ============================
class AddSelectionToLayer(bpy.types.Operator):
    """Menambahkan selection ke dalam layer sementara."""
    bl_idname = "rig.add_selection_to_layer"
    bl_label = "Tambah Layer Sementara"
    bl_options = {'REGISTER', 'UNDO'}
    
    layer_name: bpy.props.StringProperty(name="Layer Name", default="New Layer")
    
    def execute(self, context):
        selected = bpy.context.selected_objects
        armature = context.object
        
        if not selected and not (armature and armature.type == 'ARMATURE' and context.selected_pose_bones):
            self.report({'WARNING'}, "Tidak ada objek atau bone yang dipilih!")
            return {'CANCELLED'}
        
        new_layer = context.scene.temp_layers.layers.add()
        new_layer.name = self.layer_name
        
        for obj in selected:
            item = new_layer.items.add()
            item.name = obj.name
        
        if armature and armature.type == 'ARMATURE' and context.selected_pose_bones:
            for bone in context.selected_pose_bones:
                item = new_layer.items.add()
                item.name = bone.name
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
#============================== Toggle visibility dari layer sementara. ================================
class ToggleLayerVisibility(bpy.types.Operator):
    """Toggle visibility dari layer sementara."""
    bl_idname = "rig.toggle_layer_visibility"
    bl_label = "Toggle Visibility"
    
    layer_index: bpy.props.IntProperty()
    
    def execute(self, context):
        temp_layer = context.scene.temp_layers.layers[self.layer_index]
        temp_layer.toggle_visibility(context)
        return {'FINISHED'}

#============================== Memilih objek atau bone yang ada dalam layer ==============================
class SelectLayerItems(bpy.types.Operator):
    """Memilih objek atau bone yang ada dalam layer."""
    bl_idname = "rig.select_layer_items"
    bl_label = "Pilih Objek/Bone"
    
    layer_index: bpy.props.IntProperty()
    extend: bpy.props.BoolProperty(default=False)
    
    def invoke(self, context, event):
        self.extend = event.shift
        return self.execute(context)
    
    def execute(self, context):
        temp_layer = context.scene.temp_layers.layers[self.layer_index]
        temp_layer.select_items(context, extend=self.extend)
        return {'FINISHED'}

class DeleteLayer(bpy.types.Operator):
    """Menghapus layer sementara."""
    bl_idname = "rig.delete_layer"
    bl_label = "Hapus Layer"
    
    layer_index: bpy.props.IntProperty()
    
    def execute(self, context):
        context.scene.temp_layers.layers.remove(self.layer_index)
        return {'FINISHED'}

class RigLayersPanel(bpy.types.Panel):
    """Panel UI untuk menampilkan daftar layer sementara."""
    bl_label = "Temporary Rig Layers"
    bl_idname = "VIEW3D_PT_rig_layers"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Raha_Tools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.operator("view3d.isolate_toggle", text="Toggle Isolate View", icon='HIDE_OFF')                        
        layout.operator("rig.add_selection_to_layer", text="+ Tambah Layer")
        
        if scene.temp_layers.layers:
            for i, temp_layer in enumerate(scene.temp_layers.layers):
                row = layout.row()

                select_btn = row.operator("rig.select_layer_items", text=temp_layer.name)
                select_btn.layer_index = i
                select_btn.extend = False               
                row.operator("rig.toggle_layer_visibility", text="", icon='HIDE_OFF' if temp_layer.is_visible else 'HIDE_ON', depress=temp_layer.is_visible).layer_index = i
                row.operator("rig.delete_layer", text="", icon='X').layer_index = i                  

classes = [VIEW3D_OT_isolate_toggle, TemporaryRigLayer, RigLayerManager, AddSelectionToLayer, ToggleLayerVisibility, SelectLayerItems, DeleteLayer, RigLayersPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.temp_layers = bpy.props.PointerProperty(type=RigLayerManager)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.temp_layers

if __name__ == "__main__":
    register()