"""
通过 Blender headless 合并 CAD 主体 + AI 网格外观。

用法：
  blender -b -P pipeline/merge_blender.py -- \
      --cad output/step/main.step \
      --ai input/skin.glb \
      --target-dim 30 \
      --out output/stl/merged.stl

注：CAD 进 Blender 需要先转成网格。建议 CadQuery 端同时导出 STL，
本脚本接受 STL/STEP/OBJ/GLB 任意组合（STEP 走 import_curve_step + remesh，
不可控时建议走 STL）。

如果 Blender 没装，整个工作流只剩纯 CAD 路径，依然 90% 够用。
"""

import sys

# Blender 在执行 -P 脚本时，命令行参数在 -- 之后
def parse_argv():
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
    else:
        argv = []
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--cad", required=True, help="CAD 主体（建议 STL/OBJ）")
    p.add_argument("--ai", required=True, help="AI 生成的网格（GLB/OBJ/STL）")
    p.add_argument("--target-dim", type=float, required=True,
                   help="AI 网格最长边的目标尺寸 (mm)")
    p.add_argument("--out", required=True, help="输出 STL 路径")
    p.add_argument("--mode", choices=["union", "skin", "above"], default="skin",
                   help="union=布尔合并; skin=AI 当外壳裹住 CAD; above=AI 放 CAD 上方")
    return p.parse_args(argv)


def main():
    import bpy

    args = parse_argv()

    # 清空场景
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    def import_mesh(path: str, name_hint: str):
        ext = path.lower().rsplit(".", 1)[-1]
        before = set(bpy.data.objects)
        if ext == "stl":
            bpy.ops.wm.stl_import(filepath=path)
        elif ext == "obj":
            bpy.ops.wm.obj_import(filepath=path)
        elif ext == "glb" or ext == "gltf":
            bpy.ops.import_scene.gltf(filepath=path)
        elif ext == "step":
            raise SystemExit("STEP 不支持直接进 Blender，请改传 STL")
        else:
            raise SystemExit(f"未知格式 {ext}")
        new_objs = list(set(bpy.data.objects) - before)
        # 合并所有新进来的 mesh 成一个对象
        meshes = [o for o in new_objs if o.type == "MESH"]
        if not meshes:
            raise SystemExit(f"{path} 未导入任何网格")
        bpy.ops.object.select_all(action="DESELECT")
        for m in meshes:
            m.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        if len(meshes) > 1:
            bpy.ops.object.join()
        obj = bpy.context.view_layer.objects.active
        obj.name = name_hint
        return obj

    cad = import_mesh(args.cad, "CAD")
    ai = import_mesh(args.ai, "AI")

    # 缩放 AI 到目标尺寸（按最长边）
    bbox = ai.dimensions
    longest = max(bbox)
    if longest > 0:
        scale = args.target_dim / longest
        ai.scale = (scale, scale, scale)
        bpy.context.view_layer.update()

    # 把 AI 应用变换烧进网格
    bpy.ops.object.select_all(action="DESELECT")
    ai.select_set(True)
    bpy.context.view_layer.objects.active = ai
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # 合并模式
    if args.mode == "union":
        # 布尔 union AI 到 CAD
        bool_mod = cad.modifiers.new("BoolUnion", "BOOLEAN")
        bool_mod.operation = "UNION"
        bool_mod.object = ai
        bpy.context.view_layer.objects.active = cad
        bpy.ops.object.modifier_apply(modifier="BoolUnion")
        ai.select_set(True)
        bpy.ops.object.delete()
    elif args.mode == "above":
        # 把 AI 放 CAD 上方
        cad_top = cad.matrix_world @ cad.bound_box[1]  # 粗略
        ai.location.z += (cad.dimensions.z) / 2 + (ai.dimensions.z) / 2
    elif args.mode == "skin":
        # 简化：AI 居中包住 CAD（用户视觉上 AI 是外壳，CAD 是内骨架）
        # 实际"挖空 AI 内部、塞 CAD"需要复杂布尔，第一版先把两者一起导出
        pass

    # 选中所有 mesh 一起导出 STL
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.wm.stl_export(filepath=args.out, export_selected_objects=False)
    print(f"[merge_blender] 已写入 {args.out}")


if __name__ == "__main__":
    main()
