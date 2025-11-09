#!/usr/bin/env python3
"""
Visual Indicators Module for Voice-to-Text App
Provides system tray icon, overlay window, and desktop notifications.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import logging
from PIL import Image, ImageDraw
import io

class VisualIndicator:
    """Manages all visual feedback for the voice-to-text application."""
    
    def __init__(self, max_duration_sec=300):
        self.max_duration_sec = max_duration_sec
        self.recording = False
        self.start_time = None
        self.overlay_window = None
        self.tray_icon = None
        self.update_thread = None
        self.running = True
        
        # Try to import optional dependencies
        self.has_pystray = self._try_import_pystray()
        self.has_plyer = self._try_import_plyer()
        
        # Initialize components
        self._setup_overlay()
        if self.has_pystray:
            self._setup_tray_icon()
    
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
    
    def _setup_overlay(self):
        """Setup overlay window for recording status."""
        try:
            # Create overlay window in a separate thread to avoid main loop conflicts
            self.overlay_setup_complete = threading.Event()
            self.overlay_thread = threading.Thread(target=self._create_overlay_window, daemon=True)
            self.overlay_thread.start()

            # Wait for overlay setup to complete (with timeout)
            if self.overlay_setup_complete.wait(timeout=5):
                logging.info("✅ Overlay window initialized")
            else:
                logging.warning("⚠️ Overlay window setup timed out")
                self.overlay_window = None

        except Exception as e:
            logging.warning(f"⚠️ Failed to setup overlay window: {e}")
            self.overlay_window = None

    def _create_overlay_window(self):
        """Create the overlay window in its own thread with its own event loop."""
        try:
            self.overlay_window = tk.Tk()
            self.overlay_window.title("Voice-to-Text Status")
            self.overlay_window.geometry("250x80+50+50")  # width x height + x_offset + y_offset
            self.overlay_window.attributes("-topmost", True)
            self.overlay_window.attributes("-alpha", 0.9)
            self.overlay_window.resizable(False, False)

            # Remove window decorations for a cleaner look
            self.overlay_window.overrideredirect(True)

            # Create frame with border
            main_frame = tk.Frame(self.overlay_window, bg="#2c3e50", relief="raised", bd=2)
            main_frame.pack(fill="both", expand=True, padx=2, pady=2)

            # Status label
            self.status_label = tk.Label(
                main_frame,
                text="🎤 Voice-to-Text Ready",
                font=("Arial", 10, "bold"),
                bg="#2c3e50",
                fg="white"
            )
            self.status_label.pack(pady=5)

            # Timer label
            self.timer_label = tk.Label(
                main_frame,
                text="Press Ctrl+Alt+T to start",
                font=("Arial", 9),
                bg="#2c3e50",
                fg="#ecf0f1"
            )
            self.timer_label.pack(pady=2)

            # Progress bar
            self.progress_var = tk.DoubleVar()
            self.progress_bar = ttk.Progressbar(
                main_frame,
                variable=self.progress_var,
                maximum=100,
                length=200
            )
            self.progress_bar.pack(pady=5)

            # Hide initially
            self.overlay_window.withdraw()

            # Signal that setup is complete
            self.overlay_setup_complete.set()

            # Start update loop in this thread
            self._start_overlay_update_loop()

            # Run the tkinter event loop in this thread
            self.overlay_window.mainloop()

        except Exception as e:
            logging.warning(f"⚠️ Failed to create overlay window: {e}")
            self.overlay_window = None
            self.overlay_setup_complete.set()  # Signal completion even on error
    
    def _start_overlay_update_loop(self):
        """Start the overlay update loop in the same thread as the overlay window."""
        def update_loop():
            if self.overlay_window and self.recording:
                try:
                    elapsed = time.time() - self.start_time
                    remaining = max(0, self.max_duration_sec - elapsed)

                    # Update timer display
                    minutes = int(remaining // 60)
                    seconds = int(remaining % 60)
                    timer_text = f"⏱️ {minutes:02d}:{seconds:02d} remaining"

                    # Update progress bar
                    progress = (elapsed / self.max_duration_sec) * 100

                    # Update display directly (we're in the right thread now)
                    self._update_overlay_display(timer_text, progress)

                    # Warning when 30 seconds left
                    if remaining <= 30 and remaining > 29:
                        self._show_notification("⚠️ Recording Time Warning", "30 seconds remaining!")

                    # Warning when 10 seconds left
                    if remaining <= 10 and remaining > 9:
                        self._show_notification("⚠️ Recording Time Warning", "10 seconds remaining!")

                except Exception as e:
                    logging.warning(f"⚠️ Overlay update error: {e}")

            # Schedule next update
            if self.running and self.overlay_window:
                self.overlay_window.after(1000, update_loop)  # Update every second

        # Start the update loop
        if self.overlay_window:
            self.overlay_window.after(100, update_loop)  # Start after 100ms
    
    def _update_overlay_display(self, timer_text, progress):
        """Update overlay display elements (called on main thread)."""
        try:
            if self.timer_label:
                self.timer_label.config(text=timer_text)
            if self.progress_bar:
                self.progress_var.set(min(100, progress))
        except Exception as e:
            logging.warning(f"⚠️ Display update error: {e}")
    
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

        # Update overlay (thread-safe)
        if self.overlay_window:
            try:
                self.overlay_window.after(0, lambda: self._update_recording_ui(True))
                self.overlay_window.after(0, self.overlay_window.deiconify)  # Show window
            except Exception as e:
                logging.warning(f"⚠️ Overlay start recording error: {e}")

        # Update tray icon
        if self.has_pystray and self.tray_icon:
            try:
                icon_image = self._create_icon_image("red")
                self.tray_icon.icon = icon_image
                self.tray_icon.title = "Voice-to-Text App - Recording"
            except Exception as e:
                logging.warning(f"⚠️ Tray icon update error: {e}")

        # Show notification
        self._show_notification("🎙️ Recording Started", "Voice recording in progress...")

        logging.info("🔴 Visual indicators: Recording started")

    def stop_recording(self):
        """Visual feedback for recording stop."""
        self.recording = False

        # Update overlay (thread-safe)
        if self.overlay_window:
            try:
                self.overlay_window.after(0, lambda: self._update_recording_ui(False))
                self.overlay_window.after(0, self.overlay_window.withdraw)  # Hide window
            except Exception as e:
                logging.warning(f"⚠️ Overlay stop recording error: {e}")

        # Update tray icon
        if self.has_pystray and self.tray_icon:
            try:
                icon_image = self._create_icon_image("gray")
                self.tray_icon.icon = icon_image
                self.tray_icon.title = "Voice-to-Text App - Idle"
            except Exception as e:
                logging.warning(f"⚠️ Tray icon update error: {e}")

        # Show notification
        self._show_notification("⏹️ Recording Stopped", "Processing audio...")

        logging.info("⚪ Visual indicators: Recording stopped")
    
    def _update_recording_ui(self, is_recording):
        """Update UI elements for recording state."""
        try:
            if is_recording:
                self.status_label.config(text="🔴 Recording...", fg="#e74c3c")
                self.timer_label.config(text="⏱️ 30:00 remaining")
                self.progress_var.set(0)
            else:
                self.status_label.config(text="🎤 Voice-to-Text Ready", fg="white")
                self.timer_label.config(text="Press Ctrl+Alt+T to start")
                self.progress_var.set(0)
        except Exception as e:
            logging.warning(f"⚠️ UI update error: {e}")
    
    def transcription_complete(self, text):
        """Visual feedback for transcription completion."""
        # Show notification with transcribed text preview
        preview = text[:50] + "..." if len(text) > 50 else text
        self._show_notification("✅ Transcription Complete", f"Text: {preview}")
        
        logging.info("✅ Visual indicators: Transcription complete")
    
    def show_error(self, error_message):
        """Visual feedback for errors."""
        self._show_notification("❌ Error", error_message)
        logging.info(f"❌ Visual indicators: Error shown - {error_message}")
    
    def cleanup(self):
        """Clean up visual components."""
        self.running = False
        
        if self.overlay_window:
            try:
                self.overlay_window.destroy()
            except:
                pass
        
        if self.has_pystray and self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        
        logging.info("🧹 Visual indicators cleaned up")
