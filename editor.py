import logging

logger = logging.getLogger(__name__)

def delete_tags(tag_dict, tags_to_delete):
    """Deletes specified tags from the dictionary."""
    new_dict = tag_dict.copy()
    for tag in tags_to_delete:
        if tag in new_dict:
            del new_dict[tag]
    return new_dict

def rename_tag(tag_dict, old_name, new_name):
    """Renames a tag and merges counts if the new name already exists."""
    if not old_name or not new_name or old_name == new_name:
        return tag_dict

    new_dict = tag_dict.copy()
    if old_name in new_dict:
        count = new_dict.pop(old_name)
        if new_name in new_dict:
            new_dict[new_name] += count
        else:
            new_dict[new_name] = count
    return new_dict

def merge_tags(tag_dict, tags_to_merge, target_name):
    """Merges multiple tags into a target tag name."""
    if not target_name or not tags_to_merge:
        return tag_dict

    new_dict = tag_dict.copy()
    total_count = 0
    for tag in tags_to_merge:
        if tag in new_dict:
            total_count += new_dict.pop(tag)

    if target_name in new_dict:
        new_dict[target_name] += total_count
    else:
        new_dict[target_name] = total_count
    return new_dict
