import bpy

#===================== Isolate view ========================================================== 
class VIEW3D_OT_isolate_toggle(bpy.types.Operator):
    bl_idname = "view3d.isolate_toggle"
    bl_label = "Toggle Isolate View"
    bl_description = "Isolate selected object or bone, toggle to reveal"
    bl_options = {'REGISTER', 'UNDO'}

    # Property untuk menyimpan objek/bone yang terseleksi sebelum isolasi
    stored_selection: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    is_hidden: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        obj = context.active_object
        mode = context.object.mode if obj else 'OBJECT'

        if mode == 'POSE':  # Pose Mode (Bone)
            if self.is_hidden:
                # Unhide semua bone
                bpy.ops.pose.reveal()
                # Unselect semua bone
                bpy.ops.pose.select_all(action='DESELECT')
                # Select kembali bone yang diingat
                for bone_name in self.stored_selection:
                    bone = obj.pose.bones.get(bone_name.name)
                    if bone:
                        bone.bone.select = True
                # Periksa layer dan hide bone yang terdaftar di layer off
                self._check_layer_visibility(context, mode)
            else:
                # Simpan bone yang terseleksi
                self.stored_selection.clear()
                for bone in context.selected_pose_bones:
                    item = self.stored_selection.add()
                    item.name = bone.name
                # Hide bone yang tidak terseleksi
                bpy.ops.pose.hide(unselected=True)
        else:  # Object Mode
            if self.is_hidden:
                # Unhide semua objek
                bpy.ops.object.hide_view_clear()
                # Unselect semua objek
                bpy.ops.object.select_all(action='DESELECT')
                # Select kembali objek yang diingat
                for obj_name in self.stored_selection:
                    obj = bpy.data.objects.get(obj_name.name)
                    if obj:
                        obj.select_set(True)
                # Periksa layer dan hide objek yang terdaftar di layer off
                self._check_layer_visibility(context, mode)
            else:
                # Simpan objek yang terseleksi
                self.stored_selection.clear()
                for obj in context.selected_objects:
                    item = self.stored_selection.add()
                    item.name = obj.name
                # Hide objek yang tidak terseleksi
                bpy.ops.object.hide_view_set(unselected=True)

        self.is_hidden = not self.is_hidden  # Toggle state
        return {'FINISHED'}

    def _check_layer_visibility(self, context, mode):
        """Memeriksa visibility layer dan menyembunyikan objek/bone yang terdaftar di layer off."""
        if not hasattr(context.scene, 'temp_layers'):
            return

        for layer in context.scene.temp_layers.layers:
            if not layer.is_visible:  # Jika layer off
                if mode == 'POSE':  # Pose Mode (Bone)
                    armature = context.object
                    if armature and armature.type == 'ARMATURE':
                        for bone_name in layer.items:
                            bone = armature.pose.bones.get(bone_name.name)
                            if bone:
                                bone.bone.hide = True
                else:  # Object Mode
                    for obj_name in layer.items:
                        obj = bpy.data.objects.get(obj_name.name)
                        if obj:
                            obj.hide_set(True)

#========== Class untuk menyimpan daftar objek yang disimpan sementara =======================
class TemporaryRigLayer(bpy.types.PropertyGroup):
    """Class untuk menyimpan daftar objek yang disimpan sementara."""
    name: bpy.props.StringProperty(name="Layer Name")
    items: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    is_visible: bpy.props.BoolProperty(name="Is Visible", default=True)
    show_extra_buttons: bpy.props.BoolProperty(name="Show Extra Buttons", default=False)

    def toggle_visibility(self, context):
        """Toggle visibility dari objek/bone yang terdaftar di layer ini."""
        self.is_visible = not self.is_visible  # Toggle nilai visibilitas

        armature = context.object
        if armature and armature.type == 'ARMATURE' and context.mode == 'POSE':
            for bone_name in self.items:
                bone = armature.pose.bones.get(bone_name.name)
                if bone:
                    bone.bone.hide = not self.is_visible  # Terapkan hide/unhide
        else:
            for obj_name in self.items:
                obj = bpy.data.objects.get(obj_name.name)
                if obj:
                    obj.hide_set(not self.is_visible)  # Terapkan hide/unhide

        # Paksa UI untuk refresh
        context.area.tag_redraw()


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

#============== Menambahkan objek/bone ke layer yang sudah ada ============================
class AddToExistingLayer(bpy.types.Operator):
    """Menambahkan objek/bone ke layer yang sudah ada."""
    bl_idname = "rig.add_to_existing_layer"
    bl_label = "Tambah ke Layer"
    bl_options = {'REGISTER', 'UNDO'}
    
    layer_index: bpy.props.IntProperty()
    
    def execute(self, context):
        selected = bpy.context.selected_objects
        armature = context.object
        
        if not selected and not (armature and armature.type == 'ARMATURE' and context.selected_pose_bones):
            self.report({'WARNING'}, "Tidak ada objek atau bone yang dipilih!")
            return {'CANCELLED'}
        
        temp_layer = context.scene.temp_layers.layers[self.layer_index]
        
        for obj in selected:
            if obj.name not in [item.name for item in temp_layer.items]:
                item = temp_layer.items.add()
                item.name = obj.name
        
        if armature and armature.type == 'ARMATURE' and context.selected_pose_bones:
            for bone in context.selected_pose_bones:
                if bone.name not in [item.name for item in temp_layer.items]:
                    item = temp_layer.items.add()
                    item.name = bone.name
        
        return {'FINISHED'}

#============================== Toggle visibility dari layer sementara. ================================
class ToggleLayerVisibility(bpy.types.Operator):
    """Toggle visibility dari layer sementara."""
    bl_idname = "rig.toggle_layer_visibility"
    bl_label = "Toggle Visibility"
    
    layer_index: bpy.props.IntProperty()
    
    def execute(self, context):
        temp_layer = context.scene.temp_layers.layers[self.layer_index]
        temp_layer.toggle_visibility(context)  # Panggil metode toggle_visibility
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
        armature = context.object
        
        if armature and armature.type == 'ARMATURE' and context.mode == 'POSE':
            if not self.extend:
                bpy.ops.pose.select_all(action='DESELECT')
            for bone_name in temp_layer.items:
                bone = armature.pose.bones.get(bone_name.name)
                if bone:
                    bone.bone.select = True
        else:
            if not self.extend:
                bpy.ops.object.select_all(action='DESELECT')
            for obj_name in temp_layer.items:
                obj = bpy.data.objects.get(obj_name.name)
                if obj:
                    obj.select_set(True)
                    context.view_layer.objects.active = obj
        
        return {'FINISHED'}

class DeleteLayer(bpy.types.Operator):
    """Menghapus layer sementara."""
    bl_idname = "rig.delete_layer"
    bl_label = "Hapus Layer"
    
    layer_index: bpy.props.IntProperty()
    
    def execute(self, context):
        context.scene.temp_layers.layers.remove(self.layer_index)
        return {'FINISHED'}

class RenameLayer(bpy.types.Operator):
    """Operator untuk mengganti nama layer."""
    bl_idname = "rig.rename_layer"
    bl_label = "Rename Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: bpy.props.IntProperty()  # Index layer yang akan di-rename
    new_name: bpy.props.StringProperty(name="New Name", default="")  # Nama baru

    def execute(self, context):
        # Ambil layer berdasarkan index
        temp_layer = context.scene.temp_layers.layers[self.layer_index]
        # Update nama layer
        temp_layer.name = self.new_name
        return {'FINISHED'}

    def invoke(self, context, event):
        # Buka dialog untuk memasukkan nama baru
        return context.window_manager.invoke_props_dialog(self)

# Operator untuk mengeluarkan objek/bone dari layer
class KickFromLayer(bpy.types.Operator):
    """Operator untuk mengeluarkan objek/bone yang dipilih dari layer."""
    bl_idname = "rig.kick_from_layer"
    bl_label = "Kick from Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: bpy.props.IntProperty()  # Index layer yang akan dikick

    def execute(self, context):
        # Ambil layer berdasarkan index
        temp_layer = context.scene.temp_layers.layers[self.layer_index]
        
        # Dapatkan objek/bone yang dipilih
        selected_objects = context.selected_objects
        selected_bones = context.selected_pose_bones if context.mode == 'POSE' else []

        # Loop melalui objek yang dipilih
        for obj in selected_objects:
            for i, item in enumerate(temp_layer.items):
                if item.name == obj.name:
                    temp_layer.items.remove(i)
                    break

        # Loop melalui bone yang dipilih (jika dalam mode POSE)
        for bone in selected_bones:
            for i, item in enumerate(temp_layer.items):
                if item.name == bone.name:
                    temp_layer.items.remove(i)
                    break

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
        layout.operator("rig.add_selection_to_layer", text="+ Add selection")
        
        if scene.temp_layers.layers:
            for i, temp_layer in enumerate(scene.temp_layers.layers):
                box = layout.box()
                row = box.row()

                select_btn = row.operator("rig.select_layer_items", text=temp_layer.name, icon='RESTRICT_SELECT_OFF')
                select_btn.layer_index = i
                select_btn.extend = False
                
                row.prop(temp_layer, "show_extra_buttons", text="", icon='TOOL_SETTINGS')
                
                if temp_layer.show_extra_buttons:
                    sub_row = box.row(align=True)

                    rename_btn = sub_row.operator("rig.rename_layer", text="", icon='GREASEPENCIL')
                    rename_btn.layer_index = i

                    sub_row.separator()  # Tambahkan spasi
                    
                    add_btn = sub_row.operator("rig.add_to_existing_layer", text="", icon='ADD')
                    add_btn.layer_index = i

                    sub_row.separator()  # Tambahkan spasi
                    
                    kick_btn = sub_row.operator("rig.kick_from_layer", text="", icon='PANEL_CLOSE')
                    kick_btn.layer_index = i

                    sub_row.separator()  # Tambahkan spasi
                    
                    visibility_btn = sub_row.operator("rig.toggle_layer_visibility", text="", icon='HIDE_OFF' if temp_layer.is_visible else 'HIDE_ON')
                    visibility_btn.layer_index = i

                    sub_row.separator()  # Tambahkan spasi
                    
                    delete_btn = sub_row.operator("rig.delete_layer", text="", icon='TRASH')
                    delete_btn.layer_index = i
                                    
classes = [VIEW3D_OT_isolate_toggle, TemporaryRigLayer, RigLayerManager, AddSelectionToLayer, AddToExistingLayer, ToggleLayerVisibility, SelectLayerItems, DeleteLayer,RenameLayer,KickFromLayer, RigLayersPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    global preview_collections
    bpy.types.Scene.show_tween_machine = bpy.props.BoolProperty(
        name="Show Tween Machine", 
        description="Tampilkan tombol Tween Machine", 
        default=False
    )
        
    bpy.types.Scene.temp_layers = bpy.props.PointerProperty(type=RigLayerManager)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.temp_layers

if __name__ == "__main__":
    register()
