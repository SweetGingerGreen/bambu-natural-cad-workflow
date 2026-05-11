# Bambu Natural CAD Workflow

这是一个面向拓竹（Bambu Lab）3D 打印机的自然语言建模工作区。

核心目标很简单：

> 用户用中文描述想要的物件，AI 代理负责写 CadQuery / OpenSCAD / Python，生成可导入 Bambu Studio 的 STEP 或 STL 文件。

当前主要服务两类打印任务：

- **机械/工程件**：自行车码表支架、水壶架、灯架、GoPro 接口、螺孔阵列等。关键尺寸必须由参数化 CAD 生成。
- **装饰/有机件**：笔筒、空气凤梨支架、鹿角蕨板、花盆、桌面摆件等。优先用程序化建模，必要时结合图像生成和轮廓追踪。

这个仓库是私人工作流仓库，包含模板代码、打印规则、复盘文档和已确认的终稿归档。

## 工作流

```text
用户描述 / 参考图
        |
        v
AI 代理判断任务类型
        |
        +-- 机械接口、孔位、卡箍 -> CadQuery 参数化建模 -> STEP/STL
        |
        +-- 有机造型、装饰轮廓 -> OpenSCAD / Python / 图像追踪 -> STL
        |
        v
output/ 临时预览
        |
        v
Bambu Studio 手动检查、切片、打印
        |
        v
prints/YYYY-MM/<project>/ 归档终稿
```

重要边界：

- 不绕过 Bambu Studio 直接推送打印机。
- 不把 AI 图生 3D 的网格用于关键尺寸。
- 不做承重骑行安全件，例如车把、座管、刹车、传动结构。

## 目录结构

```text
.
├── AGENTS.md                  # 给 AI 代理看的项目规则
├── README.md                  # 当前文件
├── requirements.txt           # Python 依赖
├── .env.example               # API Key 模板，真实 .env 不入库
├── calibration/               # 打印校准件
├── docs/                      # FDM 规则、Bambu 流程、复盘经验
├── input/                     # 用户放参考图/GLB，本仓库只保留 .gitkeep
├── output/                    # 临时生成区，不提交具体模型
├── parametric/                # CadQuery 参数化模板
├── pipeline/                  # 通用构建/合并入口
├── prints/YYYY-MM/<project>/  # 用户确认打印的终稿归档
├── scad/                      # OpenSCAD 源文件
└── scripts/                   # 图像追踪、网格生成等辅助脚本
```

## 环境初始化

在 macOS 上：

```bash
cd ~/Desktop/3d-printer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果 `pip install cadquery` 在 OpenCascade 依赖上失败，改用 conda-forge：

```bash
brew install miniforge
mamba create -n cq python=3.11 -c conda-forge cadquery requests python-dotenv numpy
mamba activate cq
```

之后运行命令前使用对应环境即可。

## 常用命令

生成校准件：

```bash
source .venv/bin/activate
python -m calibration.hole_test_card
python -m calibration.ring_31_8
python -m calibration.gopro_mini
```

生成车把卡箍默认件：

```bash
source .venv/bin/activate
python -m parametric.handlebar_clamp
```

使用通用构建入口：

```bash
source .venv/bin/activate
python -m pipeline.build planter_box --params '{"length": 300, "width": 200, "height": 80}' --name planter_30x20x8
```

快速检查某个模板能否 import：

```bash
source .venv/bin/activate
python -c "from parametric import handlebar_clamp; handlebar_clamp.build(31.8)"
```

## 打印产物规则

- `output/` 是临时工作区，只保留目录骨架，不提交具体 STEP/STL/3MF。
- 用户确认开始打印或确认采用的文件，放入 `prints/YYYY-MM/<project>/`。
- 已废弃草稿不要继续堆在 Bambu Studio 项目里；打开新版前先关闭旧项目或新建项目。

当前归档示例：

- `prints/2026-05/rest_pen_holder_workstation/`
- `prints/2026-05/air_plant_f2_lattice_tie/`
- `prints/2026-05/staghorn_e2_coral_board/`

## 建模原则

机械件：

- 接口尺寸、螺孔、卡箍、螺母槽必须来自 CadQuery 精确几何。
- 默认通孔放大来自 `parametric/_common.py`，当前仍是经验值，需通过校准件实测后更新。
- 螺纹默认不打印，使用通孔加螺母槽。
- Bambu Studio 优先导入 STEP；装饰网格才使用 STL。

装饰/有机件：

- 如果用户选定概念图编号，默认严格复刻图中比例和轮廓，不做自由发挥。
- 图像追踪类任务先生成并检查 mask，再导出 STL。
- 中心圆盘、挂孔、绑绳孔等功能区用干净 CAD 几何重建，不直接依赖图片阴影。
- 修改结构时先删除旧结构再替换，避免多个模型或多个圆盘重叠。

更多细节见：

- `docs/fdm-rules.md`
- `docs/bambu-studio-workflow.md`
- `docs/retrospectives/2026-05-rest-pen-holder.md`
- `docs/retrospectives/2026-05-staghorn-coral-board.md`

## API Key

`.env.example` 只提供变量名模板。真实 `.env` 不入库。

```text
TRIPO_API_KEY=
MESHY_API_KEY=
```

需要 AI 图生 3D API 时，由用户自己把 key 填进 `.env`。

## Bambu Studio 使用约定

- AI 代理可以帮忙打开 STL/STEP 到 Bambu Studio 预览。
- 打开新版前必须避免把旧草稿叠在同一个 plate 上。
- 切片参数、打印机选择、发送打印保持用户人工确认。

推荐材料默认值：

| 场景 | 材料 |
| --- | --- |
| 室内装饰件 | PLA |
| 户外/自行车非承重配件 | PETG |
| 高温或更高强度需求 | ASA / PA-CF，需单独评估 |

## 给 AI 代理的入口

接手本仓库前先读：

1. `AGENTS.md`
2. `docs/fdm-rules.md`
3. `docs/bambu-studio-workflow.md`
4. 与当前任务相关的 `docs/retrospectives/`

用户不会直接写 CAD 代码。代理应该把自然语言需求转成可验证的模型文件，并在输出前做尺寸、组件数量、文件路径和 Bambu 打开方式检查。
