#!/usr/bin/env python3
"""
Test script to verify that all dependencies are properly installed
and the basic components of the voice-to-text app are working.
"""

import sys

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import numpy as np
        print("✅ numpy imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import numpy: {e}")
        return False
    
    try:
        import scipy.io.wavfile as wav
        print("✅ scipy imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import scipy: {e}")
        return False
    
    try:
        import sounddevice as sd
        print("✅ sounddevice imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import sounddevice: {e}")
        return False
    
    try:
        import whisper
        print("✅ whisper imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import whisper: {e}")
        return False
    
    try:
        import keyboard
        print("✅ keyboard imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import keyboard: {e}")
        return False
    
    try:
        import pyperclip
        print("✅ pyperclip imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import pyperclip: {e}")
        return False
    
    try:
        import pyautogui
        print("✅ pyautogui imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import pyautogui: {e}")
        return False
    
    return True

def test_audio_devices():
    """Test audio device detection."""
    print("\nTesting audio devices...")
    
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        
        if input_devices:
            print(f"✅ Found {len(input_devices)} input device(s):")
            for i, device in enumerate(input_devices[:3]):  # Show first 3
                print(f"   {i+1}. {device['name']}")
        else:
            print("⚠️ No input devices found. Microphone may not be available.")
            
        return len(input_devices) > 0
        
    except Exception as e:
        print(f"❌ Error checking audio devices: {e}")
        return False

def test_whisper_model():
    """Test Whisper model loading (this may take a moment)."""
    print("\nTesting Whisper model loading...")
    
    try:
        import whisper
        print("🔄 Loading Whisper 'base' model... (this may take a moment)")
        model = whisper.load_model("base")
        print("✅ Whisper model loaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to load Whisper model: {e}")
        return False

def test_clipboard():
    """Test clipboard functionality."""
    print("\nTesting clipboard functionality...")
    
    try:
        import pyperclip
        
        # Test writing to clipboard
        test_text = "Voice-to-text test"
        pyperclip.copy(test_text)
        
        # Test reading from clipboard
        clipboard_content = pyperclip.paste()
        
        if clipboard_content == test_text:
            print("✅ Clipboard functionality working")
            return True
        else:
            print("⚠️ Clipboard test failed - content mismatch")
            return False
            
    except Exception as e:
        print(f"❌ Clipboard test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Voice-to-Text App Setup Test")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Audio Devices Test", test_audio_devices),
        ("Clipboard Test", test_clipboard),
        ("Whisper Model Test", test_whisper_model),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The voice-to-text app should work correctly.")
        print("You can now run: python simple_transcriber.py")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")
        print("You may need to install additional dependencies or check your system configuration.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
