# AGENTS.md · 3D 打印自然语言建模工作流

> 给接手这个仓库的 AI 编码代理看的项目说明（Codex / Claude Code / Cursor 等通用）。
> 用户不会写 CAD 代码，**所有几何/Python/CLI 都由你执行**，用户只在对话里用自然语言说要什么件。

## 项目目标

用户有一台拓竹（Bambu Lab）3D 打印机，但完全不会用 3D 软件。这个仓库提供一条工作流：

> **用户一句话 → 你写/调 CadQuery 代码 → 生成 STEP/STL → 用户拖进 Bambu Studio 打印**

用户主要做两类件：
1. **机械/工程件**（自行车配件：码表支架、水壶架、灯架等）— 接口尺寸敏感，必须走参数化 CAD
2. **装饰/有机件**（鹿角蕨板花盆、桌面摆件等）— 多数纯 CAD 够用，造型复杂时走 AI 图生 3D + Blender 合并

## 核心原则（必须遵守）

1. **自然语言即接口**：用户说一句话（中文为主），你判断需求、组合或扩展模板、跑 CadQuery、把 STEP/STL 路径回告。**不要让用户碰 Python**。
2. **AI 网格不承担关键尺寸**：所有接口（卡箍直径、螺孔间距、卡扣公差）必须从 CadQuery 几何来。AI 生成的 GLB 仅用作装饰外观/外壳。
3. **机械件首选 STEP，装饰件 STL**：Bambu Studio 支持 STEP 导入并保留精度；AI 网格件用 STL。
4. **工程规则内置在模板**：见 `docs/fdm-rules.md`。默认 PETG（户外/自行车）、通孔+螺母槽、不画印刷螺纹、孔径补偿 +0.3mm。
5. **不打印承重骑行件**（车把、座管、刹车、传动）— 安全相关，不在范围内。

## 目录结构

```
~/Desktop/3d-printer/
├── README.md                   # 给用户看的：怎么跟 AI 说话出模型
├── AGENTS.md                   # 本文件：给 AI 代理看的
├── requirements.txt            # cadquery / requests / python-dotenv / numpy
├── .env.example → .env         # API Key（仅 AI 自动化时用，用户自填）
│
├── docs/
│   ├── fdm-rules.md            # 材料/打印方向/孔径补偿/螺纹策略
│   └── prompt-cookbook.md      # 用户常用 prompt 抄答案手册
│
├── parametric/                 # 你维护的 CadQuery 模板库
│   ├── _common.py              # 全局补偿（HOLE_OFFSET 等）+ M 螺丝规格表 + export()
│   ├── handlebar_clamp.py      # 两件式车把卡箍（22.2/25.4/31.8mm 通用）
│   ├── seatpost_clamp.py       # 座管夹（复用 handlebar_clamp）
│   ├── bolt_pattern.py         # 通用螺孔阵列工具 + 网格生成
│   ├── gopro_mount.py          # GoPro 三爪母接口
│   ├── water_bottle_cage.py    # 水壶架（背板 + 环抱）
│   └── planter_box.py          # 鹿角蕨板/挂墙花盆（参数化）
│
├── calibration/                # 校准件
│   ├── hole_test_card.py       # M3/M4/M5/M6 各 3 种孔径补偿
│   ├── ring_31_8.py            # 31.8mm 卡箍测试（复用 handlebar_clamp）
│   └── gopro_mini.py           # GoPro 三爪小样
│
├── pipeline/
│   ├── build.py                # CLI 入口：python -m pipeline.build <template> --params <json>
│   └── merge_blender.py        # Blender headless 合并 CAD + AI 网格（用户装 Blender 后启用）
│
├── input/                      # 用户放参考图 / 从 AI 服务下载的 GLB（你只读不写）
└── output/
    ├── step/                   # 你写入：机械件 STEP（首选）
    ├── stl/                    # 你写入：装饰/AI 件 STL
    └── 3mf/                    # 你写入：（可选）已切片 Bambu Studio 项目
```

## 环境

- Python venv 在 `.venv/`（macOS / arm64 验证可用，CadQuery 2.7.0）
- 所有命令前先 `source .venv/bin/activate`
- 如果 pip 装 cadquery 失败，README 里有 mamba 退路

## 常用命令

```bash
# 激活环境
source .venv/bin/activate

# 跑某个模板的默认参数（如 README 里展示的"开箱"件）
python -m parametric.handlebar_clamp     # → output/step/handlebar_clamp_31_8_{base,cap}.step

# 通用 CLI 入口（推荐你用这个）
python -m pipeline.build planter_box --params '{"length": 300, "width": 200, "height": 80}' --name planter_30x20x8

# 跑校准件
python -m calibration.hole_test_card
python -m calibration.ring_31_8
python -m calibration.gopro_mini

# 单文件 import 验证（写完新模板后跑一下确保没语法/几何错）
python -c "from parametric import handlebar_clamp; handlebar_clamp.build(31.8)"
```

## 校准状态（重要）

`parametric/_common.py` 顶部三个常量是**机器+材料相关的真实补偿**，需要打实物校准：

```python
HOLE_OFFSET = 0.30          # 通孔放大 (mm)
SLIDE_FIT_OFFSET = 0.20     # 紧配合销孔放大
CLEARANCE = 0.30            # 一般间隙
```

**当前状态**：未校准，是经验初值。

**校准流程**：
1. 用户用平时常用材料（推荐 PETG）打三个校准件
2. 用户实测后告诉你，例如"M5 +0.3 最顺、卡箍稍紧"
3. **你直接编辑 `_common.py` 里的常量**，例如把 `HOLE_OFFSET = 0.30` 改成 `0.30`（保持）或 `0.35`（更松）
4. 之后所有件自动用校准过的参数

**校准前**：可以先做"小玩意"（笔筒、钥匙扣、装饰件），尺寸不敏感。**承接自行车配件前必须校准**。

## 标准任务模式

### 用户说"做个 X"

1. **判断类别**：机械件 / 装饰件 / 混合 / 信息不全
2. **检查模板**：`parametric/` 里有现成的吗？
   - 有 → 直接 `python -m pipeline.build <template> --params <json>`，调用 `parametric/_common.py::export()`
   - 没有 → 写一个新的 `parametric/<name>.py`（必须有 `build(**params)` 返回 Workplane 或 dict[str, Workplane]），然后调用
3. **缺关键尺寸时反问 1-2 个问题**（不要瞎猜车把直径、瓶子直径、屏幕尺寸这种）
4. **生成后回告路径**：`output/step/<name>.step` + 简短打印建议（材料、方向、是否需要支撑）

### 用户要 AI 外观（树皮纹、动物造型等纯 CAD 难做的）

1. 提供两条路径让用户选：
   - **A) AI 图生 3D**：让用户在 Tripo3D / Meshy / GPT Image 2 mesh editing 等服务网页生成 GLB → 下载到 `input/` → 你用 `pipeline/merge_blender.py` 合并到 CAD 主体
   - **B) 程序化纹理**：CadQuery 内 displacement / 周期性几何（噪声/六边形/孔阵），全自动但效果不如 AI
2. 走 A 路径需要用户装 Blender（headless 命令行调用，不需要 GUI 操作）
3. **关键尺寸（接口、孔距、卡扣）必须从 CAD 来**，AI 网格只贴外观

### 用户对结果不满意（"再大点"、"卡得太松"等）

直接调参数重跑，几秒钟一次。所有模板都是参数化的，改 `_common.py` 全局或单次调用 params 都行。

### Bambu Studio 预览新版

打开新版 STL/3MF 前，先确认不会把旧草稿继续叠到当前 Bambu Studio plate 里。必要时退出 Bambu Studio 或新建项目后再打开。PETG/PLA 主件和 TPU 软环默认分开预览/打印。详见 `docs/bambu-studio-workflow.md`。

## 写新模板的约定

```python
"""<模板用途简短描述>。"""

import cadquery as cq
from . import _common as cm   # 强制使用统一的 export / 补偿常量


def build(**params) -> cq.Workplane | dict[str, cq.Workplane]:
    """所有模板必须暴露 build()。多件套返回 dict[str, Workplane]。"""
    ...


if __name__ == "__main__":
    p = build()
    if isinstance(p, dict):
        for name, part in p.items():
            cm.export(part, f"<template_name>_{name}")
    else:
        cm.export(p, "<template_name>")
```

注意：
- `cm.export(part, name)` 默认同时导出 STEP + STL
- 不要硬编码孔径，用 `cm.thru_hole_d("M5")` 取带补偿的尺寸
- 不要硬编码间隙，用 `cm.CLEARANCE`
- 螺孔搭配六角螺母槽（`cm.M_SPECS[m]["nut_af"]` / `nut_h`）
- 复用 `parametric/bolt_pattern.py::add_holes()` 而不是自己每次写

## 安全/隐私边界

- **不要替用户填 API Key**，让用户自己填进 `.env`
- **不要直推打印机**：保持用户在 Bambu Studio 里手动审核切片
- **不要打承重骑行件**（车把、座管、刹车、传动）
- **AI 生成内容不影响关键尺寸**

## 已知限制

- `pipeline/merge_blender.py` 第一版 `mode=skin` 还是占位逻辑（仅把两个网格一起导出，没真正"挖空 AI 内壳套 CAD 主体"）。需要时改进它的布尔逻辑。
- `water_bottle_cage.py` 的桥接结构是简化几何，复杂车架要适配可能要重新设计。
- 没有自动切片 → 3MF 流水线。用户都在 Bambu Studio 里手动切片。

## 参考

- 用户视角入口：[README.md](README.md)
- 工程规则：[docs/fdm-rules.md](docs/fdm-rules.md)
- Bambu 预览规则：[docs/bambu-studio-workflow.md](docs/bambu-studio-workflow.md)
- Prompt 示例：[docs/prompt-cookbook.md](docs/prompt-cookbook.md)
- 打印复盘：[docs/retrospectives/2026-05-rest-pen-holder.md](docs/retrospectives/2026-05-rest-pen-holder.md)
- 按图复刻复盘：[docs/retrospectives/2026-05-staghorn-coral-board.md](docs/retrospectives/2026-05-staghorn-coral-board.md)
- CadQuery 文档：https://cadquery.readthedocs.io/
- Bambu Studio：https://bambulab.com/zh-cn/download/studio
