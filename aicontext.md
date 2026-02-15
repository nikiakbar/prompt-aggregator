# AI Context - Prompt Aggregator

## Core Instructions
- Always update `README.md` and `aicontext.md` when adding new features.

## Requested Features

### 1. General Requirements
- Language: Python 3.12
- UI: Gradio
- Runtime: Docker
- Input: Filesystem path inside container
- Supported Formats: .png, .webp, .jpg, .jpeg
- Port: 4000

### 2. Functional Behavior
- Input: Directory path string.
- Metadata Extraction: Use Pillow to extract positive prompts from 'parameters' or 'prompt' keys.
- Normalization: Lowercase, trim, remove SD weights (e.g., `(word:1.2)`).
- Recursive Scanning: Scan directories recursively for images.
- Memory Management: Lazy iteration over files, optional batch processing (100 images).
- Progress: Show processed/total in UI and logs.

### 3. UI Requirements
- Section A - Input: Path, Process button, Path/Count display.
- Section B - Tag Table: | Select | Tag | Count |.
  - Features: Sort by count, inline edit, multi-select.
  - Operations: Merge, Delete, Rename.
- Section C - Output: Preview, Export to file (`/data/wildcard.txt`).

### 4. Docker & CI/CD
- Base Image: python:3.12-slim
- Volume Mounts: `./input:/input`, `./data:/data`
- CI/CD: GitHub Actions for Docker Hub push with branch-based tagging.

### 5. Logging & Persistence
- Logging: Centralized logging with startup configuration output to stdout. Using `ENV PYTHONUNBUFFERED=1` and `force=True` in `logging.basicConfig` to ensure immediate visibility in Docker logs. Added "Test Log Output" button.
- State Persistence: Ability to Save/Load current state (tag counts) to/from `/data/state.json`.
