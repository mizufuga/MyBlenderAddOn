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
    bl_label = "My Coordinate Quantize Operator"
    
    quantize_val: bpy.props.IntProperty(default=16)
    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None) and (context.active_object.type == 'MESH')
    
    def execute(self, context):
        for v in context.object.data.vertices:
            if v.select:
                x = round(v.co.x * self.quantize_val) / self.quantize_val
                y = round(v.co.y * self.quantize_val) / self.quantize_val
                z = round(v.co.z * self.quantize_val) / self.quantize_val
                v.co = Vector((x, y, z))
                print(v.co)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(QuantizeOp.bl_idname)

def register():
    bpy.utils.register_class(QuantizeOp)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(QuantizeOp)


if __name__ == '__main__':
    register()
    bpy.ops.object.quantize_op("INVOKE_DEFAULT")

