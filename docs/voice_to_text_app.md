# Voice-to-Text Transcription App: Detailed Implementation Draft

---

## 1. Overview

A lightweight desktop utility that lets you record up to 30 minutes of microphone audio via a global hotkey, runs an offline Whisper transcription, and pastes the result at the current cursor. Designed for simplicity, reliability, and offline use.

---

## 2. Features

* **Global hotkey (Ctrl + Alt + T)** to toggle recording on/off
* **Max duration**: 30 minutes (configurable)
* **Offline transcription** using Whisper “medium” model
* **Auto-paste** result via clipboard at cursor
* **Console notifications** for state changes, errors
* **Graceful exit** via ESC
* **Configurable** via a central section at top of script

---

## 3. Technology Stack

* **Language**: Python 3.8+
* **Key libraries**:

  * `openai-whisper` (Whisper models & transcription)
  * `sounddevice` (audio capture)
  * `numpy` & `scipy` (audio buffering & WAV writing)
  * `keyboard` (global hotkeys)
  * `pyperclip` & `pyautogui` (clipboard & paste)
  * `logging` (structured logs)
  * `threading` (non-blocking tasks)

---

## 4. Project Structure

```text
voice_to_text_app/
├── simple_transcriber.py       # single‐script executable
├── requirements.txt            # pip dependencies
└── README.md                   # quick start & troubleshooting
```

---

## 5. Dependencies & Installation

* **requirements.txt**

  ```text
  openai-whisper
  sounddevice
  numpy
  scipy
  keyboard
  pyperclip
  pyautogui
  ```
* **Install**

  ```bash
  pip install -r requirements.txt
  ```

---

## 6. Configuration

At the top of `simple_transcriber.py` you can adjust:

```python
MAX_DURATION_SEC = 1800           # max recording length
HOTKEY_TOGGLE     = 'ctrl+alt+t'  # start/stop
EXIT_HOTKEY       = 'esc'         # quit
MODEL_NAME        = 'medium'      # whisper model
SAMPLE_RATE       = 16000         # microphone rate
TEMP_WAV_PATH     = 'temp_audio.wav'
```

---

## 7. Application Workflow

1. **Startup**

   * Load Whisper model (prints progress).
   * Spawn threads: exit listener, hotkey listener.
2. **Recording**

   * On press Ctrl + Alt + T:

     * If not recording → start audio stream → append audio buffers → notify.
     * If already recording → stop stream → write WAV → trigger transcription.
3. **Transcription**

   * Feed WAV to Whisper → retrieve text → notify.
   * Copy text to clipboard → simulate Ctrl+V → notify.
   * Delete temp WAV.
4. **Exit**

   * On ESC → clean shutdown (via `os._exit(0)`).

---

## 8. Annotated Code Snippet

```python
#!/usr/bin/env python3
import os, threading, logging
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
import whisper
import keyboard
import pyperclip
import pyautogui

# ─── Configuration ─────────────────────────────────────────────────────────────
MAX_DURATION_SEC = 1800           # 30 minutes
HOTKEY_TOGGLE     = 'ctrl+alt+t'
EXIT_HOTKEY       = 'esc'
MODEL_NAME        = 'medium'
SAMPLE_RATE       = 16000
TEMP_WAV_PATH     = 'temp_audio.wav'

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

# ─── Global State ──────────────────────────────────────────────────────────────
model = whisper.load_model(MODEL_NAME)
recording = False
audio_frames = []
stream = None

# ─── Audio Callback ────────────────────────────────────────────────────────────
def audio_callback(indata, frames, time, status):
    if status:
        logging.warning(f"Audio status: {status}")
    audio_frames.append(indata.copy())

# ─── Start Recording ───────────────────────────────────────────────────────────
def start_recording():
    global recording, audio_frames, stream
    if recording:
        logging.debug("start_recording called while already recording.")
        return
    audio_frames = []
    recording = True
    try:
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=audio_callback
        )
        stream.start()
        logging.info("🎙️ Recording started... (max 30 min)")
        # auto-stop after MAX_DURATION_SEC to prevent buffer overflows
        threading.Timer(MAX_DURATION_SEC, stop_recording_and_transcribe).start()
    except Exception as e:
        recording = False
        logging.error(f"❌ Failed to start recording: {e}")

# ─── Stop & Transcribe ─────────────────────────────────────────────────────────
def stop_recording_and_transcribe():
    global recording, stream
    if not recording:
        logging.debug("stop_recording called with no active recording.")
        return
    recording = False
    try:
        stream.stop(); stream.close()
        # concatenate buffers
        audio_np = np.concatenate(audio_frames, axis=0).flatten()
        wav.write(TEMP_WAV_PATH, SAMPLE_RATE, audio_np)
        logging.info("📝 Transcribing... please wait.")
        result = model.transcribe(TEMP_WAV_PATH)
        text = result.get('text', '').strip()
        logging.info(f"✅ Transcription successful: \"{text}\"")
        # paste
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        logging.info("📋 Text pasted at cursor.")
    except Exception as e:
        logging.error(f"❌ Error during transcribe/paste: {e}")
    finally:
        if os.path.exists(TEMP_WAV_PATH):
            os.remove(TEMP_WAV_PATH)

# ─── Hotkey Listener ───────────────────────────────────────────────────────────
def hotkey_listener():
    logging.info(f"🚀 Press {HOTKEY_TOGGLE} to toggle recording.")
    while True:
        keyboard.wait(HOTKEY_TOGGLE)
        # dispatch in a thread so UI stays responsive
        if not recording:
            threading.Thread(target=start_recording, daemon=True).start()
        else:
            threading.Thread(target=stop_recording_and_transcribe, daemon=True).start()

# ─── Exit Listener ─────────────────────────────────────────────────────────────
def exit_listener():
    keyboard.wait(EXIT_HOTKEY)
    logging.info("👋 Exit signal received. Shutting down.")
    os._exit(0)

# ─── Main Entrypoint ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=exit_listener, daemon=True).start()
    hotkey_listener()
```

---

## 9. Error Handling & Logging

* Uses Python’s `logging` module for clear, timestamped messages.
* Warns on audio buffer or device issues.
* Gracefully handles file‐I/O and transcription exceptions.
* Automatically cleans up temporary WAV files.

---

## 10. Testing

1. **Unit Tests**: Mock `audio_callback` with synthetic data.
2. **Integration**:

   * Record < 1 s, paste.
   * Hit max duration, ensure auto-stop.
   * Disconnect microphone → observe error log.
3. **Cross-platform**: Verify hotkeys and audio capture on Windows/macOS/Linux.

---

## 11. Packaging & Distribution

* **PyInstaller** to create a single executable:

  ```bash
  pyinstaller --onefile simple_transcriber.py
  ```
* Bundle `models/` directory if using custom Whisper paths.

---

## 12. Security & Privacy

* **Clipboard**: Optionally clear (`pyperclip.copy('')`) after paste.
* **Temporary Files**: Auto-deleted.
* **Offline**: No cloud calls; all data stays local.

---

## 13. Future Enhancements

* **System Tray Icon** with start/stop controls (e.g., `pystray`).
* **Config file** (YAML/JSON) for hotkeys & model choice.
* **Language selection** or Whisper “small”/“medium” switch.
* **GUI version** with progress bar & transcript history.
* **Custom audio filters** (noise reduction) via `pydub`.

---

## 14. Next Steps for Implementation

1. **Clone repo** and create virtualenv.
2. Install dependencies.
3. Run `simple_transcriber.py`, exercise start/stop, exit.
4. Package executable for end-users.
5. Write brief README with screenshots and troubleshooting tips.

This markdown file is ready for inclusion in your project repository as **voice\_to\_text\_app.md**.
