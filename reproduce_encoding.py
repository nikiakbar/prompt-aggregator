import piexif
import piexif.helper
from PIL import Image

from loader import extract_prompt, decode_exif_user_comment

def create_tricky_images():
    # 1. Image with valid UNICODE UserComment (UTF-16)
    img_u = Image.new('RGB', (50, 50))
    exif_u = {"Exif": {}}
    text_u = "unicode prompt, nice"
    # piexif helper dump creates proper unicode header and utf-16 bytes
    exif_u["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(text_u, encoding="unicode")
    img_u.save("test_unicode.jpg", exif=piexif.dump(exif_u))
    
    # 2. Image with ASCII UserComment (ASCII header)
    img_a = Image.new('RGB', (50, 50))
    exif_a = {"Exif": {}}
    text_a = "ascii prompt, cool"
    exif_a["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(text_a, encoding="ascii")
    img_a.save("test_ascii.jpg", exif=piexif.dump(exif_a))

    # 3. Image with NO HEADER (raw utf-8 bytes) - This simulates the "missing prefix" case
    # piexif helper might choke on this, but let's see if our fallback works
    img_raw = Image.new('RGB', (50, 50))
    exif_raw = {"Exif": {}}
    text_raw = "raw utf8 prompt"
    # Manual byte insertion without header
    exif_raw["Exif"][piexif.ExifIFD.UserComment] = text_raw.encode('utf-8')
    img_raw.save("test_raw.jpg", exif=piexif.dump(exif_raw))

def test_decoding():
    create_tricky_images()
    
    print("\n--- Testing Unicode ---")
    res_u = extract_prompt("test_unicode.jpg")
    print(f"Got: '{res_u}'")
    assert res_u == "unicode prompt, nice"
    
    print("\n--- Testing ASCII ---")
    res_a = extract_prompt("test_ascii.jpg")
    print(f"Got: '{res_a}'")
    assert res_a == "ascii prompt, cool"

    print("\n--- Testing Raw UTF-8 ---")
    res_raw = extract_prompt("test_raw.jpg")
    print(f"Got: '{res_raw}'")
    # This relies on fallback or piexif being smart
    assert res_raw == "raw utf8 prompt"
    
    print("\nALL ENCODING TESTS PASSED")

if __name__ == "__main__":
    test_decoding()
