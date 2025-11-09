#!/usr/bin/env python3
"""
Simplified Visual Indicators Module for Voice-to-Text App
Provides system tray icon and desktop notifications without complex GUI threading.
"""

import threading
import time
import logging
from PIL import Image, ImageDraw

class SimpleVisualIndicator:
    """Manages visual feedback for the voice-to-text application (simplified version)."""
    
    def __init__(self, max_duration_sec=300):
        self.max_duration_sec = max_duration_sec
        self.recording = False
        self.start_time = None
        self.tray_icon = None
        self.running = True
        self.warning_30_shown = False
        self.warning_10_shown = False
        
        # Try to import optional dependencies
        self.has_pystray = self._try_import_pystray()
        self.has_plyer = self._try_import_plyer()
        
        # Initialize components
        if self.has_pystray:
            self._setup_tray_icon()
        
        # Start monitoring thread for time warnings
        self.monitor_thread = threading.Thread(target=self._monitor_recording_time, daemon=True)
        self.monitor_thread.start()
    
    def _try_import_pystray(self):
        """Try to import pystray for system tray functionality."""
        try:
            global pystray
            import pystray
            return True
        except ImportError:
            logging.info("📝 pystray not available - system tray icon disabled")
            return False
    
    def _try_import_plyer(self):
        """Try to import plyer for desktop notifications."""
        try:
            global plyer
            from plyer import notification
            return True
        except ImportError:
            logging.info("📝 plyer not available - desktop notifications disabled")
            return False
    
    def _create_icon_image(self, color="gray"):
        """Create a microphone icon for the system tray."""
        # Create a simple microphone icon
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if color == "red":
            fill_color = (255, 0, 0, 255)  # Red when recording
        else:
            fill_color = (128, 128, 128, 255)  # Gray when idle
        
        # Draw microphone shape
        # Microphone body (rounded rectangle)
        draw.rounded_rectangle([20, 15, 44, 40], radius=8, fill=fill_color)
        
        # Microphone stand
        draw.rectangle([30, 40, 34, 55], fill=fill_color)
        
        # Base
        draw.ellipse([25, 50, 39, 58], fill=fill_color)
        
        return img
    
    def _setup_tray_icon(self):
        """Setup system tray icon."""
        if not self.has_pystray:
            return
        
        try:
            # Create menu items
            menu_items = [
                pystray.MenuItem("Voice-to-Text App", lambda: None, enabled=False),
                pystray.MenuItem("Status: Idle", lambda: None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self._quit_app)
            ]
            
            # Create tray icon
            icon_image = self._create_icon_image("gray")
            self.tray_icon = pystray.Icon(
                "voice_to_text",
                icon_image,
                "Voice-to-Text App - Idle",
                menu=pystray.Menu(*menu_items)
            )
            
            # Start tray icon in a separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            logging.info("✅ System tray icon initialized")
            
        except Exception as e:
            logging.warning(f"⚠️ Failed to setup system tray: {e}")
    
    def _monitor_recording_time(self):
        """Monitor recording time and show warnings."""
        while self.running:
            try:
                if self.recording and self.start_time:
                    elapsed = time.time() - self.start_time
                    remaining = max(0, self.max_duration_sec - elapsed)
                    
                    # Warning when 30 seconds left
                    if remaining <= 30 and remaining > 29 and not self.warning_30_shown:
                        self._show_notification("⚠️ Recording Time Warning", "30 seconds remaining!")
                        self.warning_30_shown = True
                    
                    # Warning when 10 seconds left
                    if remaining <= 10 and remaining > 9 and not self.warning_10_shown:
                        self._show_notification("⚠️ Recording Time Warning", "10 seconds remaining!")
                        self.warning_10_shown = True
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logging.warning(f"⚠️ Recording monitor error: {e}")
                time.sleep(1)
    
    def _show_notification(self, title, message):
        """Show desktop notification."""
        if not self.has_plyer:
            return
        
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name="Voice-to-Text",
                timeout=3
            )
        except Exception as e:
            logging.warning(f"⚠️ Notification error: {e}")
    
    def _quit_app(self):
        """Quit the application from tray menu."""
        import os
        os._exit(0)
    
    def start_recording(self):
        """Visual feedback for recording start."""
        self.recording = True
        self.start_time = time.time()
        self.warning_30_shown = False
        self.warning_10_shown = False
        
        # Update tray icon
        if self.has_pystray and self.tray_icon:
            try:
                icon_image = self._create_icon_image("red")
                self.tray_icon.icon = icon_image
                self.tray_icon.title = "Voice-to-Text App - Recording"
                
                # Update menu to show recording status
                menu_items = [
                    pystray.MenuItem("Voice-to-Text App", lambda: None, enabled=False),
                    pystray.MenuItem("Status: Recording", lambda: None, enabled=False),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Exit", self._quit_app)
                ]
                self.tray_icon.menu = pystray.Menu(*menu_items)
                
            except Exception as e:
                logging.warning(f"⚠️ Tray icon update error: {e}")
        
        # Show notification
        self._show_notification("🎙️ Recording Started", "Voice recording in progress...")
        
        logging.info("🔴 Visual indicators: Recording started")
    
    def stop_recording(self):
        """Visual feedback for recording stop."""
        self.recording = False
        
        # Update tray icon
        if self.has_pystray and self.tray_icon:
            try:
                icon_image = self._create_icon_image("gray")
                self.tray_icon.icon = icon_image
                self.tray_icon.title = "Voice-to-Text App - Idle"
                
                # Update menu to show idle status
                menu_items = [
                    pystray.MenuItem("Voice-to-Text App", lambda: None, enabled=False),
                    pystray.MenuItem("Status: Idle", lambda: None, enabled=False),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Exit", self._quit_app)
                ]
                self.tray_icon.menu = pystray.Menu(*menu_items)
                
            except Exception as e:
                logging.warning(f"⚠️ Tray icon update error: {e}")
        
        # Show notification
        self._show_notification("⏹️ Recording Stopped", "Processing audio...")
        
        logging.info("⚪ Visual indicators: Recording stopped")
    
    def transcription_complete(self, text):
        """Visual feedback for transcription completion."""
        # Show notification with transcribed text preview
        preview = text[:50] + "..." if len(text) > 50 else text
        self._show_notification("✅ Transcription Complete", f"Text: {preview}\n💾 Saved to session log")

        logging.info("✅ Visual indicators: Transcription complete")
    
    def show_error(self, error_message):
        """Visual feedback for errors."""
        self._show_notification("❌ Error", error_message)
        logging.info(f"❌ Visual indicators: Error shown - {error_message}")
    
    def cleanup(self):
        """Clean up visual components."""
        self.running = False
        
        if self.has_pystray and self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        
        logging.info("🧹 Visual indicators cleaned up")
