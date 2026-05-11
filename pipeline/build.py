"""
通用构建入口：被 Claude 调用以快速实例化某个模板。

用法（命令行）：
  python -m pipeline.build handlebar_clamp --bar 31.8 --bolt M5 --name my_clamp

更常见的用法是 Claude 直接 import 模板模块跑 build()，本文件只是命令行便捷入口。
"""

import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parametric import _common as cm  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("template", help="parametric/ 下的模块名，如 handlebar_clamp")
    parser.add_argument("--name", help="输出文件名（默认 {template}_default）")
    parser.add_argument("--params", help="JSON 字符串，传给模板的 build()", default="{}")
    args = parser.parse_args()

    import json
    params = json.loads(args.params)

    mod = importlib.import_module(f"parametric.{args.template}")
    if not hasattr(mod, "build"):
        raise SystemExit(f"模板 {args.template} 缺少 build() 函数")

    result = mod.build(**params)
    base_name = args.name or f"{args.template}_default"

    if isinstance(result, dict):
        for sub_name, part in result.items():
            paths = cm.export(part, f"{base_name}_{sub_name}")
            print(f"[{sub_name}] {paths}")
    else:
        paths = cm.export(result, base_name)
        print(paths)


if __name__ == "__main__":
    main()
