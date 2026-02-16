# AI Context - Prompt Aggregator Project

## Core Requirements
- Python 3.12 + Gradio
- Dockerized (port 4000)
- Volume mounts: `./input` -> `/input` (source), `./data` -> `/data` (output)
- Supported formats: `.png`, `.webp`, `.jpg`, `.jpeg`
- Recursive image scanning.

## Functional Directives
- Extract **ONLY positive prompt** from metadata (A1111 format only).
- Ignore negative prompts and technical parameters (Steps, Sampler, CFG, etc.).
- Preserve phrase order.
- Preserve LoRA tags (`<lora:name:weight>`) as requested by user.
- Normalize tags: lowercase, trim, remove weights (except for LoRAs).
- Split by comma.
- Interactive UI: Merge, Rename, Delete, Inline Edit.
- Export to `/data/wildcard.txt`.
- Persistence: Save/Load state to `/data/state.json`.

## Technical Implementations
- **Modular Structure:** `loader.py` (extraction), `parser.py` (normalization), `aggregator.py` (counting), `editor.py` (logic), `app.py` (UI).
- **Efficiency:** Uses lazy generators for directory scanning. Two-pass processing to show accurate progress bars.
- **Logging:** Centralized logging to `stdout` with `PYTHONUNBUFFERED=1` and `force=True` root logger config for Docker visibility.
- **Robustness:** Handles binary/jumbled metadata with `piexif` for JPEG/WebP EXIF and standard `img.info` for PNG.
- **CI/CD:** GitHub Actions workflow with Buildx caching and Public ECR mirror for base image.

## Key Heuristics
- **A1111 Only:** strictly parses "parameters" (PNG) or UserComment (JPEG).
- `is_likely_negative`: Identifies negative prompts by common keywords (lowres, bad anatomy, etc.), excluding generic words.
- `PARAMETER_PREFIXES`: Filters out common A1111 parameters that might appear in metadata fields.
- **EXIF Handling:** Uses `piexif` to robustly decode UserComment fields (often UNICODE).
