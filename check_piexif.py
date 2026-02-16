import piexif
import piexif.helper

def test_piexif_helper():
    print("Testing piexif.helper.UserComment")
    try:
        # Create a UserComment with UNICODE encoding (A1111 style)
        text = "masterpiece, best quality"
        dumped = piexif.helper.UserComment.dump(text, encoding="unicode")
        print(f"Dumped (UNICODE): {dumped[:20]}...")
        
        # Load it back
        loaded = piexif.helper.UserComment.load(dumped)
        print(f"Loaded: '{loaded}'")
        
        if loaded == text:
            print("SUCCESS: UNICODE roundtrip working.")
        else:
            print("FAILURE: UNICODE roundtrip mismatch.")
            
        # Test implicit ASCII (no header, or ASCII header)
        text_ascii = "simple text"
        # piexif dump with ascii
        dumped_ascii = piexif.helper.UserComment.dump(text_ascii, encoding="ascii")
        print(f"Dumped (ASCII): {dumped_ascii[:20]}...")
        loaded_ascii = piexif.helper.UserComment.load(dumped_ascii)
        print(f"Loaded (ASCII): '{loaded_ascii}'")
        
        if loaded_ascii == text_ascii:
             print("SUCCESS: ASCII roundtrip working.")
             
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_piexif_helper()
