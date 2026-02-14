import os
from PIL import Image
from PIL.ExifTags import TAGS

SUPPORTED_EXTENSIONS = ('.png', '.webp', '.jpg', '.jpeg')

def extract_prompt(image_path):
    """
    Extracts the positive prompt from image metadata.
    Supported: A1111 (parameters), ComfyUI (prompt), and EXIF UserComment for JPEG.
    """
    try:
        with Image.open(image_path) as img:
            info = img.info
            prompt = ""

            # Case 1: PNG/WebP with 'parameters' (A1111)
            if 'parameters' in info:
                params = info['parameters']
                if 'Negative prompt:' in params:
                    prompt = params.split('Negative prompt:')[0]
                elif 'Steps:' in params:
                    prompt = params.split('Steps:')[0]
                else:
                    prompt = params
            # Case 2: PNG/WebP with 'prompt'
            elif 'prompt' in info:
                prompt = info['prompt']
            # Case 3: JPEG or others with EXIF
            else:
                exif = img.getexif()
                if exif:
                    for tag_id in exif:
                        tag_name = TAGS.get(tag_id, tag_id)
                        if tag_name == 'UserComment':
                            value = exif.get(tag_id)
                            if isinstance(value, bytes):
                                # Strip potential encoding prefix (e.g., ASCII\x00\x00\x00)
                                if value.startswith(b'ASCII\x00\x00\x00'):
                                    value = value[8:].decode('utf-8', errors='ignore')
                                elif value.startswith(b'UNICODE\x00'):
                                    value = value[8:].decode('utf-16', errors='ignore')
                                else:
                                    value = value.decode('utf-8', errors='ignore')

                            if 'Negative prompt:' in value:
                                prompt = value.split('Negative prompt:')[0]
                            elif 'Steps:' in value:
                                prompt = value.split('Steps:')[0]
                            else:
                                prompt = value
                            break

            return prompt.strip()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
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
