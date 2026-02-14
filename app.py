import gradio as gr
import os
from loader import get_image_files, extract_prompt
from parser import parse_prompt
from aggregator import aggregate_tags
from editor import delete_tags, rename_tag, merge_tags

def process_path(path):
    if not path:
        return "Current active path: None", 0, [], "", {}
    if not os.path.exists(path):
        return f"Path does not exist: {path}", 0, [], "", {}

    files = get_image_files(path)
    tag_lists = []
    for f in files:
        prompt = extract_prompt(f)
        tags = parse_prompt(prompt)
        tag_lists.append(tags)

    tag_counts = aggregate_tags(tag_lists)

    # Sort by count descending initially
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    df_data = [[False, tag, count] for tag, count in sorted_tags]
    preview = "\n".join([tag for tag, count in sorted_tags])

    return f"Current active path: {path}", len(files), df_data, preview, tag_counts

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
    new_tag_counts = delete_tags(tag_counts, tags_to_delete)

    sorted_tags = sorted(new_tag_counts.items(), key=lambda x: x[1], reverse=True)
    new_df_data = [[False, tag, count] for tag, count in sorted_tags]
    preview = "\n".join([tag for tag, count in sorted_tags])
    return new_df_data, preview, new_tag_counts

def handle_rename(df_data, tag_counts, new_name):
    selected = [row[1] for row in df_data if row[0]]
    if len(selected) != 1:
        gr.Warning("Please select exactly one tag to rename.")
        return df_data, "\n".join(sorted(tag_counts.keys())), tag_counts

    old_name = selected[0]
    new_tag_counts = rename_tag(tag_counts, old_name, new_name)

    sorted_tags = sorted(new_tag_counts.items(), key=lambda x: x[1], reverse=True)
    new_df_data = [[False, tag, count] for tag, count in sorted_tags]
    preview = "\n".join([tag for tag, count in sorted_tags])
    return new_df_data, preview, new_tag_counts

def handle_merge(df_data, tag_counts, target_name):
    selected = [row[1] for row in df_data if row[0]]
    if not selected:
        gr.Warning("No tags selected to merge.")
        return df_data, "\n".join(sorted(tag_counts.keys())), tag_counts

    new_tag_counts = merge_tags(tag_counts, selected, target_name)

    sorted_tags = sorted(new_tag_counts.items(), key=lambda x: x[1], reverse=True)
    new_df_data = [[False, tag, count] for tag, count in sorted_tags]
    preview = "\n".join([tag for tag, count in sorted_tags])
    return new_df_data, preview, new_tag_counts

def export_to_file(tag_counts):
    if not tag_counts:
        return "No tags to export."
    try:
        os.makedirs("/output", exist_ok=True)
        output_path = "/output/wildcard.txt"
        sorted_tags = sorted(tag_counts.keys())
        with open(output_path, "w") as f:
            f.write("\n".join(sorted_tags))
        return f"Successfully exported to {output_path}"
    except Exception as e:
        return f"Export failed: {e}"

# UI Construction
with gr.Blocks(title="SD Prompt Tag Aggregator") as demo:
    tag_counts_state = gr.State({})

    gr.Markdown("## Stable Diffusion Prompt Tag Aggregator")

    with gr.Group():
        gr.Markdown("### Section A — Input")
        with gr.Row():
            path_input = gr.Textbox(label="Directory Path", placeholder="/data/images", scale=4)
            process_btn = gr.Button("Process", variant="primary", scale=1)

        with gr.Row():
            active_path_display = gr.Markdown("Current active path: None")
            images_found_display = gr.Number(label="Images Found", interactive=False)

    with gr.Group():
        gr.Markdown("### Section B — Tag Table")
        tag_table = gr.Dataframe(
            headers=["Select", "Tag", "Count"],
            datatype=["bool", "str", "number"],
            col_count=(3, "fixed"),
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
        gr.Markdown("### Section C — Output")
        preview_area = gr.TextArea(label="Wildcard List Preview", interactive=False, lines=10)
        export_btn = gr.Button("Export to file", variant="primary")
        export_status = gr.Markdown("")

    # Event Handlers
    def on_process_click(path):
        act_path, img_count, df_data, preview, tag_counts = process_path(path)
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

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=4000)
