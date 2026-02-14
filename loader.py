import os
import logging
from PIL import Image
from PIL.ExifTags import TAGS

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = ('.png', '.webp', '.jpg', '.jpeg')

import json

def extract_prompt(image_path):
    """
    Robustly extracts the positive prompt from image metadata.
    Supports A1111, ComfyUI, and various EXIF/IPTC formats.
    """
    try:
        with Image.open(image_path) as img:
            info = img.info
            meta_sources = []

            # 1. Collect all candidates from img.info (PNG, WebP chunks)
            for k, v in info.items():
                try:
                    # Handle both string and bytes keys
                    key = k.decode('utf-8', errors='ignore').lower() if isinstance(k, bytes) else str(k).lower()
                    if key in ['parameters', 'prompt', 'comment', 'description', 'usercomment']:
                        val = v.decode('utf-8', errors='ignore') if isinstance(v, bytes) else str(v)
                        if val.strip():
                            meta_sources.append(val.strip())
                except:
                    continue

            # 2. Collect from EXIF (JPEG, WebP)
            try:
                exif = img.getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        if tag_name in ['UserComment', 'ImageDescription', 'Software', 'Comment']:
                            if isinstance(value, bytes):
                                # Strip common EXIF encoding prefixes
                                if value.startswith(b'ASCII\x00\x00\x00'):
                                    decoded = value[8:].decode('utf-8', errors='ignore')
                                elif value.startswith(b'UNICODE\x00'):
                                    decoded = value[8:].decode('utf-16', errors='ignore')
                                else:
                                    decoded = value.decode('utf-8', errors='ignore')
                            else:
                                decoded = str(value)
                            if decoded.strip():
                                meta_sources.append(decoded.strip())
            except:
                pass

            if not meta_sources:
                return ""

            # 3. Process candidates to find the actual prompt
            for candidate in meta_sources:
                # Case A: A1111/Standard parameters string
                if 'Negative prompt:' in candidate or 'Steps:' in candidate:
                    if 'Negative prompt:' in candidate:
                        return candidate.split('Negative prompt:')[0].strip()
                    return candidate.split('Steps:')[0].strip()

                # Case B: ComfyUI JSON
                if candidate.startswith('{') and '"inputs"' in candidate:
                    try:
                        data = json.loads(candidate)
                        prompts = []
                        # Heuristic: find CLIPTextEncode or similar nodes
                        for node in data.values():
                            if isinstance(node, dict) and 'inputs' in node:
                                text = node['inputs'].get('text')
                                if isinstance(text, str) and len(text) > 3:
                                    # Avoid common non-prompt inputs
                                    if not any(x in text.lower() for x in ['embedding:', 'checkpoint']):
                                        prompts.append(text)
                        if prompts:
                            # Return the longest one (usually the positive prompt)
                            return max(prompts, key=len).strip()
                    except:
                        pass

            # Fallback: Return the longest candidate that isn't a short technical string
            # This handles cases where 'prompt' key is used directly as a string.
            return max(meta_sources, key=len).strip()
    except Exception as e:
        logger.error(f"Error extracting prompt from {image_path}: {e}")
        return ""

def get_image_files(directory):
    """Returns a list of supported image files in the directory recursively."""
    files = []
    if os.path.isdir(directory):
        for root, dirs, filenames in os.walk(directory):
            for f in filenames:
                if f.lower().endswith(SUPPORTED_EXTENSIONS):
                    files.append(os.path.join(root, f))
    return files

def get_image_files_generator(directory):
    """Yields supported image files in the directory recursively (lazy iteration)."""
    if os.path.isdir(directory):
        for root, dirs, filenames in os.walk(directory):
            for f in filenames:
                if f.lower().endswith(SUPPORTED_EXTENSIONS):
                    yield os.path.join(root, f)
