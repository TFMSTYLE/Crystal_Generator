# SPDX-FileCopyrightText: 2025-2026 The French Monkey
# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Crystal",
    "author": "The French Monkey",
    "version": (1, 0, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Crystal",
    "description": "Generate parametric crystal clusters",
    "category": "Add Mesh",
    "license": "GPL-3.0-or-later",
}

import bpy, bmesh, random, math
from math import sin, cos, tau
from mathutils import Matrix, Vector, Euler

# ------------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------------

def cg_apply_or_update_bevel(obj, amount, angle_limit=0.785):
    if amount <= 0.0:
        for m in list(obj.modifiers):
            if m.type == "BEVEL" and m.name.startswith("CG_Bevel"):
                obj.modifiers.remove(m)
        return
    mod = next((m for m in obj.modifiers if m.type == "BEVEL" and m.name.startswith("CG_Bevel")), None)
    if not mod:
        mod = obj.modifiers.new("CG_Bevel", "BEVEL")
    mod.name = "CG_Bevel"
    mod.width = amount
    mod.segments = 1
    mod.limit_method = 'ANGLE'
    mod.angle_limit = angle_limit
    mod.profile = 0.7
    mod.miter_outer = 'MITER_ARC'
    mod.harden_normals = True

# ------------------------------------------------------------------------
# Crystal Building
# ------------------------------------------------------------------------

def cg_random_on_disk(rng, radius):
    t = rng.random()
    rr = radius * (t ** 0.5)
    a = rng.random() * tau
    return rr * cos(a), rr * sin(a)

def cg_build_cluster_mesh(props):
    rng = random.Random(int(props.seed))
    bm = bmesh.new()
    n_sides = 6
    cluster_count = max(1, int(props.cluster_count))
    crystals_per_cluster = max(1, int(props.crystals_per_cluster))
    cluster_radius = max(0.0, float(props.cluster_radius))
    height_min = max(0.001, float(props.crystal_height_min))
    height_max = max(height_min, float(props.crystal_height_max))
    base_radius = max(0.001, float(props.crystal_radius))
    taper = max(0.0, min(0.6, float(props.taper)))
    tip_length = max(0.0, min(1.0, float(props.tip_length)))
    tilt_max = max(0.0, min(45.0, float(props.tilt_max)))
    irregularity = max(0.0, min(0.1, float(props.irregularity)))
    twist = max(0.0, min(30.0, float(props.twist)))
    body_segments = max(1, int(props.body_segments))

    def size_bias(dist, r):
        t = min(1.0, max(0.0, dist / (r + 1e-8)))
        return 1.0 - 0.7 * (t ** 0.75)

    cluster_offsets = [(0.0, 0.0)] if cluster_count == 1 else [
        (cluster_radius * 1.5 * cos(i / cluster_count * tau),
         cluster_radius * 1.5 * sin(i / cluster_count * tau))
        for i in range(cluster_count)
    ]

    for cx, cy in cluster_offsets:
        for _ in range(crystals_per_cluster):
            lx, ly = cg_random_on_disk(rng, cluster_radius)
            px, py = cx + lx, cy + ly
            dist = math.hypot(lx, ly)
            h = rng.uniform(height_min, height_max) * size_bias(dist, cluster_radius)
            r0 = base_radius * (0.6 + 0.8 * rng.random()) * size_bias(dist, cluster_radius)
            r1 = r0 * (1.0 - taper * (0.8 + 0.4 * rng.random()))
            tip_h = h * tip_length * (0.85 + 0.3 * rng.random())
            tilt_deg = rng.uniform(0.0, tilt_max) * (dist / (cluster_radius + 1e-8))
            tilt_ax = rng.random() * tau
            yaw = rng.random() * tau
            twist_deg = rng.uniform(-twist, twist)
            body_h = max(0.0, h - tip_h)
            seg_h = body_h / body_segments if body_segments > 0 else body_h
            local_bm_verts_rings, z_acc, prev_ring = [], 0.0, None
            for si in range(body_segments + 1):
                t = 0.0 if body_h == 0.0 else (z_acc / body_h)
                r_ring = (1.0 - t) * r0 + t * r1
                ring = [bm.verts.new((r_ring * cos(yaw + k / n_sides * tau),
                                      r_ring * sin(yaw + k / n_sides * tau), z_acc))
                        for k in range(n_sides)]
                local_bm_verts_rings.append(ring)
                if prev_ring:
                    for k in range(n_sides):
                        try:
                            bm.faces.new((prev_ring[k], prev_ring[(k + 1) % n_sides],
                                          ring[(k + 1) % n_sides], ring[k]))
                        except ValueError:
                            pass
                prev_ring, z_acc = ring, z_acc + seg_h
            if local_bm_verts_rings:
                try:
                    bm.faces.new(tuple(reversed(local_bm_verts_rings[0])))
                except ValueError:
                    pass
            tip_base_ring = local_bm_verts_rings[-1] if local_bm_verts_rings else []
            tip_top = bm.verts.new((0.0, 0.0, body_h + tip_h))
            off = 0.08 * r1 * (rng.random() - 0.5)
            tip_top.co.x += off * cos(yaw * 1.7)
            tip_top.co.y += off * sin(yaw * 1.7)
            for k in range(n_sides):
                try:
                    bm.faces.new((tip_base_ring[k], tip_base_ring[(k + 1) % n_sides], tip_top))
                except ValueError:
                    pass
            if irregularity > 0.0:
                bm.verts.ensure_lookup_table()
                for ring_i, ring in enumerate(local_bm_verts_rings):
                    ring_t = ring_i / max(1, body_segments)
                    for v in ring:
                        radial = Vector((v.co.x, v.co.y, 0.0))
                        if radial.length > 1e-8:
                            radial.normalize()
                        v.co += radial * irregularity * (0.25 + 0.75 * ring_t) * (rng.random() - 0.5)
                tip_top.co += Vector((
                    irregularity * 0.5 * (rng.random() - 0.5),
                    irregularity * 0.5 * (rng.random() - 0.5),
                    irregularity * 0.2 * (rng.random() - 0.5)))
            if abs(twist_deg) > 1e-6 and (body_h + tip_h) > 1e-6:
                twist_rad = math.radians(twist_deg)
                total_h = body_h + tip_h
                for ring in local_bm_verts_rings:
                    z = ring[0].co.z if ring else 0.0
                    ang = max(0.0, min(1.0, z / total_h)) * twist_rad
                    R = Matrix.Rotation(ang, 4, 'Z')
                    for v in ring:
                        v.co = R @ v.co
                tip_top.co = Matrix.Rotation(twist_rad, 4, 'Z') @ tip_top.co
            R_tilt = Matrix.Rotation(math.radians(tilt_deg), 4, Vector((cos(tilt_ax), sin(tilt_ax), 0.0))) if tilt_deg > 0.0 else Matrix.Identity(4)
            M = Matrix.Translation(Vector((px, py, 0.0))) @ R_tilt
            for ring in local_bm_verts_rings:
                for v in ring:
                    v.co = M @ v.co
            tip_top.co = M @ tip_top.co
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("CrystalMesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return mesh

# ------------------------------------------------------------------------
# Rebuild / Generate
# ------------------------------------------------------------------------

def rebuild_crystal(obj):
    if not obj or obj.type != "MESH": return False
    pvals = {k: obj[k] for k in (
        "cluster_count","crystals_per_cluster","cluster_radius",
        "crystal_radius","crystal_height_min","crystal_height_max",
        "taper","tip_length","tilt_max","irregularity","twist",
        "body_segments","bevel","seed")}
    class _P: pass
    P = _P(); [setattr(P, k, v) for k, v in pvals.items()]
    mesh = cg_build_cluster_mesh(P)
    old = obj.data; obj.data = mesh
    if old and old.users == 0: bpy.data.meshes.remove(old)
    cg_apply_or_update_bevel(obj, float(P.bevel))
    if hasattr(obj.data, "use_auto_smooth"): obj.data.use_auto_smooth = True
    elif hasattr(obj.data, "normals_auto_smooth"): obj.data.normals_auto_smooth = True
    elif hasattr(obj.data, "normals") and hasattr(obj.data.normals, "autosmooth"): obj.data.normals.autosmooth = True
    return True

def generate_crystal(context):
    p = context.scene.crystalgen_props
    obj = context.active_object
    keys = ("cluster_count","crystals_per_cluster","cluster_radius",
            "crystal_radius","crystal_height_min","crystal_height_max",
            "taper","tip_length","tilt_max","irregularity","twist",
            "body_segments","bevel","seed")

    if obj and obj.type == "MESH" and "crystal_generator" in obj and obj.select_get():
        for k in keys:
            obj[k] = getattr(p, k)
        rebuild_crystal(obj)
        obj.name = obj.data.name = "CrystalCluster"
        return obj

    mesh = bpy.data.meshes.new("CrystalMesh")
    new_obj = bpy.data.objects.new("Crystal", mesh)
    context.collection.objects.link(new_obj)
    context.view_layer.objects.active = new_obj
    new_obj.select_set(True)
    for k in keys:
        new_obj[k] = getattr(p, k)
    new_obj["crystal_generator"] = True
    rebuild_crystal(new_obj)
    new_obj.name = new_obj.data.name = "CrystalCluster"
    return new_obj

# ------------------------------------------------------------------------
# Live Update
# ------------------------------------------------------------------------

def update_crystal(self, context):
    p = context.scene.crystalgen_props
    if not p.live_update:
        return
    obj = context.active_object
    if not obj or obj.type != "MESH" or "crystal_generator" not in obj:
        return
    for k in (
        "cluster_count","crystals_per_cluster","cluster_radius",
        "crystal_radius","crystal_height_min","crystal_height_max",
        "taper","tip_length","tilt_max","irregularity","twist",
        "body_segments","bevel","seed"):
        obj[k] = getattr(p, k)
    rebuild_crystal(obj)
    obj.name = obj.data.name = "CrystalCluster"

# ------------------------------------------------------------------------
# Properties / UI
# ------------------------------------------------------------------------

class CrystalGenProperties(bpy.types.PropertyGroup):
    live_update: bpy.props.BoolProperty(name="Live Update", default=False)

    cluster_count: bpy.props.IntProperty(name="Cluster Count", default=1, min=1, max=20, update=update_crystal)
    crystals_per_cluster: bpy.props.IntProperty(name="Crystals per Cluster", default=18, min=1, max=500, update=update_crystal)
    cluster_radius: bpy.props.FloatProperty(name="Cluster Radius", default=1.2, min=0.0, max=10.0, subtype='FACTOR', update=update_crystal)

    crystal_radius: bpy.props.FloatProperty(name="Crystal Base Radius", default=0.07, min=0.005, max=1.0, subtype='FACTOR', update=update_crystal)
    crystal_height_min: bpy.props.FloatProperty(name="Min Height", default=0.6, min=0.01, max=50.0, subtype='FACTOR', update=update_crystal)
    crystal_height_max: bpy.props.FloatProperty(name="Max Height", default=1.6, min=0.01, max=50.0, subtype='FACTOR', update=update_crystal)

    taper: bpy.props.FloatProperty(name="Body Taper", default=0.12, min=0.0, max=0.6, subtype='FACTOR', update=update_crystal)
    tip_length: bpy.props.FloatProperty(name="Tip Length (Rel.)", default=0.28, min=0.0, max=1.0, subtype='FACTOR', update=update_crystal)
    tilt_max: bpy.props.FloatProperty(name="Max Tilt (°)", default=9.0, min=0.0, max=45.0, subtype='FACTOR', update=update_crystal)
    irregularity: bpy.props.FloatProperty(name="Facet Irregularity", default=0.012, min=0.0, max=0.1, subtype='FACTOR', update=update_crystal)
    twist: bpy.props.FloatProperty(name="Twist (°)", default=4.0, min=0.0, max=30.0, subtype='FACTOR', update=update_crystal)
    body_segments: bpy.props.IntProperty(name="Body Segments", default=3, min=1, max=24, update=update_crystal)

    bevel: bpy.props.FloatProperty(name="Bevel Amount", default=0.003, min=0.0, max=0.05, subtype='FACTOR', update=update_crystal)
    seed: bpy.props.IntProperty(name="Seed", default=1, min=0, max=100000, update=update_crystal)
    
# ------------------------------------------------------------------------
# Operators
# ------------------------------------------------------------------------

class CRYSTALGEN_OT_generate(bpy.types.Operator):
    bl_idname = "crystal.generate"
    bl_label = "Generate Crystal"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        generate_crystal(context)
        return {"FINISHED"}
    
class CRYSTALGEN_OT_reset_settings(bpy.types.Operator):
    bl_idname = "crystal.reset_settings"
    bl_label = "Reset Settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.crystalgen_props
        old_live = props.live_update 

        for prop_name, prop_def in CrystalGenProperties.__annotations__.items():
            rna_prop = CrystalGenProperties.bl_rna.properties.get(prop_name)
            if rna_prop and hasattr(props, prop_name):
                setattr(props, prop_name, rna_prop.default)

        props.live_update = old_live

        if old_live:
            update_crystal(props, context)

        self.report({'INFO'}, "Crystal Generator settings reset to defaults")
        return {'FINISHED'}
    
# ------------------------------------------------------------------------
# UI
# ------------------------------------------------------------------------

class VIEW3D_PT_crystal_generator(bpy.types.Panel):
    bl_label = "Crystal"
    bl_idname = "VIEW3D_PT_crystal_generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Crystal"

    def draw(self, context):
        layout = self.layout
        p = context.scene.crystalgen_props
        o = context.object

        row = layout.row(align=True)
        row.operator("crystal.generate", text="Generate Crystal", icon="MESH_ICOSPHERE")

        row = layout.row(align=True)
        row.prop(p, "live_update", toggle=True)
        row.operator("crystal.reset_settings", text="Reset")

        layout.separator(factor=0.5)

        layout.prop(p, "cluster_count", slider=True)
        layout.prop(p, "crystals_per_cluster", slider=True)
        layout.prop(p, "cluster_radius")

        layout.separator(factor=0.5)

        layout.prop(p, "crystal_radius")
        layout.prop(p, "crystal_height_min")
        layout.prop(p, "crystal_height_max")
        layout.prop(p, "taper")
        layout.prop(p, "tip_length")

        layout.separator(factor=0.5)

        layout.prop(p, "tilt_max")
        layout.prop(p, "irregularity")
        layout.prop(p, "twist")
        layout.prop(p, "body_segments", slider=True)

        layout.separator(factor=0.5)

        layout.prop(p, "bevel")
        layout.prop(p, "seed", slider=True)

        layout.separator(factor=0.5)

        if o and o.type == "MESH" and "crystal_generator" in o and o.select_get():
            layout.label(text=f"Editing: {o.name}", icon="MESH_ICOSPHERE")
        else:
            layout.label(text="No crystal selected", icon="INFO")

# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------

classes = (
    CrystalGenProperties,
    CRYSTALGEN_OT_generate,
    CRYSTALGEN_OT_reset_settings, 
    VIEW3D_PT_crystal_generator, 
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.crystalgen_props = bpy.props.PointerProperty(type=CrystalGenProperties)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.crystalgen_props

if __name__ == "__main__":
    register()
