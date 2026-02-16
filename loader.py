import os
import logging
import re
import piexif
import piexif.helper
from PIL import Image

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = ('.png', '.webp', '.jpg', '.jpeg')

# Keywords commonly found in negative prompts
NEGATIVE_KEYWORDS = [
    'lowres', 'bad anatomy', 'bad hands', 'missing fingers',
    'extra digit', 'fewer digits', 'cropped', 'worst quality', 'low quality',
    'normal quality', 'jpeg artifacts', 'signature', 'watermark', 'username',
    'blurry', 'bad feet', 'easynegative', 'ng_deepnegative', 'bad-hands-5',
    'bad_prompt', 'extra limbs', 'mutation'
]

def is_likely_negative(text):
    """Heuristic to check if a string is likely a negative prompt."""
    if not text:
        return False
    text_lower = text.lower().strip()

    # If it starts with "negative prompt:", it definitely is one
    if text_lower.startswith('negative prompt:'):
        return True

    match_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)
    # If it contains many negative keywords, it's likely negative
    return match_count >= 2

def decode_exif_user_comment(user_comment):
    """
    Decodes the UserComment field from EXIF data using smart heuristics.
    Handles Little Endian vs Big Endian UTF-16 to avoid Mojibake (Chinese characters).
    """
    if not user_comment:
        return ""

    try:
        if isinstance(user_comment, bytes):
            # Debug log
            if len(user_comment) > 50:
                 logger.debug(f"Decoding UserComment bytes (partial): {user_comment[:50].hex()}")

            # 1. Handle UNICODE prefix
            if user_comment.startswith(b'UNICODE\x00'):
                payload = user_comment[8:]
                
                # Try both LE and BE, pick the one that looks like English/ASCII
                # This works because A1111 prompts are mostly ASCII + English punctuation
                candidates = []
                for enc in ['utf-16le', 'utf-16be', 'utf-16']:
                    try:
                        decoded = payload.decode(enc)
                        # Score: Count printable ASCII/English chars
                        # Count standard printable ASCII (32-126) and newline/tab
                        # Mojibake will be mostly >127
                        score = sum(1 for c in decoded if 32 <= ord(c) <= 126 or c in '\n\r\t')
                        candidates.append((score, decoded))
                        # If almost perfect ASCII score, we can stop early
                        if score > len(payload)/2 * 0.9: # UTF-16 is 2 bytes per char
                             return decoded.strip()
                    except:
                        pass
                
                if candidates:
                    # Return the one with the highest ASCII score
                    candidates.sort(key=lambda x: x[0], reverse=True)
                    best_score, best_decoded = candidates[0]
                    # Log if it was confusing (e.g. low score)
                    if best_decoded and best_score < len(best_decoded) * 0.5:
                         logger.warning(f"Low confidence decode ({best_score}/{len(best_decoded)} ASCII chars): {best_decoded[:30]}...")
                    return best_decoded.strip()
            
            # 2. Handle ASCII prefix or raw
            if user_comment.startswith(b'ASCII\x00\x00\x00'):
                return user_comment[8:].decode('utf-8', errors='ignore').strip()
            
            # 3. Fallback / piexif helper
            try:
                # Piexif's load is decent generally
                return piexif.helper.UserComment.load(user_comment)
            except:
                pass
            
            # 4. Last resort: UTF-8
            return user_comment.decode('utf-8', errors='ignore').strip()

    except Exception as e:
        logger.warning(f"Failed to decode UserComment: {e}")
        pass

    return str(user_comment).strip()

def extract_a1111_params(param_str):
    """
    Extracts the positive prompt from an A1111 parameter string.
    Format: Positive Prompt \n Positive Prompt \n Negative Prompt: ... \n Steps: ...
    """
    if not param_str:
        return ""
        
    # Standard line-based parsing
    lines = param_str.strip().split('\n')
    positive_lines = []
    
    for line in lines:
        line_lower = line.lower()
        # stop if we hit negative prompt or steps
        if line_lower.startswith('negative prompt:') or line_lower.startswith('steps:'):
            break
        positive_lines.append(line)
        
    prompt = " ".join(positive_lines).strip()
    
    # Just in case the split didn't catch inline "Negative prompt:" (rare but possible in badly formatted metadata)
    if 'negative prompt:' in prompt.lower():
        prompt = re.split(r'negative prompt:', prompt, flags=re.IGNORECASE)[0]
        
    return prompt.strip()

def extract_prompt(image_path):
    """
    Robustly extracts ONLY the positive prompt from image metadata.
    Strictly focuses on A1111 format using PNGInfo or EXIF UserComment via piexif.
    """
    try:
        img = Image.open(image_path)
        
        # Strategy 1: PNG Info (parameters key)
        # Usage: PNG, WebP
        if img.info and 'parameters' in img.info:
            return extract_a1111_params(img.info['parameters'])
            
        # Strategy 2: EXIF UserComment via piexif
        # Usage: JPEG, WebP (sometimes)
        if 'exif' in img.info:
            try:
                exif_dict = piexif.load(img.info['exif'])
                # 0x9286 is UserComment
                if piexif.ExifIFD.UserComment in exif_dict.get('Exif', {}):
                    user_comment = exif_dict['Exif'][piexif.ExifIFD.UserComment]
                    decoded_comment = decode_exif_user_comment(user_comment)
                    if decoded_comment:
                        return extract_a1111_params(decoded_comment)
            except Exception:
                pass

        # Strategy 3: Fallback standard Image.getexif for JPEGs if piexif fail/not used
        # (Though piexif handles most, sometimes PIL's getexif is simpler for base tags)
        # 0x9286 = 37510 = UserComment
        exif = img.getexif()
        if exif:
            # check for UserComment
            if 37510 in exif:
                return extract_a1111_params(decode_exif_user_comment(exif[37510]))
            
            # check for ImageDescription (0x010e = 270) - some tools put params there
            if 270 in exif:
                 return extract_a1111_params(str(exif[270]))

        return ""
        
    except Exception as e:
        logger.error(f"Error extracting prompt from {image_path}: {e}")
        return ""

def get_image_files_generator(directory):
    """Yields supported image files in the directory recursively (lazy iteration)."""
    if os.path.isdir(directory):
        for root, dirs, filenames in os.walk(directory):
            for f in filenames:
                if f.lower().endswith(SUPPORTED_EXTENSIONS):
                    yield os.path.join(root, f)
