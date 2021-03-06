#Copyright (c) 2017 Simón Flores (https://github.com/cheece)

#Permission is hereby granted, free of charge,
#to any person obtaining a copy of this software
#and associated documentation files (the "Software"),
#to deal in the Software without restriction,
#including without limitation the rights to use,
#copy, modify, merge, publish, distribute, sublicense,
#and/or sell copies of the Software, and to permit
#persons to whom the Software is furnished to do so,
#subject to the following conditions:The above copyright
#notice and this permission notice shall be included
#in all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY
#OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
#LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
#EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
#FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
#AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#OTHER DEALINGS IN THE SOFTWARE.

#this a jiggle bone animation tool

#to enable jiggle physics first enable "jiggle scene" in the scene properties and then enable jiggle bone on the bones

bl_info = {
    "name": "Jiggle Armature",
    "author": "Simón Flores",
    "version": (2, 0, 0),
    "blender": (2, 80, 0),
    "description": "Jiggle bone animation tool",
    "warning": "",
    "wiki_url": "",
    "category": "Animation",
}

import bpy
import math
import bmesh
from collections import defaultdict
from bpy.app.handlers import persistent
from bpy.types import Menu, Panel, UIList
from mathutils import Matrix, Vector, Quaternion


class JiggleScene(bpy.types.PropertyGroup):
    test_mode: bpy.props.BoolProperty(default=False)
    sub_steps: bpy.props.IntProperty(min=1, default = 2)
    iterations: bpy.props.IntProperty(min=1, default = 4)
    last_frame: bpy.props.IntProperty()
    length_fix_iters: bpy.props.IntProperty(min=0, default = 2)



class JiggleScenePanel(bpy.types.Panel):
    bl_idname = "Scene_PT_jiggle"
    bl_label = "Jiggle Scene"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        layout.prop(context.scene.jiggle,"test_mode", text="")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        #col.prop(context.scene.jiggle,"test_mode")
        #col.prop(context.scene.jiggle,"sub_steps")
        col.prop(context.scene.jiggle,"iterations")
        #col.prop(context.scene.jiggle,"length_fix_iters")
        #col.operator("jiggle.bake")

inop = False
def funp(prop):
    def f(self,context):
        global inop
        if(inop):
            return
        inop = True
        b = context.bone
        o = context.object
        arm = o.data
        for b2 in arm.bones:
            if(b2.select):
                setattr(b2.jiggle, prop, getattr(b.jiggle,prop))
        inop = False
    return f
class JiggleBone(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(default=False, update = funp("enabled"))
    Kld: bpy.props.FloatProperty(name = "linear damping",min=0.0, max=1.0,default = 0.01, update = funp("Kld"))
    Kd: bpy.props.FloatProperty(name = "angular damping",min=0.0, max=1.0,default = 0.01, update = funp("Kd"))
    Ks: bpy.props.FloatProperty(name = "stiffness",min=0.0 , max = 1.0, default = 0.8, update = funp("Ks"))
    mass: bpy.props.FloatProperty(min=0.0001, default = 1.0, update = funp("mass"))
    #M = bpy.props.FloatVectorProperty(size=9,subtype='MATRIX')
    R: bpy.props.FloatVectorProperty(name="rotation", size=4,subtype='QUATERNION')
    W: bpy.props.FloatVectorProperty(size=3,subtype='XYZ')
    P: bpy.props.FloatVectorProperty(size=3,subtype='XYZ')
    V: bpy.props.FloatVectorProperty(size=3,subtype='XYZ')
    control: bpy.props.FloatProperty(name = "control",min=0.0, max=1.0,default = 1, update = funp("control"))
    control_bone: bpy.props.StringProperty(name = "control bone")
    debug: bpy.props.StringProperty()

def setq(om, m):
    for i in range(4):
        om[i]= m[i]

class ResetJigglePropsOperator(bpy.types.Operator):
    bl_idname = "jiggle.reset"
    bl_label = "Reset State"
    def execute(self, context):
        scene = context.scene
        for o in scene.objects:
            if(o.select_get() and o.type == 'ARMATURE' ):
                ow = o.matrix_world
                for b in o.pose.bones:
                    if(b.bone.select):
                        M = ow@b.matrix #ow*Sbp.wmat* Sb.rmat #im
                        #l ,r,s = M.decompose()

                        Jb = b.bone.jiggle
                        setq(Jb.R, M.to_quaternion().normalized())
                        Jb.V = Vector((0,0,0))
                        Jb.P = M.translation.copy()
                        Jb.W = Vector((0,0,0))
                        #Jb.M = Matrix(M)
        return {'FINISHED'}


class JiggleBonePanel(bpy.types.Panel):
    bl_idname = "Bone_PT_jiggle_bone"
    bl_label = "Jiggle Bone"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return ( context.bone is not None and context.object is not None and context.object.type == 'ARMATURE')

    def draw_header(self, context):
        layout = self.layout
        bon = context.bone
        layout.prop(bon.jiggle, "enabled", text="")

    def draw(self, context):
        layout = self.layout

        bon = context.bone
        col = layout.column()
        layout.enabled = context.scene.jiggle.test_mode
        if(not context.scene.jiggle.test_mode):
            col.label(text= "jigglescene disabled, see scene properties")

        if(bon.jiggle.enabled):
            col.prop(bon.jiggle,"Ks")
            col.prop(bon.jiggle,"Kd")
            col.prop(bon.jiggle,"Kld")
            col.prop(bon.jiggle,"mass")
            col.prop(bon.jiggle,"debug")
            col.prop(bon.jiggle,"control")
            col.prop(bon.jiggle,"control_bone")
            col.operator("jiggle.reset")
            if(bon.parent==None):
                col.label(text= "warning: jibblebones without parent will fall",icon='COLOR_RED')

class JB:
    def __init__(self, b,M,p):
        self.M  = M.copy()
        self.length = b.bone.length*M.col[0].length
        self.b = b
        self.parent = p
        self.rest = None
        self.w = 0
        self.Cx = None

    def applyImpulse(self, p, I, t=0.5):
        if self.w <= 0:
            return

        I = I * self.w
        C = self.sample(t)
        r = p - C
        tg = p + I
        r2 = tg - C
        ax = r.cross(r2)

        if(ax.length_squared > 0.000001):
            angle = r.angle(r2)
            mr = Matrix.Rotation(angle, 3, ax)
            self.R = (mr @ self.R).normalized()
            self.M.translation += C - self.sample(t)
            p = mr @ (p - C) + C

        self.M.translation += tg - p

    def sample(self, t):
        return self.M.translation + t * self.M.col[1].to_3d() * self.length

    @property
    def P(self):
        return self.M.translation
    @P.setter
    def P(self, x):
        self.M.translation = x

    @property
    def Q(self):
        return self.M.to_quaternion()
    @Q.setter
    def Q(self, x):
        self.R = x.to_matrix()

    @property
    def R(self):
        return self.M.to_3x3()
    @R.setter
    def R(self, x):
        translation = self.M.translation
        self.M = x.to_4x4()
        self.M.translation = translation

def propB(ow,b, l, p, children_of_bone):
    j = JB(b, ow @ b.matrix, p)
    l.append(j)
    for c in children_of_bone[b]:
        propB(ow,c,l,j,children_of_bone)

def qadd(a,b):
    return Quaternion((a[0]+b[0],a[1]+b[1],a[2]+b[2],a[3]+b[3]))

def qadd2(a,b):
    a.x+=b.x
    a.y+=b.y
    a.z+=b.z
    a.w+=b.w

def quatSpring(Jb,r=None,k=None):
    Q0 = Jb.parent.Q
    Q1 = Jb.Q
    w0 = Jb.parent.w
    w1 = Jb.w
    if(r is None):
        r = Jb.rest.to_quaternion()
        k = Jb.k
    Q0x = Q0.x
    Q0y = Q0.y
    Q0z = Q0.z
    Q0w = Q0.w
    Q1x = Q1.x
    Q1y = Q1.y
    Q1z = Q1.z
    Q1w = Q1.w
    rx  =  r.x
    ry  =  r.y
    rz  =  r.z
    rw  =  r.w

    tmp0 = Q0w * rx + Q0x * rw + Q0y * rz - Q0z * ry
    tmp1 = Q0w * rw - Q0x * rx - Q0y * ry - Q0z * rz
    tmp2 = Q0w * rz + Q0x * ry - Q0y * rx + Q0z * rw
    tmp3 = Q0w * ry - Q0x * rz + Q0y * rw + Q0z * rx


    tmp4 = Q1w * tmp0 - Q1x * tmp1 - Q1y * tmp2 + Q1z * tmp3
    tmp5 = Q1w * tmp3 + Q1x * tmp2 - Q1y * tmp1 - Q1z * tmp0
    tmp6 = Q1w * tmp2 - Q1x * tmp3 + Q1y * tmp0 - Q1z * tmp1

    tmp7 = Q1x * rz
    tmp8 = Q1y * rx
    tmp9 = Q1w * rw
    tmp10 = Q1z * ry

    c = pow(tmp4, 2) + pow(tmp5, 2) + pow(tmp6, 2)

    dQ0x = 2 * tmp6 * (tmp7  + Q1w * ry            + Q1y * rw + Q1z * rx)
    dQ0y = 2 * tmp6 * (tmp10 - Q1w * rx - Q1x * rw + Q1y * rz           )
    dQ0z = 2 * tmp6 * (tmp9             - Q1x * rx - Q1y * ry + Q1z * rz)
    dQ0w = 2 * tmp6 * (tmp8  + Q1w * rz - Q1x * ry            - Q1z * rw)

    dQ0x += 2 * tmp5 * (tmp8  - Q1w * rz + Q1x * ry            - Q1z * rw)
    dQ0y += 2 * tmp5 * (tmp9             - Q1x * rx + Q1y * ry - Q1z * rz)
    dQ0z += 2 * tmp5 * (tmp10 + Q1w * rx + Q1x * rw + Q1y * rz           )
    dQ0w += 2 * tmp5 * (tmp7  + Q1w * ry            - Q1y * rw - Q1z * rx)

    dQ0x += 2 * tmp4 * (tmp9             + Q1x * rx - Q1y * ry - Q1z * rz)
    dQ0y += 2 * tmp4 * (tmp8  + Q1w * rz + Q1x * ry            + Q1z * rw)
    dQ0z += 2 * tmp4 * (tmp7  - Q1w * ry            - Q1y * rw + Q1z * rx)
    dQ0w += 2 * tmp4 * (tmp10 + Q1w * rx - Q1x * rw - Q1y * rz)


    dQ1x = -2 * tmp6 * tmp3 + 2 * tmp5 * tmp2 - 2 * tmp4 * tmp1
    dQ1y =  2 * tmp6 * tmp0 - 2 * tmp5 * tmp1 - 2 * tmp4 * tmp2
    dQ1z = -2 * tmp6 * tmp1 - 2 * tmp5 * tmp0 + 2 * tmp4 * tmp3
    dQ1w =  2 * tmp6 * tmp2 + 2 * tmp5 * tmp3 + 2 * tmp4 * tmp0


    div = dQ0x*dQ0x*w0 + \
          dQ0y*dQ0y*w0 + \
          dQ0z*dQ0z*w0 + \
          dQ0w*dQ0w*w0 + \
          dQ1x*dQ1x*w1 + \
          dQ1y*dQ1y*w1 + \
          dQ1z*dQ1z*w1 + \
          dQ1w*dQ1w*w1

    if(div> 1e-8):
        s = -c/div
        if(w0>0.0):
            #qadd2(Q0, Quaternion((dQ0w*s*w0*k,dQ0x*s*w0*k,dQ0y*s*w0*k,dQ0z*s*w0*k)))
            #
            Q0.x+=dQ0x*s*w0*k
            Q0.y+=dQ0y*s*w0*k
            Q0.z+=dQ0z*s*w0*k
            Q0.w+=dQ0w*s*w0*k
            Jb.parent.Q = Q0.normalized()
        #qadd2(Q1, Quaternion((dQ1w*s*w1*k,dQ1x*s*w1*k,dQ1y*s*w1*k,dQ1z*s*w1*k)))
        Q1.x+=dQ1x*s*w1*k
        Q1.y+=dQ1y*s*w1*k
        Q1.z+=dQ1z*s*w1*k
        Q1.w+=dQ1w*s*w1*k
        Jb.Q = Q1.normalized()

def step(scene):
    global dt
    sub_steps = 1#*scene.jiggle.sub_steps)
    dt = 1.0/(scene.render.fps*sub_steps)

    for o in scene.objects:
        if(o.type == 'ARMATURE'):

            ow = o.matrix_world.copy()
            scale = ow.col[0].length

            children_of_bone = defaultdict(list)
            for bone in o.pose.bones:
                if bone.parent is not None:
                    children_of_bone[bone.parent].append(bone)

            for _ in range( sub_steps):
                bl = []

                for b in o.pose.bones:
                    if(b.parent==None):
                        propB(ow,b,bl,None,children_of_bone)

                bl2 = []
                for wb in bl:
                    b = wb.b
                    # o------ -> ---o---
                    wb.restW = b.bone.matrix_local.copy() * scale
                    wb.Q = wb.Q.normalized()

                    if(b.bone.jiggle.enabled):
                    #(wb.parent.restW.inverted() * wb.restW) #
                        Jb = b.bone.jiggle
                        wb.rest =  b.bone.matrix_local #
                        if(b.parent!=None):
                            wb.rest = b.bone.parent.matrix_local.inverted() @ wb.rest
                        wb.Kc = 0
                        if(Jb.control_bone!=""):
                            if(Jb.control_bone in o.pose.bones):
                                cb = o.pose.bones[Jb.control_bone]
                                clm = cb.matrix
                                if(cb.parent!=None):
                                    clm = cb.parent.matrix.inverted() @ clm
                                wb.cQ = clm.to_quaternion().normalized()
                                wb.Kc = 1- pow(1-Jb.control, 1/scene.jiggle.iterations)


                        wb.rest_base = wb.rest.copy()
                        wb.rest.translation = wb.rest.translation * scale
                        wb.length = b.bone.length*scale
                        wb.irest = wb.rest.inverted()
                        wb.w = 1.0/Jb.mass
                        wb.k = 1- pow(1-Jb.Ks, 1/scene.jiggle.iterations)
                        Jb.V*= 1.0-Jb.Kld
                        Jb.V+= scene.gravity*dt
                        Jb.W*= 1.0-Jb.Kd
                        R = Jb.R.to_matrix()
                        wb.R = R.normalized()
                        wb.P = Jb.P.copy()
                        wb.Cx = wb.sample(0.5)
                        qv = Quaternion()
                        qv.x = Jb.W[0]
                        qv.y = Jb.W[1]
                        qv.z = Jb.W[2]
                        qv.w = 0
                        cv = wb.Cx + Jb.V*dt
                        wb.Q = qadd(wb.Q, qv@wb.Q*dt*0.5).normalized()    #newton's first law
                        wb.P += cv - wb.sample(0.5)#the same

                        bl2.append(wb)


                for i in range(scene.jiggle.iterations):
                    for wb in bl2:
                        b = wb.b
                        if(b.parent==None):
                            continue
                        Jb = b.bone.jiggle
                        Pc =  wb.P
                        target_m = wb.parent.M@wb.rest
                        Pt = target_m.translation.copy()
                        if(Jb.debug in scene.objects):
                            scene.objects[Jb.debug].location = Pc
                        W = wb.w + wb.parent.w
                        I = (Pc-Pt)/W

                        wb.applyImpulse(Pc,-I)
                        wb.parent.applyImpulse(Pt,I)

                #for i in range(scene.jiggle.iterations):
                    for wb in bl2:
                        b = wb.b
                        if(b.parent==None):
                            continue
                        Jb = b.bone.jiggle
                        quatSpring(wb)
                        if(wb.Kc>0.0):
                            quatSpring(wb,wb.cQ, wb.Kc)
                for wb in bl2:
                    b = wb.b
                    if(b.parent==None):
                        continue
                    Jb = b.bone.jiggle
                    wb.P = wb.parent.M@wb.rest.translation
                    wb.R = wb.Q.normalized().to_matrix()


                for wb in bl2:
                    b = wb.b
                    Jb = b.bone.jiggle
                    R = Jb.R.to_matrix()
                    Jb.V = (wb.sample(0.5) - wb.Cx)/dt
                    Jb.P = wb.P.copy()
                    wb.Q = wb.Q.normalized()
                    qv = wb.Q@Jb.R.conjugated() #qadd(wb.Q,-Jb.R)*Jb.R.conjugated()#
                    Jb.W = Vector((qv.x,qv.y,qv.z))*(2/dt)
                    Jb.R = wb.Q

                for wb in bl:
                    wb.R*=scale
                for wb in bl2:
                    b = wb.b
                    pM = ow
                    if(b.parent!=None):
                        pM = wb.parent.M
                    b.matrix_basis = (pM@wb.rest_base).inverted()@wb.M

    scene.jiggle.last_frame+= 1



@persistent
def update(scene, tm = False):
    global dt
    dt = 1.0/(scene.render.fps*scene.jiggle.sub_steps)
    # print(scene.jiggle.test_mode)
    if(not (scene.jiggle.test_mode or tm)):
        return
   # if(scene.frame_current == scene.jiggle.last_frame):
   #     return
    # print("beg2 " + str(scene.frame_current)+ " " +  str(scene.jiggle.last_frame))
    if(scene.frame_current <  scene.jiggle.last_frame or scene.frame_current == scene.frame_start): #frame break
        scene.jiggle.last_frame = scene.frame_current
        for o in scene.objects:
            if( o.type == 'ARMATURE'):
                ow = o.matrix_world
                for b in o.pose.bones:
                    if(b.bone.jiggle.enabled):
                        M = ow@b.matrix #ow*Sbp.wmat* Sb.rmat #im

                        Jb = b.bone.jiggle
                        setq(Jb.R, M.to_quaternion())
                        Jb.V = Vector((0,0,0))
                        Jb.P = M.translation.copy()
                        Jb.W = Vector((0,0,0))

        if(scene.frame_current <= bpy.context.scene.frame_start):
            return
    nframes = scene.frame_current - scene.jiggle.last_frame
    for i in range(nframes):
        step(scene)

classes = [
    JiggleScene,
    JiggleScenePanel,
    JiggleBone,
    ResetJigglePropsOperator,
    JiggleBonePanel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Bone.jiggle = bpy.props.PointerProperty(type = JiggleBone)
    bpy.types.Scene.jiggle = bpy.props.PointerProperty(type = JiggleScene)
    bpy.app.handlers.frame_change_pre.append(update)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.app.handlers.frame_change_pre.remove(update)

if __name__ == '__main__':
	register()
