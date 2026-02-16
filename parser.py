import re
import logging
import string

logger = logging.getLogger(__name__)

def is_printable(s):
    """Checks if a string consists mostly of printable characters."""
    if not s:
        return True
    printable = sum(1 for c in s if c in string.printable or ord(c) > 127)
    return (printable / len(s)) > 0.9

def clean_text(text):
    """Removes non-printable control characters from text."""
    if not text:
        return ""
    # Remove control characters except for common ones like newline, tab
    return "".join(c for c in text if c.isprintable() or c in "\n\r\t")

def normalize_tag(tag):
    """
    Normalizes a single tag:
    - remove LoRA/technical tags like <lora:...>
    - remove embedding tags like (embedding:...)
    - lowercase
    - trim whitespace
    - remove Stable Diffusion weights like (word:1.2)
    """
    if not tag:
        return ""

    # Clean non-printable characters
    tag = clean_text(tag)

    # Remove LoRA and other <...> content
    tag = re.sub(r'<[^>]+>', '', tag)

    # Remove (embedding:...) content
    tag = re.sub(r'\(embedding:[^)]+\)', '', tag)

    # Lowercase
    tag = tag.lower()

    # Remove weight suffix like : 1.2 or :1.2 (handling optional spaces)
    tag = re.sub(r':\s*[0-9.]+', '', tag)

    # Remove wrapping parentheses, brackets, and braces iteratively
    last_tag = None
    while tag != last_tag:
        last_tag = tag
        tag = tag.strip('()[]{} \n\r\t')

    return tag

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
