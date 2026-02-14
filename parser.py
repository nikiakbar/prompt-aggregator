import re

def normalize_tag(tag):
    """
    Normalizes a single tag:
    - lowercase
    - trim whitespace
    - remove Stable Diffusion weights like (word:1.2) or [word]
    """
    if not tag:
        return ""

    # Lowercase
    tag = tag.lower()

    # Remove weight suffix like :1.2
    tag = re.sub(r':[0-9.]+', '', tag)

    # Remove wrapping parentheses, brackets, and braces
    # Using strip for multiple layers like (((tag)))
    tag = tag.strip('()[]{} ')

    return tag.strip()

def parse_prompt(prompt):
    """
    Splits prompt by comma and normalizes each tag.
    Returns a list of tags.
    """
    if not prompt:
        return []

    # Split by comma
    segments = prompt.split(',')

    # Normalize segments and filter out empty ones
    tags = [normalize_tag(s) for s in segments]
    return [t for t in tags if t]
