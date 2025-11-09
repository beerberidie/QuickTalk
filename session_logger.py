#!/usr/bin/env python3
"""
Session Logger Module for Voice-to-Text App
Handles automatic logging of transcription sessions to text files.
"""

import os
import logging
from datetime import datetime

class SessionLogger:
    """Manages session-based logging of voice transcriptions."""
    
    def __init__(self, log_folder_path="transcription_logs", include_metadata=True):
        self.log_folder_path = log_folder_path
        self.include_metadata = include_metadata
        self.session_file_path = None
        self.session_start_time = None
        self.recording_count = 0
        
        # Create session file
        self._create_session_file()
    
    def _create_session_file(self):
        """Create a new session log file with timestamp."""
        try:
            # Create log folder if it doesn't exist
            if not os.path.exists(self.log_folder_path):
                os.makedirs(self.log_folder_path)
                logging.info(f"📁 Created log folder: {self.log_folder_path}")
            
            # Generate session filename with timestamp
            self.session_start_time = datetime.now()
            timestamp = self.session_start_time.strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"VoiceToText_Session_{timestamp}.txt"
            self.session_file_path = os.path.join(self.log_folder_path, filename)
            
            # Create session file with header
            with open(self.session_file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 50 + "\n")
                f.write("🎤 VOICE-TO-TEXT SESSION LOG\n")
                f.write("=" * 50 + "\n")
                f.write(f"Session started: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"App: Voice-to-Text Transcription App\n")
                f.write(f"Log file: {filename}\n")
                f.write("=" * 50 + "\n\n")
            
            logging.info(f"📝 Session log created: {self.session_file_path}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to create session log: {e}")
            self.session_file_path = None
            return False
    
    def log_transcription(self, text, recording_duration=None, recording_start_time=None):
        """Log a transcription to the session file."""
        if not self.session_file_path:
            logging.warning("⚠️ No session file available for logging")
            return False
        
        try:
            self.recording_count += 1
            
            # Use current time if recording start time not provided
            if recording_start_time is None:
                recording_start_time = datetime.now()
            
            with open(self.session_file_path, 'a', encoding='utf-8') as f:
                # Write timestamp and recording info
                timestamp_str = recording_start_time.strftime("%H:%M:%S")
                f.write(f"[{timestamp_str}] Recording #{self.recording_count}")
                
                if self.include_metadata and recording_duration:
                    f.write(f" (Duration: {recording_duration:.1f}s)")
                
                f.write("\n")
                
                # Write the transcribed text with proper formatting
                f.write(f'"{text}"\n\n')
                
                # Add separator for readability
                f.write("-" * 30 + "\n\n")
            
            logging.info(f"📝 Transcription #{self.recording_count} logged to session file")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to log transcription: {e}")
            return False
    
    def log_error(self, error_message, recording_start_time=None):
        """Log an error or failed transcription to the session file."""
        if not self.session_file_path:
            return False
        
        try:
            self.recording_count += 1
            
            if recording_start_time is None:
                recording_start_time = datetime.now()
            
            with open(self.session_file_path, 'a', encoding='utf-8') as f:
                timestamp_str = recording_start_time.strftime("%H:%M:%S")
                f.write(f"[{timestamp_str}] Recording #{self.recording_count} - ERROR\n")
                f.write(f"❌ {error_message}\n\n")
                f.write("-" * 30 + "\n\n")
            
            logging.info(f"📝 Error logged to session file")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to log error: {e}")
            return False
    
    def add_session_note(self, note):
        """Add a custom note to the session file."""
        if not self.session_file_path:
            return False
        
        try:
            with open(self.session_file_path, 'a', encoding='utf-8') as f:
                timestamp_str = datetime.now().strftime("%H:%M:%S")
                f.write(f"[{timestamp_str}] NOTE: {note}\n\n")
                f.write("-" * 30 + "\n\n")
            
            logging.info(f"📝 Note added to session file")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to add note: {e}")
            return False
    
    def close_session(self):
        """Close the session and add footer to the log file."""
        if not self.session_file_path:
            return False
        
        try:
            session_end_time = datetime.now()
            session_duration = session_end_time - self.session_start_time
            
            with open(self.session_file_path, 'a', encoding='utf-8') as f:
                f.write("\n" + "=" * 50 + "\n")
                f.write("📊 SESSION SUMMARY\n")
                f.write("=" * 50 + "\n")
                f.write(f"Session ended: {session_end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total duration: {session_duration}\n")
                f.write(f"Total recordings: {self.recording_count}\n")
                f.write("=" * 50 + "\n")
            
            logging.info(f"📝 Session closed: {self.recording_count} recordings logged")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to close session: {e}")
            return False
    
    def get_session_info(self):
        """Get information about the current session."""
        return {
            "session_file": self.session_file_path,
            "start_time": self.session_start_time,
            "recording_count": self.recording_count,
            "log_folder": self.log_folder_path
        }
    
    def get_session_file_path(self):
        """Get the full path to the current session file."""
        return self.session_file_path
    
    def get_log_folder_path(self):
        """Get the full path to the log folder."""
        return os.path.abspath(self.log_folder_path)
