import bpy
import math
from mathutils import *
import numpy as np

"""
1.useful functions for me
2.operators
3.a template. register, unregister, if block for testing.
"""


########################### useful functions

def GetCamPosFromCtx(ctx):
    assert type(ctx.space_data) is bpy.types.SpaceView3D
    return GetCamPos(ctx.space_data)

def GetCamPos(spaceView3d):
    #A = bpy.data.screens[2].areas[5].spaces[0].region_3d.view_matrix
    A = spaceView3d.region_3d.view_matrix
    viewLoc = spaceView3d.region_3d.view_location
    viewLoc = Vector((viewLoc.x, viewLoc.y, viewLoc.z, 1.0))

    # ugly blender Matrix and Vector? i could not find a way to write like 'A * v'
    x = A.inverted()[0].dot(viewLoc)
    y = A.inverted()[1].dot(viewLoc)
    z = A.inverted()[2].dot(viewLoc)

    return Vector((x, y, z))



########################## operators

class QuantizeOp(bpy.types.Operator):
    bl_idname = "object.quantize_op"
    bl_label = "CoQuantize"
    bl_description = "quantize coordinates of selected vertices.\n"\
        "for example, if (1.23, 1.26, 1.27) is converted into (1.25, 1.25, 1.25).\n"\
        "each elt is calculated like round(x * N) / N.\n"\
        "now, N is fixed to 16. it is my fault, i'm not accustomed to Blender Add on."
    
    quantize_val: bpy.props.IntProperty(default=16)
    
    @classmethod
    def poll(cls, context):
        if not context.mode == 'OBJECT':
            return False
        return (context.active_object is not None) and (context.active_object.type == 'MESH')
    
    def execute(self, context):
        for v in context.object.data.vertices:
            if v.select:
                x = round(v.co.x * self.quantize_val) / self.quantize_val
                y = round(v.co.y * self.quantize_val) / self.quantize_val
                z = round(v.co.z * self.quantize_val) / self.quantize_val
                v.co = Vector((x, y, z))
        return {'FINISHED'}

class QuantizeUvOp(bpy.types.Operator):
    bl_idname = "object.quantize_uv_op"
    bl_label = "UV Quantize"
    bl_description = "quantize UV values of selected vertices in UV editor.\n"\
        "u will be set to round(u * N) / N.\n"\
        "N is width of an image, which is found in the node first, for now.\n"
    
    @classmethod
    def poll(cls, context):
        if not context.mode == 'OBJECT':
            return False
    
        try:
            # check if we can access desired data from this context.
            _ = context.object.material_slots[0].material.node_tree.nodes
        except:
            return False
        
        return True
    
    def execute(self, context):
        imgWidth = 0
        for node in context.object.material_slots[0].material.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                imgWidth = node.image.size[0]
        if imgWidth == 0:
            return {'FINISHED'}
        
        for i in context.object.data.uv_layers[0].data:
            if not i.select:
                continue
            u = round(i.uv[0] * imgWidth) / imgWidth
            v = round(i.uv[1] * imgWidth) / imgWidth
            i.uv = Vector((u, v))
        return {'FINISHED'}

class MoveDepthOp(bpy.types.Operator):
    bl_idname = "object.move_depth_op"
    bl_label = "MoveDepth"
    bl_description = "you can move an object without changing its position in the screen.\n"\
        "this operator may be useful for setting up a pose with IK."
    
    def __init__(self):
        self.prevMousePos = Vector((0.0, 0.0))
        self.spd = 0.3
        self.posBeforeOp = Vector((0.0, 0.0, 0.0))
    
    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False
        elif context.active_object is None:
            #print("no object is selected???")
            return False
        elif not context.active_object.type == "MESH":
            #print("selected object is not a mesh????")
            return False
        elif not type(context.space_data) is bpy.types.SpaceView3D:
            #print("ctx.space_data is not bpy.types.SpaceView3D")
            return False
        return True
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.prevMousePos = Vector((event.mouse_x, event.mouse_y))
        
        # context.object.location is not a value, but a reference! so create a new vector.
        self.posBeforeOp = Vector(context.object.location)
        
        print("oh posBeforeOp was set just now")
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            mousePos = Vector((event.mouse_x, event.mouse_y))
            dPos = mousePos - Vector((event.mouse_prev_x, event.mouse_prev_y))
            objPos = context.object.location
            curCamPos = GetCamPosFromCtx(context)
            dv = objPos - curCamPos
            if dv.length > 0:
                newLength = dv.length + dPos.y * self.spd
                newDv = dv / dv.length * newLength
                context.object.location = curCamPos + newDv
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.object.location = self.posBeforeOp
            return {'CANCELLED'}
        elif event.type in {'LEFTMOUSE'}:
            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}

class MyOperatorsPanel(bpy.types.Panel):
    bl_idname = "VIEW3DT_PT_myoperators"
    bl_label = "MyOperators"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None)
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='OBJECT_DATA')
    
    def draw(self, context):
        layout = self.layout
        
        layout.operator(MoveDepthOp.bl_idname)
        layout.operator(QuantizeOp.bl_idname)
        layout.operator(QuantizeUvOp.bl_idname)
    


classes = [QuantizeOp, QuantizeUvOp, MoveDepthOp, MyOperatorsPanel]

def menu_func(self, context):
    self.layout.operator(QuantizeOp.bl_idname)
    self.layout.operator(MoveDepthOp.bl_idname)

def register():
    for i in classes:
        bpy.utils.register_class(i)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    for i in classes:
        bpy.utils.unregister_class(i)


if __name__ == '__main__':
    register()
    

