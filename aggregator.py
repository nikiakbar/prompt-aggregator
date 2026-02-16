from collections import Counter
import logging

logger = logging.getLogger(__name__)

def aggregate_tags(tag_lists):
    """
    Counts occurrences of each tag in a list of tag lists.
    Returns a dictionary of {tag: count}.
    """
    logger.debug(f"Aggregating tags from {len(tag_lists)} lists")
    counter = Counter()
    for tags in tag_lists:
        counter.update(tags)
    logger.info(f"Aggregation complete. Found {len(counter)} unique tags.")
    return dict(counter)
