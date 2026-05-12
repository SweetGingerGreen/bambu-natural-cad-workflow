# Bambu Natural CAD Workflow

Natural-language, agent-assisted CAD workflow for Bambu Lab 3D printing.

This repository is a practical starter kit for turning short product ideas or reference images into printable STEP/STL files. It is designed around an AI coding agent that writes and runs CadQuery, OpenSCAD, Python, and mesh-processing scripts while the human still reviews the final model in Bambu Studio before printing.

## What This Is

- Parametric CAD templates for common FDM parts.
- Calibration parts for printer/material fit checks.
- A lightweight build pipeline for generating STEP/STL files.
- Documentation for Bambu Studio preview habits, FDM rules, and modeling retrospectives.
- A few archived final print examples under `prints/`.

The main target is a Bambu Lab printer, but the generated STEP/STL files are standard CAD/mesh outputs and can be used with other slicers.

## Typical Workflow

```text
idea / reference image
        |
        v
AI agent selects or edits a template
        |
        +-- mechanical interfaces, clamps, holes -> CadQuery -> STEP/STL
        |
        +-- organic shape or traced image -> OpenSCAD/Python/mesh tools -> STL
        |
        v
output/ temporary generated files
        |
        v
human review in Bambu Studio
        |
        v
prints/YYYY-MM/<project>/ archived final files
```

Key rules:

- Do not send jobs directly to the printer from automation. Review and slice manually.
- Do not rely on AI-generated meshes for critical dimensions.
- Do not print safety-critical riding parts such as handlebars, seatposts, brakes, or drivetrain components.
- Use STEP for precise mechanical parts when possible; use STL for decorative meshes.

## Repository Layout

```text
.
├── AGENTS.md                  # Operating instructions for coding agents
├── README.md                  # Project overview
├── requirements.txt           # Python dependencies
├── .env.example               # Empty API-key template; real .env is ignored
├── calibration/               # Fit-test and calibration models
├── docs/                      # FDM rules, Bambu workflow, retrospectives
├── input/                     # Local reference images/GLB files; ignored except .gitkeep
├── output/                    # Temporary generated files; ignored except .gitkeep
├── parametric/                # CadQuery templates
├── pipeline/                  # Build and Blender helper entry points
├── prints/                    # Confirmed example final artifacts
├── scad/                      # OpenSCAD source
└── scripts/                   # Image tracing and mesh helper scripts
```

## Setup

```bash
git clone https://github.com/SweetGingerGreen/bambu-natural-cad-workflow.git
cd bambu-natural-cad-workflow
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If CadQuery fails to install through pip on macOS, use conda-forge instead:

```bash
brew install miniforge
mamba create -n cq python=3.11 -c conda-forge cadquery requests python-dotenv numpy
mamba activate cq
pip install opencv-python-headless pillow shapely trimesh mapbox-earcut
```

## Common Commands

Generate calibration parts:

```bash
source .venv/bin/activate
python -m calibration.hole_test_card
python -m calibration.ring_31_8
python -m calibration.gopro_mini
```

Generate the default handlebar clamp:

```bash
source .venv/bin/activate
python -m parametric.handlebar_clamp
```

Use the generic build entry point:

```bash
source .venv/bin/activate
python -m pipeline.build planter_box --params '{"length": 300, "width": 200, "height": 80}' --name planter_30x20x8
```

Run a quick import/build check:

```bash
source .venv/bin/activate
python -c "from parametric import handlebar_clamp; handlebar_clamp.build(31.8)"
```

## Image Tracing Example

Some decorative models are generated from a concept image. The reference image itself is not committed by default; put it under `input/` and pass its path explicitly:

```bash
source .venv/bin/activate
python scripts/trace_e2_staghorn_clean.py --image input/staghorn_e2_reference.png
```

The script writes:

- `output/preview/staghorn_e2_clean_v3_mask.png`
- `output/stl/staghorn_e2_clean_v3.stl`

Image tracing scripts are usually tuned to a specific concept image and may need crop/threshold edits for a different image.

## Generated Files

- `output/` is temporary and ignored by git except for directory placeholders.
- `input/` is ignored because it may contain private reference photos or third-party meshes.
- `prints/` contains curated example final artifacts. If you fork this repository for personal use, remove or replace these examples if your own files are not meant to be public.
- Real `.env` files are ignored. Only `.env.example` is committed.

## FDM Defaults

The default engineering assumptions live in `parametric/_common.py` and `docs/fdm-rules.md`.

Current starting values:

- Through holes: nominal diameter + `0.30mm`
- Slide-fit holes: nominal diameter + `0.20mm`
- General clearance: `0.30mm`

These are initial values, not universal truth. Print the calibration pieces with your real printer, nozzle, filament, and slicer profile before making tight mechanical interfaces.

## Public-Release Checklist

Before publishing a fork, check:

- No `.env`, API keys, access tokens, cookies, or private app settings are tracked.
- No local-only paths such as `.codex/`, `.claude/`, or `/Users/<name>/...` are hardcoded in scripts.
- No private reference photos or customer/client files are under `input/`, `output/`, or `prints/`.
- Generated binary artifacts in `prints/` are intentionally public and licensed.
- README examples do not reveal private printer names, network details, or account data.

## Safety

This repository is for hobby and light utility prints. It does not provide engineering certification, finite-element validation, or product safety guarantees. For bikes and other safety-critical contexts, use these models only for non-load-bearing accessories.

## License

MIT. See `LICENSE`.
