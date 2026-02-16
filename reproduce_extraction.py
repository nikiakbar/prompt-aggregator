import os
import io
import piexif
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from loader import extract_prompt

def create_test_images():
    # 1. create PNG with parameters
    img_png = Image.new('RGB', (100, 100))
    metadata = PngInfo()
    params = "PNG prompt v1, masterpiece\nNegative prompt: blurry\nSteps: 20"
    metadata.add_text("parameters", params)
    img_png.save("test_a1111.png", pnginfo=metadata)
    
    # 2. create JPEG with UserComment (via piexif)
    img_jpg = Image.new('RGB', (100, 100))
    exif_dict = {"Exif": {}}
    # UserComment needs to be bytes, often with charset prefix
    user_comment = "JPEG prompt v1, masterpiece\nNegative prompt: blurry\nSteps: 20"
    # standard UNICODE prefix
    prefix = b'UNICODE\x00'
    encoded = prefix + user_comment.encode('utf-16le')
    
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = encoded
    exif_bytes = piexif.dump(exif_dict)
    img_jpg.save("test_a1111.jpg", exif=exif_bytes)

def test_extraction():
    create_test_images()
    
    print("\n--- Testing A1111 PNG Extraction ---")
    extracted_png = extract_prompt("test_a1111.png")
    print(f"PNG Extracted: '{extracted_png}'")
    if extracted_png == "PNG prompt v1, masterpiece":
        print("SUCCESS")
    else:
        print(f"FAILURE: Expected 'PNG prompt v1, masterpiece'")

    print("\n--- Testing A1111 JPEG Extraction (piexif) ---")
    extracted_jpg = extract_prompt("test_a1111.jpg")
    print(f"JPEG Extracted: '{extracted_jpg}'")
    if extracted_jpg == "JPEG prompt v1, masterpiece":
        print("SUCCESS")
    else:
        print(f"FAILURE: Expected 'JPEG prompt v1, masterpiece'")

    # Clean up
    if os.path.exists("test_a1111.png"): os.remove("test_a1111.png")
    if os.path.exists("test_a1111.jpg"): os.remove("test_a1111.jpg")

if __name__ == "__main__":
    test_extraction()
