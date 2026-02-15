import os
import logging
import json
import re
from PIL import Image
from PIL.ExifTags import TAGS

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = ('.png', '.webp', '.jpg', '.jpeg')

def extract_prompt(image_path):
    """
    Robustly extracts the positive prompt from image metadata.
    Handles A1111, ComfyUI, InvokeAI, NovelAI and more.
    """
    try:
        with Image.open(image_path) as img:
            info = img.info
            all_metadata = {}

            # 1. Collect from img.info (PNG, WebP chunks)
            for k, v in info.items():
                try:
                    key = k.decode('utf-8', errors='ignore').lower() if isinstance(k, bytes) else str(k).lower()
                    val = v.decode('utf-8', errors='ignore') if isinstance(v, bytes) else str(v)
                    if val.strip():
                        all_metadata[key] = val.strip()
                except:
                    continue

            # 2. Collect from EXIF (JPEG, WebP)
            try:
                exif = img.getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        if isinstance(tag_name, str):
                            key = tag_name.lower()
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
                                all_metadata[key] = decoded.strip()
            except:
                pass

            if not all_metadata:
                return ""

            # 3. Strategy: Look for A1111-style parameters in ANY field
            for key, val in all_metadata.items():
                v_lower = val.lower()
                # Check for common markers in A1111 parameters string
                if 'negative prompt:' in v_lower or 'steps:' in v_lower:
                    # Case-insensitive split
                    if 'negative prompt:' in v_lower:
                        parts = re.split(r'negative prompt:', val, flags=re.IGNORECASE)
                        return parts[0].strip()
                    if 'steps:' in v_lower:
                        parts = re.split(r'steps:', val, flags=re.IGNORECASE)
                        return parts[0].strip()

            # 4. Strategy: Look for ComfyUI/JSON in specific keys
            # ComfyUI often uses 'prompt' or 'workflow'. InvokeAI uses 'sd_metadata'.
            for key in ['prompt', 'workflow', 'sd_metadata', 'sd-metadata', 'metadata']:
                val = all_metadata.get(key)
                if val and val.strip().startswith('{'):
                    try:
                        data = json.loads(val)
                        if isinstance(data, dict):
                            # ComfyUI heuristic: look for CLIPTextEncode nodes
                            prompts = []
                            for node in data.values():
                                if isinstance(node, dict) and 'inputs' in node:
                                    inputs = node['inputs']
                                    txt = inputs.get('text') or inputs.get('string')
                                    if isinstance(txt, str) and len(txt) > 3:
                                        # Filter out technical stuff
                                        if not any(x in txt.lower() for x in ['embedding:', 'checkpoint', 'lora:']):
                                            prompts.append(txt)
                            if prompts:
                                return max(prompts, key=len).strip()

                            # InvokeAI/Generic JSON prompt keys
                            for p_key in ['positive_prompt', 'prompt', 'text']:
                                if p_key in data and isinstance(data[p_key], str):
                                    return data[p_key].strip()
                    except:
                        pass

            # 5. Strategy: Check priority keys for plain text
            priority_keys = ['parameters', 'prompt', 'description', 'comment', 'usercomment', 'dream', 'software']
            for key in priority_keys:
                val = all_metadata.get(key)
                if val:
                    # InvokeAI legacy 'dream' format
                    if '--' in val and any(x in val for x in ['--steps', '--cfg', '--seed']):
                        return val.split('--')[0].strip()

                    # If not JSON, assume it's the prompt
                    if not (val.startswith('{') or val.startswith('[')):
                        if len(val) > 2:
                            return val.strip()

            # 6. Fallback: return the longest non-JSON string found anywhere
            non_json_meta = [v for v in all_metadata.values() if not (v.startswith('{') or v.startswith('['))]
            if non_json_meta:
                # Filter out likely technical tags
                candidates = [v for v in non_json_meta if len(v.split()) > 1]
                if candidates:
                    return max(candidates, key=len).strip()
                return max(non_json_meta, key=len).strip()

            return ""
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
