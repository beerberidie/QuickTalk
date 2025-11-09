#!/usr/bin/env python3
"""
Voice-to-Text Transcription App
A lightweight desktop utility for offline voice transcription using Whisper.

Features:
- Global hotkey (Ctrl+Alt+T) to toggle recording
- Max 30-minute recording duration
- Offline Whisper transcription
- Auto-paste result at cursor
- ESC to exit gracefully
"""

import os
import threading
import logging
import time
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
import whisper
import keyboard
import pyperclip
import pyautogui
from simple_visual_indicators import SimpleVisualIndicator
from session_logger import SessionLogger

# ─── Configuration ─────────────────────────────────────────────────────────────
MAX_DURATION_SEC = 1800           # 30 minutes
HOTKEY_TOGGLE     = 'ctrl+alt+t'  # start/stop recording
EXIT_HOTKEY       = 'esc'         # quit application
MODEL_NAME        = 'medium'       # whisper model (base, small, medium, large)
SAMPLE_RATE       = 16000         # microphone sample rate

# Visual indicators configuration
ENABLE_VISUAL_INDICATORS = True   # Enable system tray, overlay, and notifications
SHOW_OVERLAY_WINDOW = False       # Show floating status window (disabled due to threading issues)
SHOW_DESKTOP_NOTIFICATIONS = True # Show toast notifications

# Session logging configuration
ENABLE_SESSION_LOGGING = True     # Enable automatic session logging to text files
LOG_FOLDER_PATH = "transcription_logs"  # Folder to save session logs (relative to app directory)
LOG_INCLUDE_METADATA = True       # Include recording duration and timestamps in logs

# Use absolute path for temp file to avoid working directory issues
TEMP_WAV_PATH     = os.path.join(os.getcwd(), 'temp_audio.wav')

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

# ─── Global State ──────────────────────────────────────────────────────────────
model = None
recording = False
audio_frames = []
stream = None
auto_stop_timer = None
visual_indicator = None
session_logger = None
recording_start_time = None

def load_whisper_model():
    """Load the Whisper model with progress indication."""
    global model
    try:
        logging.info(f"🔄 Loading Whisper '{MODEL_NAME}' model... (this may take a moment)")
        model = whisper.load_model(MODEL_NAME)
        logging.info("✅ Whisper model loaded successfully!")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to load Whisper model: {e}")
        return False

# ─── Audio Callback ────────────────────────────────────────────────────────────
def audio_callback(indata, frames, time, status):
    """Callback function for audio stream to capture audio data."""
    # Note: frames and time parameters are required by sounddevice but not used
    _ = frames, time  # Suppress unused variable warnings

    if status:
        logging.warning(f"Audio status: {status}")
    if recording:
        audio_frames.append(indata.copy())

# ─── Start Recording ───────────────────────────────────────────────────────────
def start_recording():
    """Start audio recording from microphone."""
    global recording, audio_frames, stream, auto_stop_timer, recording_start_time

    if recording:
        logging.debug("start_recording called while already recording.")
        return

    # Reset audio buffer and record start time
    audio_frames = []
    recording = True
    recording_start_time = time.time()
    
    try:
        # Create and start audio stream
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=audio_callback,
            dtype=np.float32
        )
        stream.start()
        logging.info("🎙️ Recording started... (max 30 min)")

        # Update visual indicators
        if visual_indicator and ENABLE_VISUAL_INDICATORS:
            visual_indicator.start_recording()

        # Set auto-stop timer to prevent buffer overflows
        auto_stop_timer = threading.Timer(MAX_DURATION_SEC, stop_recording_and_transcribe)
        auto_stop_timer.start()
        
    except Exception as e:
        recording = False
        logging.error(f"❌ Failed to start recording: {e}")
        logging.error("Make sure your microphone is connected and accessible.")

# ─── Stop Recording & Transcribe ───────────────────────────────────────────────
def stop_recording_and_transcribe():
    """Stop recording and transcribe the audio to text."""
    global recording, stream, auto_stop_timer

    if not recording:
        logging.debug("stop_recording called with no active recording.")
        return

    recording = False

    # Update visual indicators
    if visual_indicator and ENABLE_VISUAL_INDICATORS:
        visual_indicator.stop_recording()

    # Cancel auto-stop timer if manually stopped
    if auto_stop_timer and auto_stop_timer.is_alive():
        auto_stop_timer.cancel()

    try:
        # Stop and close audio stream
        if stream:
            stream.stop()
            stream.close()
            stream = None

        if not audio_frames:
            logging.warning("⚠️ No audio data recorded.")
            return

        # Concatenate audio buffers and save to WAV
        logging.info("💾 Processing audio...")
        logging.info(f"📊 Captured {len(audio_frames)} audio frames")

        audio_np = np.concatenate(audio_frames, axis=0).flatten()
        logging.info(f"📊 Audio array shape: {audio_np.shape}, dtype: {audio_np.dtype}")

        # Convert float32 to int16 for WAV file
        audio_int16 = (audio_np * 32767).astype(np.int16)

        # Save WAV file with improved Windows compatibility
        logging.info(f"💾 Saving audio to: {TEMP_WAV_PATH}")

        # Method 1: Try using soundfile (more reliable than scipy on Windows)
        wav_saved = False
        try:
            import soundfile as sf
            sf.write(TEMP_WAV_PATH, audio_np, SAMPLE_RATE, format='WAV', subtype='PCM_16')
            wav_saved = True
            logging.info("✅ WAV file saved using soundfile library")
        except ImportError:
            logging.info("📝 soundfile not available, falling back to scipy")
        except Exception as sf_error:
            logging.warning(f"⚠️ soundfile failed: {sf_error}, falling back to scipy")

        # Method 2: Fallback to scipy with explicit file handling
        if not wav_saved:
            try:
                wav.write(TEMP_WAV_PATH, SAMPLE_RATE, audio_int16)
                wav_saved = True
                logging.info("✅ WAV file saved using scipy")
            except Exception as scipy_error:
                logging.error(f"❌ scipy WAV write failed: {scipy_error}")

        # Method 3: Last resort - use wave module for maximum compatibility
        if not wav_saved:
            try:
                import wave
                with wave.open(TEMP_WAV_PATH, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(SAMPLE_RATE)
                    wav_file.writeframes(audio_int16.tobytes())
                wav_saved = True
                logging.info("✅ WAV file saved using wave module")
            except Exception as wave_error:
                logging.error(f"❌ wave module failed: {wave_error}")

        if not wav_saved:
            logging.error("❌ All WAV writing methods failed!")
            return

        # Ensure file is fully written and accessible
        time.sleep(0.1)  # Small delay to ensure file is flushed

        # Verify file was created and is accessible
        if not os.path.exists(TEMP_WAV_PATH):
            logging.error(f"❌ WAV file does not exist: {TEMP_WAV_PATH}")
            return

        file_size = os.path.getsize(TEMP_WAV_PATH)
        logging.info(f"✅ WAV file verified ({file_size} bytes)")

        # Additional file verification - try to read it back
        try:
            test_rate, test_data = wav.read(TEMP_WAV_PATH)
            logging.info(f"✅ WAV file readable - rate: {test_rate}, samples: {len(test_data)}")
        except Exception as read_error:
            logging.warning(f"⚠️ WAV file read test failed: {read_error}")

        # Transcribe audio using Whisper with enhanced error handling
        logging.info("📝 Transcribing... please wait.")
        try:
            # Use direct numpy array transcription (bypasses ffmpeg requirement)
            logging.info("📝 Using direct numpy array transcription...")
            result = model.transcribe(audio_np, fp16=False)
            text = result.get('text', '').strip()

            if text:
                logging.info(f"✅ Transcription: \"{text}\"")

                # Calculate recording duration
                recording_duration = None
                if recording_start_time:
                    recording_duration = time.time() - recording_start_time

                # Log to session file
                if session_logger and ENABLE_SESSION_LOGGING:
                    from datetime import datetime
                    start_datetime = datetime.fromtimestamp(recording_start_time) if recording_start_time else None
                    session_logger.log_transcription(text, recording_duration, start_datetime)

                # Update visual indicators
                if visual_indicator and ENABLE_VISUAL_INDICATORS:
                    visual_indicator.transcription_complete(text)

                # Copy to clipboard and paste
                pyperclip.copy(text)
                time.sleep(0.1)  # Small delay to ensure clipboard is ready
                pyautogui.hotkey('ctrl', 'v')
                logging.info("📋 Text pasted at cursor.")
            else:
                logging.warning("⚠️ No speech detected in recording.")

                # Log error to session file
                if session_logger and ENABLE_SESSION_LOGGING:
                    from datetime import datetime
                    start_datetime = datetime.fromtimestamp(recording_start_time) if recording_start_time else None
                    session_logger.log_error("No speech detected in recording", start_datetime)

                if visual_indicator and ENABLE_VISUAL_INDICATORS:
                    visual_indicator.show_error("No speech detected in recording")

        except Exception as transcribe_error:
            logging.error(f"❌ Transcription error: {transcribe_error}")
            logging.error(f"❌ WAV file path: {TEMP_WAV_PATH}")
            logging.error(f"❌ Absolute path: {os.path.abspath(TEMP_WAV_PATH)}")
            logging.error(f"❌ WAV file exists: {os.path.exists(TEMP_WAV_PATH)}")
            if os.path.exists(TEMP_WAV_PATH):
                logging.error(f"❌ WAV file size: {os.path.getsize(TEMP_WAV_PATH)} bytes")

            # Log error to session file
            if session_logger and ENABLE_SESSION_LOGGING:
                from datetime import datetime
                start_datetime = datetime.fromtimestamp(recording_start_time) if recording_start_time else None
                session_logger.log_error(f"Transcription failed: {transcribe_error}", start_datetime)

            if visual_indicator and ENABLE_VISUAL_INDICATORS:
                visual_indicator.show_error("Transcription failed")

    except Exception as e:
        logging.error(f"❌ Error during audio processing: {e}")
        import traceback
        logging.error(f"❌ Full traceback: {traceback.format_exc()}")
    finally:
        # Clean up temporary file
        if os.path.exists(TEMP_WAV_PATH):
            try:
                os.remove(TEMP_WAV_PATH)
                logging.debug(f"🗑️ Cleaned up temp file: {TEMP_WAV_PATH}")
            except Exception as e:
                logging.warning(f"Could not remove temp file: {e}")

# ─── Hotkey Listener ───────────────────────────────────────────────────────────
def hotkey_listener():
    """Listen for hotkey presses to toggle recording."""
    logging.info(f"🚀 Press {HOTKEY_TOGGLE} to toggle recording, {EXIT_HOTKEY} to exit.")
    logging.info("🎯 Ready! Position your cursor where you want text to be pasted.")
    
    while True:
        try:
            keyboard.wait(HOTKEY_TOGGLE)
            # Dispatch in a thread to keep UI responsive
            if not recording:
                threading.Thread(target=start_recording, daemon=True).start()
            else:
                threading.Thread(target=stop_recording_and_transcribe, daemon=True).start()
        except Exception as e:
            logging.error(f"❌ Hotkey listener error: {e}")
            break

# ─── Exit Listener ─────────────────────────────────────────────────────────────
def exit_listener():
    """Listen for exit hotkey and perform graceful shutdown."""
    try:
        keyboard.wait(EXIT_HOTKEY)
        logging.info("👋 Exit signal received. Shutting down...")
        
        # Stop recording if active
        if recording and stream:
            stream.stop()
            stream.close()
        
        # Clean up temp file
        if os.path.exists(TEMP_WAV_PATH):
            os.remove(TEMP_WAV_PATH)

        # Close session log
        if session_logger:
            session_logger.close_session()

        # Clean up visual indicators
        if visual_indicator:
            visual_indicator.cleanup()

        os._exit(0)
    except Exception as e:
        logging.error(f"❌ Exit listener error: {e}")
        os._exit(1)

# ─── Main Entrypoint ───────────────────────────────────────────────────────────
def main():
    """Main application entry point."""
    print("=" * 60)
    print("🎤 Voice-to-Text Transcription App")
    print("=" * 60)

    # Show working directory and temp file path for debugging
    logging.info(f"📁 Working directory: {os.getcwd()}")
    logging.info(f"📄 Temp file path: {TEMP_WAV_PATH}")

    # Load Whisper model
    if not load_whisper_model():
        logging.error("Failed to initialize. Exiting.")
        return 1

    # Initialize session logger
    global session_logger
    if ENABLE_SESSION_LOGGING:
        try:
            session_logger = SessionLogger(LOG_FOLDER_PATH, LOG_INCLUDE_METADATA)
            session_info = session_logger.get_session_info()
            logging.info(f"✅ Session logging initialized")
            logging.info(f"📁 Log folder: {session_logger.get_log_folder_path()}")
            logging.info(f"📝 Session file: {os.path.basename(session_info['session_file'])}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to initialize session logging: {e}")
            logging.info("📝 Continuing without session logging...")
            session_logger = None

    # Initialize visual indicators
    global visual_indicator
    if ENABLE_VISUAL_INDICATORS:
        try:
            visual_indicator = SimpleVisualIndicator(MAX_DURATION_SEC)
            logging.info("✅ Visual indicators initialized")
        except Exception as e:
            logging.warning(f"⚠️ Failed to initialize visual indicators: {e}")
            logging.info("📝 Continuing without visual indicators...")
    
    try:
        # Start exit listener thread
        exit_thread = threading.Thread(target=exit_listener, daemon=True)
        exit_thread.start()
        
        # Start hotkey listener (blocking)
        hotkey_listener()
        
    except KeyboardInterrupt:
        logging.info("👋 Interrupted by user. Shutting down...")
        return 0
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
