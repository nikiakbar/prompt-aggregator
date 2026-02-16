import re
import logging
import string

logger = logging.getLogger(__name__)

# List of prefixes that indicate a tag is likely a generation parameter rather than a prompt tag
PARAMETER_PREFIXES = [
    'steps:', 'sampler:', 'cfg scale:', 'seed:', 'size:', 'model hash:', 'model:',
    'variation seed:', 'denoising strength:', 'clip skip:', 'ensd:', 'hires upscale:',
    'hires steps:', 'hires upscaler:', 'lora hashes:', 'ti hashes:', 'version:',
    'hashes:', 'template:', 'negative prompt:'
]

def is_printable(s):
    """Checks if a string consists mostly of printable characters."""
    if not s:
        return True
    # Count printable characters. ord(c) > 127 handles common unicode like emojis or accented chars
    # but we want to avoid control characters.
    printable = sum(1 for c in s if c.isprintable() or c in "\n\r\t")
    return (printable / len(s)) > 0.9 if len(s) > 0 else True

def clean_text(text):
    """Removes non-printable control characters from text."""
    if not text:
        return ""
    # Remove control characters except for common ones like newline, tab
    # We use isprintable() which is built-in and handles unicode correctly
    return "".join(c for c in text if c.isprintable() or c in " ")

def normalize_tag(tag):
    """
    Normalizes a single tag:
    - lowercase (except for LoRAs which might want to preserve case, but usually tags are lowercased)
    - trim whitespace
    - remove Stable Diffusion weights like (word:1.2)
    - filters out generation parameters
    """
    if not tag:
        return ""

    # Clean non-printable characters and extra whitespace
    tag = clean_text(tag).strip()

    # Check if it's a generation parameter
    tag_lower = tag.lower()
    for prefix in PARAMETER_PREFIXES:
        if tag_lower.startswith(prefix):
            return ""

    # LoRA tags like <lora:name:weight> - user wants to keep them.
    # We should NOT strip them or lowercase them if they are technical,
    # but the requirement says lowercase all tags.
    # Let's lowercase for consistency unless it's a LoRA?
    # Actually, let's just lowercase everything as requested in original requirements.

    # Remove weight suffix like : 1.2 or :1.2 (handling optional spaces)
    # BUT we must NOT remove it from LoRAs like <lora:name:1.2>
    if not (tag.startswith('<') and tag.endswith('>')):
        tag = re.sub(r':\s*[0-9.]+', '', tag)

    tag = tag.lower()

    # Remove wrapping parentheses, brackets, and braces iteratively
    # Don't do this for LoRAs <...>
    if not (tag.startswith('<') and tag.endswith('>')):
        last_tag = None
        while tag != last_tag:
            last_tag = tag
            tag = tag.strip('()[]{} \n\r\t')

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
