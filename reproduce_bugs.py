import logging
import json
from unittest.mock import MagicMock
from loader import extract_prompt, is_likely_negative

# Mock Image.open to avoid needing actual files
from unittest.mock import patch

def test_comfyui_bug():
    print("\n--- Testing ComfyUI Extraction ---")
    
    # Simulate ComfyUI metadata
    workflow = {
        "3": {
            "inputs": {
                "text": "a beautiful landscape, embedding:EasyNegative",  # valid prompt using embedding
                "clip": ["4", 0]
            },
            "class_type": "CLIPTextEncode"
        }
    }
    
    metadata = {
        "prompt": json.dumps(workflow)
    }
    
    # Mock Image.open context manager
    with patch('loader.Image.open') as mock_open:
        mock_img = MagicMock()
        mock_img.info = metadata
        mock_img.getexif.return_value = {}
        mock_open.return_value.__enter__.return_value = mock_img
        
        extracted = extract_prompt("dummy.png")
        print(f"ComfyUI Input: {workflow['3']['inputs']['text']}")
        print(f"Extracted: '{extracted}'")
        
        if extracted == workflow['3']['inputs']['text']:
            print("SUCCESS: ComfyUI prompt extracted.")
        else:
            print("FAILURE: ComfyUI prompt NOT extracted (likely filtered).")

def test_fallback_negative_keyword():
    print("\n--- Testing Fallback Negative Logic ---")
    
    # Simulate metadata where only fallback works (no "parameters" key, just random key)
    metadata = {
        "Description": "text error on screen" # "text" and "error" are negative keywords
    }
    
    with patch('loader.Image.open') as mock_open:
        mock_img = MagicMock()
        mock_img.info = metadata
        mock_img.getexif.return_value = {}
        mock_open.return_value.__enter__.return_value = mock_img
        
        extracted = extract_prompt("dummy.jpg")
        print(f"Input: {metadata['Description']}")
        print(f"Extracted: '{extracted}'")
        
        if extracted == metadata['Description']:
            print("SUCCESS: Prompt extracted.")
        else:
            print("FAILURE: Prompt filtered out as negative.")

if __name__ == "__main__":
    test_comfyui_bug()
    test_fallback_negative_keyword()
