# Stable Diffusion Prompt Tag Aggregator

A Gradio-based web application to aggregate positive prompt tags from image metadata into a wildcard list.

## Features
- **Robust Extraction:** Supports Automatic1111, ComfyUI, InvokeAI, and NovelAI metadata formats.
- **Strict Filtering:** Automatically isolates positive prompts, discarding negative prompts and technical parameters (Steps, Sampler, CFG, etc.).
- **Interactive Cleanup:** Merge, rename, or delete tags directly from the UI table.
- **Large Dataset Support:** Efficiently processes tens of thousands of images using lazy generators and progress tracking.
- **Persistence:** Save and load your current tag counts to resume work later.
- **Dockerized:** Easy deployment with Docker Compose.

## Metadata Handling
The app scans for positive prompts in:
- PNG `parameters` and `prompt` chunks.
- WebP metadata chunks.
- JPEG EXIF (`UserComment`, `Description`) and IPTC tags.
- ComfyUI JSON workflows (extracting from CLIPTextEncode nodes).

## Normalization Rules
1. **Lowercase:** All tags are converted to lowercase.
2. **Weight Removal:** Removes SD weights like `(tag:1.2)` (preserving LoRA weights).
3. **Clean Up:** Strips nested parentheses and brackets.
4. **LoRA Preservation:** Keeps `<lora:name:weight>` tags as requested.
5. **Parameter Filtering:** Automatically excludes technical tags like `steps: 20` or `sampler: dpm++`.

## Quick Start
1. Place your images in a local `./input` folder.
2. Run the application:
   ```bash
   docker compose up --build
   ```
3. Open `http://localhost:4000` in your browser.
4. Enter `/input` as the directory path and click **Process**.
5. Clean your tags using the table buttons and click **Export Wildcard List**.

## Volume Mappings
- **Input:** `./input` (host) -> `/input` (container)
- **Output/State:** `./data` (host) -> `/data` (container)
  - `wildcard.txt`: Exported tags.
  - `state.json`: Saved application state.
