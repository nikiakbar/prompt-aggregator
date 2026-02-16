import gradio as gr
import os
import logging
import sys
import json
from loader import get_image_files_generator, extract_prompt
from parser import parse_prompt
from aggregator import aggregate_tags
from editor import delete_tags, rename_tag, merge_tags

# Configure logging for the root logger to capture all module output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True  # Overrides any existing logging configuration (e.g. from libraries)
)
logger = logging.getLogger("prompt-aggregator")

def process_path(path, progress=gr.Progress()):
    logger.info(f"Processing path: {path}")
    if not path:
        logger.warning("No path provided.")
        return "Current active path: None", 0, [], "", {}
    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return f"Path does not exist: {path}", 0, [], "", {}

    # Lazy iteration: first pass to get total count for progress bar
    total_files = sum(1 for _ in get_image_files_generator(path))
    logger.info(f"Found {total_files} images in {path}")

    if total_files == 0:
        return f"Current active path: {path}", 0, [], "", {}

    tag_counts = {}
    batch_size = 10

    # Second pass: lazy iteration for processing
    for i, f in enumerate(get_image_files_generator(path)):
        prompt = extract_prompt(f)
        tags = parse_prompt(prompt)

        # Update counts
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Update progress and log in batches
        if (i + 1) % batch_size == 0 or (i + 1) == total_files:
            if progress:
                progress((i + 1) / total_files, desc=f"Processed {i + 1}/{total_files}")
            logger.info(f"Progress: {i + 1}/{total_files} images processed")

    # Sort by count descending initially
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    df_data = [[False, tag, count] for tag, count in sorted_tags]
    preview = "\n".join([tag for tag, count in sorted_tags])

    return f"Current active path: {path}", total_files, df_data, preview, tag_counts

def update_from_df(df_data):
    # df_data is a list of lists: [[Select, Tag, Count], ...]
    new_tag_counts = {}
    for row in df_data:
        try:
            tag = str(row[1]).strip()
            count = int(row[2])
            if tag:
                if tag in new_tag_counts:
                    new_tag_counts[tag] += count
                else:
                    new_tag_counts[tag] = count
        except (IndexError, ValueError, TypeError):
            continue

    sorted_tags = sorted(new_tag_counts.items(), key=lambda x: x[1], reverse=True)
    preview = "\n".join([tag for tag, count in sorted_tags])
    return preview, new_tag_counts

def handle_delete(df_data, tag_counts):
    tags_to_delete = [row[1] for row in df_data if row[0]]
    logger.info(f"Deleting tags: {tags_to_delete}")
    new_tag_counts = delete_tags(tag_counts, tags_to_delete)

    sorted_tags = sorted(new_tag_counts.items(), key=lambda x: x[1], reverse=True)
    new_df_data = [[False, tag, count] for tag, count in sorted_tags]
    preview = "\n".join([tag for tag, count in sorted_tags])
    return new_df_data, preview, new_tag_counts

def handle_rename(df_data, tag_counts, new_name):
    selected = [row[1] for row in df_data if row[0]]
    if len(selected) != 1:
        logger.warning(f"Rename failed: {len(selected)} tags selected (exactly 1 required).")
        gr.Warning("Please select exactly one tag to rename.")
        return df_data, "\n".join(sorted(tag_counts.keys())), tag_counts

    old_name = selected[0]
    logger.info(f"Renaming tag '{old_name}' to '{new_name}'")
    new_tag_counts = rename_tag(tag_counts, old_name, new_name)

    sorted_tags = sorted(new_tag_counts.items(), key=lambda x: x[1], reverse=True)
    new_df_data = [[False, tag, count] for tag, count in sorted_tags]
    preview = "\n".join([tag for tag, count in sorted_tags])
    return new_df_data, preview, new_tag_counts

def handle_merge(df_data, tag_counts, target_name):
    selected = [row[1] for row in df_data if row[0]]
    if not selected:
        logger.warning("Merge failed: No tags selected.")
        gr.Warning("No tags selected to merge.")
        return df_data, "\n".join(sorted(tag_counts.keys())), tag_counts

    logger.info(f"Merging tags {selected} into '{target_name}'")
    new_tag_counts = merge_tags(tag_counts, selected, target_name)

    sorted_tags = sorted(new_tag_counts.items(), key=lambda x: x[1], reverse=True)
    new_df_data = [[False, tag, count] for tag, count in sorted_tags]
    preview = "\n".join([tag for tag, count in sorted_tags])
    return new_df_data, preview, new_tag_counts

def export_to_file(tag_counts):
    if not tag_counts:
        logger.warning("Export failed: No tags to export.")
        return "No tags to export."
    try:
        os.makedirs("/data", exist_ok=True)
        output_path = "/data/wildcard.txt"
        logger.info(f"Exporting {len(tag_counts)} tags to {output_path}")
        sorted_tags = sorted(tag_counts.keys())
        with open(output_path, "w") as f:
            f.write("\n".join(sorted_tags))
        logger.info("Export successful.")
        return f"Successfully exported to {output_path}"
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return f"Export failed: {e}"

def save_app_state(tag_counts):
    if not tag_counts:
        logger.warning("Save state failed: No data to save.")
        return "No data to save."
    try:
        os.makedirs("/data", exist_ok=True)
        state_path = "/data/state.json"
        logger.info(f"Saving app state to {state_path}")
        with open(state_path, "w") as f:
            json.dump(tag_counts, f, indent=2)
        logger.info("Save state successful.")
        return f"State saved to {state_path}"
    except Exception as e:
        logger.error(f"Save state failed: {e}")
        return f"Save failed: {e}"

def test_log_output():
    logger.info("--- LOG TEST START ---")
    logger.info("This is a test log message at INFO level.")
    logger.warning("This is a test log message at WARNING level.")
    logger.error("This is a test log message at ERROR level.")
    logger.info("--- LOG TEST END ---")
    return "Log messages sent to stdout. Check your container logs."

def load_app_state():
    state_path = "/data/state.json"
    if not os.path.exists(state_path):
        logger.warning(f"Load state failed: {state_path} does not exist.")
        return {}, [], "", f"File not found: {state_path}"
    try:
        logger.info(f"Loading app state from {state_path}")
        with open(state_path, "r") as f:
            tag_counts = json.load(f)

        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        df_data = [[False, tag, count] for tag, count in sorted_tags]
        preview = "\n".join([tag for tag, count in sorted_tags])

        logger.info("Load state successful.")
        return tag_counts, df_data, preview, f"State loaded from {state_path}"
    except Exception as e:
        logger.error(f"Load state failed: {e}")
        return {}, [], "", f"Load failed: {e}"

# UI Construction
with gr.Blocks(title="SD Prompt Tag Aggregator") as demo:
    tag_counts_state = gr.State({})

    gr.Markdown("## Stable Diffusion Prompt Tag Aggregator")

    with gr.Group():
        gr.Markdown("### Section A — Input")
        with gr.Row():
            path_input = gr.Textbox(label="Directory Path", value="/input", placeholder="/input/images", scale=4)
            process_btn = gr.Button("Process", variant="primary", scale=1)

        with gr.Row():
            active_path_display = gr.Markdown("Current active path: None")
            images_found_display = gr.Number(label="Images Found", interactive=False)

    with gr.Group():
        gr.Markdown("### Section B — Tag Table")
        tag_table = gr.Dataframe(
            headers=["Select", "Tag", "Count"],
            datatype=["bool", "str", "number"],
            column_count=(3, "fixed"),
            type="array",
            interactive=True,
            label="Aggregate Tags (Edit tag text inline or use buttons below)"
        )

        with gr.Row():
            new_name_input = gr.Textbox(label="New/Target Name", placeholder="Enter tag name for Rename/Merge")
            rename_btn = gr.Button("Rename selected tag")
            merge_btn = gr.Button("Merge selected tags")
            delete_btn = gr.Button("Delete selected tags", variant="stop")

    with gr.Group():
        gr.Markdown("### Section C — Output & Persistence")
        preview_area = gr.TextArea(label="Wildcard List Preview", interactive=False, lines=10)
        with gr.Row():
            export_btn = gr.Button("Export Wildcard List", variant="primary")
            save_state_btn = gr.Button("Save State", variant="secondary")
            load_state_btn = gr.Button("Load State", variant="secondary")
        with gr.Row():
            test_log_btn = gr.Button("Test Log Output", variant="secondary")
        export_status = gr.Markdown("")

    # Event Handlers
    def on_process_click(path, progress=gr.Progress()):
        act_path, img_count, df_data, preview, tag_counts = process_path(path, progress=progress)
        return act_path, img_count, df_data, preview, tag_counts

    process_btn.click(
        on_process_click,
        inputs=[path_input],
        outputs=[active_path_display, images_found_display, tag_table, preview_area, tag_counts_state]
    )

    def on_table_edit(df_data):
        preview, new_tag_counts = update_from_df(df_data)
        return preview, new_tag_counts

    # Use input to update preview and state when table is edited
    tag_table.input(
        on_table_edit,
        inputs=[tag_table],
        outputs=[preview_area, tag_counts_state]
    )

    delete_btn.click(
        handle_delete,
        inputs=[tag_table, tag_counts_state],
        outputs=[tag_table, preview_area, tag_counts_state]
    )

    rename_btn.click(
        handle_rename,
        inputs=[tag_table, tag_counts_state, new_name_input],
        outputs=[tag_table, preview_area, tag_counts_state]
    )

    merge_btn.click(
        handle_merge,
        inputs=[tag_table, tag_counts_state, new_name_input],
        outputs=[tag_table, preview_area, tag_counts_state]
    )

    export_btn.click(
        export_to_file,
        inputs=[tag_counts_state],
        outputs=[export_status]
    )

    save_state_btn.click(
        save_app_state,
        inputs=[tag_counts_state],
        outputs=[export_status]
    )

    def on_load_click():
        tag_counts, df_data, preview, status = load_app_state()
        return tag_counts, df_data, preview, status

    load_state_btn.click(
        on_load_click,
        outputs=[tag_counts_state, tag_table, preview_area, export_status]
    )

    test_log_btn.click(
        test_log_output,
        outputs=[export_status]
    )

if __name__ == "__main__":
    SERVER_NAME = "0.0.0.0"
    PORT = 4000

    # Ensure logs are visible immediately
    print("Initializing Application...", flush=True)
    logger.info("Starting Stable Diffusion Prompt Tag Aggregator")
    logger.info(f"Configuration: SERVER_NAME={SERVER_NAME}, PORT={PORT}")
    logger.info("Input volume mount expected at: /input")
    logger.info("Output volume mount expected at: /data")
    logger.info("Python version: " + sys.version)

    demo.launch(server_name=SERVER_NAME, server_port=PORT)
