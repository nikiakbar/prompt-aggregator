import os
import logging
import json
import re
from PIL import Image
from PIL.ExifTags import TAGS
from parser import is_printable, clean_text

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = ('.png', '.webp', '.jpg', '.jpeg')

# Keywords commonly found in negative prompts
NEGATIVE_KEYWORDS = [
    'lowres', 'bad anatomy', 'bad hands', 'text', 'error', 'missing fingers',
    'extra digit', 'fewer digits', 'cropped', 'worst quality', 'low quality',
    'normal quality', 'jpeg artifacts', 'signature', 'watermark', 'username',
    'blurry', 'bad feet', 'easynegative', 'ng_deepnegative', 'bad-hands-5',
    'bad_prompt', 'extra limbs', 'mutation'
]

def is_likely_negative(text):
    """Heuristic to check if a string is likely a negative prompt."""
    if not text:
        return False
    text_lower = text.lower()
    match_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)
    return match_count >= 2

def decode_metadata_value(value):
    """Robustly decodes metadata values (bytes/strings) into clean UTF-8 strings."""
    if isinstance(value, bytes):
        # Common EXIF encoding prefixes
        if value.startswith(b'ASCII\x00\x00\x00'):
            return value[8:].decode('utf-8', errors='ignore').strip()
        if value.startswith(b'UNICODE\x00'):
            # UNICODE prefix is 8 bytes. The rest is usually UTF-16.
            try:
                return value[8:].decode('utf-16', errors='ignore').strip()
            except:
                return value[8:].decode('utf-8', errors='ignore').strip()
        # Fallback decodings
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                decoded = value.decode(enc).strip()
                if is_printable(decoded):
                    return decoded
            except:
                continue
        return value.decode('utf-8', errors='ignore').strip()
    return str(value).strip()

def extract_prompt(image_path):
    """
    Robustly extracts ONLY the positive prompt from image metadata.
    Specifically designed to ignore negative prompts and technical parameters.
    """
    try:
        with Image.open(image_path) as img:
            info = img.info
            all_metadata = {}

            # 1. Collect from img.info (PNG, WebP chunks)
            for k, v in info.items():
                try:
                    key = k.decode('utf-8', errors='ignore').lower() if isinstance(k, bytes) else str(k).lower()
                    val = decode_metadata_value(v)
                    if val and is_printable(val):
                        all_metadata[key] = clean_text(val)
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
                            val = decode_metadata_value(value)
                            if val and is_printable(val):
                                all_metadata[key] = clean_text(val)
            except:
                pass

            if not all_metadata:
                return ""

            # 3. Strategy: Look for A1111-style parameters string
            for key, val in all_metadata.items():
                v_lower = val.lower()
                if 'negative prompt:' in v_lower or 'steps:' in v_lower:
                    if 'negative prompt:' in v_lower:
                        parts = re.split(r'negative prompt:', val, flags=re.IGNORECASE)
                        return parts[0].strip()
                    if 'steps:' in v_lower:
                        parts = re.split(r'steps:', val, flags=re.IGNORECASE)
                        return parts[0].strip()

            # 4. Strategy: Look for ComfyUI/JSON
            for key in ['prompt', 'workflow', 'sd_metadata', 'sd-metadata', 'metadata']:
                val = all_metadata.get(key)
                if val and val.strip().startswith('{'):
                    try:
                        data = json.loads(val)
                        if isinstance(data, dict):
                            candidates = []
                            for node in data.values():
                                if isinstance(node, dict) and 'inputs' in node:
                                    inputs = node['inputs']
                                    txt = inputs.get('text') or inputs.get('string')
                                    if isinstance(txt, str) and len(txt) > 3:
                                        if not any(x in txt.lower() for x in ['embedding:', 'checkpoint', 'lora:']):
                                            candidates.append(txt)

                            if candidates:
                                positive_candidates = [c for c in candidates if not is_likely_negative(c)]
                                if positive_candidates:
                                    return max(positive_candidates, key=len).strip()
                                return max(candidates, key=len).strip()

                            if 'positive_prompt' in data:
                                return str(data['positive_prompt']).strip()
                    except:
                        pass

            # 5. Strategy: Check priority keys for plain text
            priority_keys = ['parameters', 'prompt', 'description', 'comment', 'usercomment', 'dream', 'software']
            for key in priority_keys:
                val = all_metadata.get(key)
                if val:
                    if '--' in val and any(x in val for x in ['--steps', '--cfg', '--seed']):
                        return val.split('--')[0].strip()

                    if not (val.startswith('{') or val.startswith('[')):
                        if len(val) > 2 and not is_likely_negative(val):
                            return val.strip()

            # 6. Fallback: return the longest printable string that doesn't look negative
            candidates = [v for v in all_metadata.values() if not (v.startswith('{') or v.startswith('['))]
            candidates = [v for v in candidates if len(v.split()) > 1 and is_printable(v)]

            positive_candidates = [c for c in candidates if not is_likely_negative(c)]
            if positive_candidates:
                return max(positive_candidates, key=len).strip()

            if candidates:
                return max(candidates, key=len).strip()

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
