# Stable Diffusion Prompt Tag Aggregator

A Python application with a Gradio UI designed to aggregate Stable Diffusion positive prompt tags from image metadata into a unified wildcard list.

## Features

- **Recursive Metadata Extraction**: Scans directories recursively for `.png`, `.webp`, `.jpg`, and `.jpeg` files.
- **Robust Metadata Support**: Handles Automatic1111 (`parameters`), ComfyUI (`prompt`), and standard JPEG EXIF (`UserComment`) metadata.
- **Tag Normalization**: Automatically cleans tags by:
  - Converting to lowercase.
  - Trimming whitespace.
  - Removing Stable Diffusion weights (e.g., `(word:1.2)` or `[word]`).
- **Interactive Management**:
  - **Inline Editing**: Modify tag names or counts directly in the table.
  - **Multi-select Operations**: Merge multiple tags into a single entry or delete unwanted tags.
  - **Rename**: Easily rename individual tags while preserving counts.
- **Wildcard Export**: Generates a sorted list of unique tags for use as a wildcard file.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Quick Start

1. **Prepare your folders**:
   Place your images in a local directory (e.g., `./data`).

2. **Run the application**:
   ```bash
   docker compose up --build
   ```

3. **Access the UI**:
   Open your browser and navigate to `http://localhost:4000`.

## Usage Workflow

1. **Input**: Enter the directory path inside the container (default is `/input`) and click **Process**.
2. **Review**: See the aggregated tags and their counts in the interactive table.
3. **Refine**:
   - Select rows to **Merge** into a new tag name.
   - Select rows to **Delete**.
   - Select a single row to **Rename**.
   - Edit the **Tag** text directly in the table for quick corrections.
4. **Export**: Click **Export to file** to save your wildcard list to `/data/wildcard.txt` inside the container (mapped to your host's `./output` folder).

## Configuration

The application uses Docker volume mounts defined in `compose.yaml`:

- `./data:/input`: Maps your local image folder to the container's input path.
- `./output:/data`: Maps the container's export folder to your local machine.

## Technical Details

- **Language**: Python 3.12
- **UI Framework**: Gradio
- **Base Image**: python:3.12-slim
- **Port**: 4000
