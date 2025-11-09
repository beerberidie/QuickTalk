# Voice-to-Text Transcription App

A lightweight desktop utility that lets you record up to 30 minutes of microphone audio via a global hotkey, runs offline Whisper transcription, and pastes the result at the current cursor position.

## Features

- 🎙️ **Global hotkey** (Ctrl + Alt + T) to toggle recording on/off
- ⏱️ **Max duration**: 30 minutes (configurable)
- 🔒 **Offline transcription** using Whisper "medium" model
- 📋 **Auto-paste** result via clipboard at cursor
- 📝 **Console notifications** for state changes and errors
- 🚪 **Graceful exit** via ESC key
- ⚙️ **Configurable** via settings at top of script
- 🔴 **System tray icon** - Shows recording status (gray=idle, red=recording)
- 📢 **Desktop notifications** - Toast notifications for recording events
- ⚠️ **Time warnings** - Alerts when recording time is running low
- 📝 **Session logging** - Automatically saves all transcriptions to timestamped text files

## Requirements

- Python 3.8 or higher
- Microphone access
- Windows/macOS/Linux (cross-platform)

## Installation

1. **Clone or download** this project to your local machine

2. **Install dependencies** using pip:
   ```bash
   pip install -r requirements.txt
   ```

   This will install:
   - `openai-whisper` - For offline speech transcription
   - `sounddevice` - For audio capture
   - `numpy` & `scipy` - For audio processing
   - `keyboard` - For global hotkey support
   - `pyperclip` & `pyautogui` - For clipboard and paste functionality

3. **First run** will download the Whisper model (about 769MB for "medium" model)

## Usage

1. **Start the application**:
   ```bash
   python simple_transcriber.py
   ```

2. **Position your cursor** where you want the transcribed text to appear (text editor, email, etc.)

3. **Press Ctrl + Alt + T** to start recording
   - You'll see "🎙️ Recording started..." in the console
   - Speak clearly into your microphone

4. **Press Ctrl + Alt + T again** to stop recording and transcribe
   - The app will process the audio and transcribe it
   - Text will be automatically pasted at your cursor position

5. **Press ESC** to exit the application

## Visual Indicators

The application provides several visual feedback mechanisms:

### 🔴 System Tray Icon
- **Gray microphone icon** when idle
- **Red microphone icon** when recording
- **Right-click menu** with status and exit option
- **Tooltip** shows current application status

### 📢 Desktop Notifications
- **Recording started** - Confirms when recording begins
- **Recording stopped** - Shows when recording ends and processing starts
- **Transcription complete** - Displays preview of transcribed text
- **Time warnings** - Alerts at 30 seconds and 10 seconds remaining
- **Error notifications** - Shows if transcription fails

### ⚠️ Time Management
- **Automatic warnings** when recording time is running low
- **30-minute maximum** with auto-stop to prevent buffer overflow
- **Visual feedback** through system tray icon color changes

### 📝 Session Logging
- **Automatic session files** - Creates a new timestamped text file each time you start the app
- **All transcriptions saved** - Every recording in a session is automatically logged
- **Rich metadata** - Includes timestamps, recording duration, and session summary
- **Organized storage** - Files saved in `transcription_logs` folder with clear naming
- **Session tracking** - Each file contains a complete log of your voice-to-text session

**Example session file**: `VoiceToText_Session_2025-06-28_14-30-15.txt`
```
==================================================
🎤 VOICE-TO-TEXT SESSION LOG
==================================================
Session started: 2025-06-28 14:30:15
App: Voice-to-Text Transcription App
==================================================

[14:32:45] Recording #1 (Duration: 8.3s)
"Hello, this is my first test recording."

[14:35:12] Recording #2 (Duration: 12.1s)
"This is another test to see how well it works."

==================================================
📊 SESSION SUMMARY
==================================================
Session ended: 2025-06-28 14:45:22
Total duration: 0:15:07
Total recordings: 2
==================================================
```

## Configuration

You can modify settings at the top of `simple_transcriber.py`:

```python
MAX_DURATION_SEC = 1800           # Max recording length (30 minutes)
HOTKEY_TOGGLE     = 'ctrl+alt+t'  # Start/stop recording hotkey
EXIT_HOTKEY       = 'esc'         # Exit application hotkey
MODEL_NAME        = 'medium'      # Whisper model (base/small/medium/large)
SAMPLE_RATE       = 16000         # Audio sample rate

# Session logging configuration
ENABLE_SESSION_LOGGING = True     # Enable automatic session logging
LOG_FOLDER_PATH = "transcription_logs"  # Folder for session files
LOG_INCLUDE_METADATA = True       # Include timestamps and duration

# Visual indicators configuration
ENABLE_VISUAL_INDICATORS = True   # Enable system tray and notifications
SHOW_DESKTOP_NOTIFICATIONS = True # Show toast notifications
```

## Whisper Models

- **base** (default): ~140MB, good balance of speed and accuracy
- **small**: ~240MB, better accuracy, slower
- **medium**: ~760MB, even better accuracy
- **large**: ~1550MB, best accuracy, slowest

## Troubleshooting

### Audio Issues
- **No microphone detected**: Check that your microphone is connected and not being used by another application
- **Poor audio quality**: Try adjusting your microphone settings or speaking closer to the mic
- **Permission denied**: On some systems, you may need to grant microphone permissions

### Hotkey Issues
- **Hotkeys not working**: Try running as administrator (Windows) or with appropriate permissions
- **Conflicts with other apps**: Change the hotkey combination in the configuration section

### Transcription Issues
- **No text output**: Ensure you're speaking clearly and the recording contains speech
- **Inaccurate transcription**: Try using a larger Whisper model (small/medium/large)
- **Slow transcription**: Use a smaller model (base/small) or ensure your CPU isn't overloaded

### Installation Issues
- **PyTorch/Whisper installation fails**: You may need to install PyTorch separately first
- **Sounddevice issues**: Install system audio libraries (e.g., `portaudio` on Linux)

## Building Executable

To create a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile simple_transcriber.py
```

The executable will be in the `dist/` folder.

## Privacy & Security

- ✅ **Completely offline** - no data sent to cloud services
- ✅ **Temporary files** are automatically deleted after transcription
- ✅ **Local processing** - all audio stays on your machine
- ✅ **No persistent storage** - audio is not saved permanently

## Technical Details

- **Audio format**: 16kHz mono WAV
- **Processing**: Real-time audio capture with numpy buffering
- **Transcription**: OpenAI Whisper running locally
- **Threading**: Non-blocking audio processing and hotkey handling

## License

MIT License - see [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Garason (beerberidie)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

**Enjoy hands-free transcription!** 🎤✨
