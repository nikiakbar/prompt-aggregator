from collections import Counter

def aggregate_tags(tag_lists):
    """
    Counts occurrences of each tag in a list of tag lists.
    Returns a dictionary of {tag: count}.
    """
    counter = Counter()
    for tags in tag_lists:
        counter.update(tags)
    return dict(counter)
