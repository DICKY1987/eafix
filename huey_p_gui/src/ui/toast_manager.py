"""
Toast Notification System for HUEY_P GUI
Non-blocking notifications with auto-dismiss and queue management
"""

import tkinter as tk
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import threading

from ..themes.colors import ColorPalette

try:
    import customtkinter as ctk  # type: ignore
    CTK_AVAILABLE = True
except Exception:  # pragma: no cover - fallback path
    CTK_AVAILABLE = False
    from types import SimpleNamespace

    class CTkFrame(tk.Frame):
        """Fallback frame using tkinter."""
        pass

    class CTkButton(tk.Button):
        """Fallback button using tkinter."""
        pass

    class CTkLabel(tk.Label):
        """Fallback label using tkinter."""
        pass

    class CTkFont:
        """Fallback font placeholder."""
        def __init__(self, *args, **kwargs):
            pass

    ctk = SimpleNamespace(
        CTkFrame=CTkFrame,
        CTkButton=CTkButton,
        CTkLabel=CTkLabel,
        CTkFont=CTkFont,
    )


class ToastType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


@dataclass
class Toast:
    message: str
    toast_type: ToastType
    duration: float  # seconds
    timestamp: datetime
    action_text: Optional[str] = None
    action_callback: Optional[Callable] = None
    toast_id: Optional[str] = None


class ToastWidget(ctk.CTkFrame):
    """Individual toast notification widget"""

    def __init__(self, master, toast: Toast, dismiss_callback: Callable, **kwargs):
        colors = self._get_toast_colors(toast.toast_type)

        default_kwargs = {
            "fg_color": colors["background"],
            "border_color": colors.get("border"),
            "border_width": 1,
            "corner_radius": 8,
            "width": 350,
            "height": 80,
        }
        if not CTK_AVAILABLE:
            default_kwargs = {"width": 350, "height": 80}

        default_kwargs.update(kwargs)

        super().__init__(master, **default_kwargs)

        self.toast = toast
        self.dismiss_callback = dismiss_callback
        self.auto_dismiss_id = None

        self.setup_ui()
        self.start_auto_dismiss()

    def _get_toast_colors(self, toast_type: ToastType) -> Dict[str, str]:
        """Get colors for toast type"""
        color_map = {
            ToastType.INFO: {
                "background": "#1A2332",
                "border": ColorPalette.INFO,
                "text": ColorPalette.DARK_TEXT_PRIMARY,
                "icon": ColorPalette.INFO,
            },
            ToastType.SUCCESS: {
                "background": "#1A2B1F",
                "border": ColorPalette.SUCCESS,
                "text": ColorPalette.DARK_TEXT_PRIMARY,
                "icon": ColorPalette.SUCCESS,
            },
            ToastType.WARNING: {
                "background": "#2B2619",
                "border": ColorPalette.WARNING,
                "text": ColorPalette.DARK_TEXT_PRIMARY,
                "icon": ColorPalette.WARNING,
            },
            ToastType.DANGER: {
                "background": "#2B1A1A",
                "border": ColorPalette.DANGER,
                "text": ColorPalette.DARK_TEXT_PRIMARY,
                "icon": ColorPalette.DANGER,
            },
        }
        return color_map.get(toast_type, color_map[ToastType.INFO])

    def setup_ui(self):
        """Setup toast UI components"""
        colors = self._get_toast_colors(self.toast.toast_type)

        frame_kwargs = {"fg_color": "transparent"} if CTK_AVAILABLE else {}
        content_frame = ctk.CTkFrame(self, **frame_kwargs)
        content_frame.pack(fill="both", expand=True, padx=8, pady=8)

        top_frame = ctk.CTkFrame(content_frame, **frame_kwargs)
        top_frame.pack(fill="x", pady=(0, 4))

        icon_map = {
            ToastType.INFO: "ℹ️",
            ToastType.SUCCESS: "✅",
            ToastType.WARNING: "⚠️",
            ToastType.DANGER: "🚨",
        }

        label_kwargs = {"font": ctk.CTkFont(family="Arial", size=16), "width": 24} if CTK_AVAILABLE else {"width": 24}
        icon_label = ctk.CTkLabel(
            top_frame,
            text=icon_map.get(self.toast.toast_type, "ℹ️"),
            **label_kwargs,
        )
        icon_label.pack(side="left", padx=(0, 8))

        msg_kwargs = {
            "font": ctk.CTkFont(family="Arial", size=12),
            "text_color": colors["text"],
            "wraplength": 250,
            "justify": "left",
        } if CTK_AVAILABLE else {"wraplength": 250, "justify": "left"}

        message_label = ctk.CTkLabel(
            top_frame,
            text=self.toast.message,
            **msg_kwargs,
        )
        message_label.pack(side="left", fill="x", expand=True)

        btn_kwargs = {
            "text": "✕",
            "font": ctk.CTkFont(family="Arial", size=12, weight="bold"),
            "width": 24,
            "height": 24,
            "fg_color": "transparent",
            "text_color": colors["text"],
            "hover_color": colors["border"],
            "command": self.dismiss,
        } if CTK_AVAILABLE else {"text": "✕", "width": 24, "command": self.dismiss}
        close_button = ctk.CTkButton(top_frame, **btn_kwargs)
        close_button.pack(side="right")

        bottom_frame = ctk.CTkFrame(content_frame, **frame_kwargs)
        bottom_frame.pack(fill="x")

        time_str = self.toast.timestamp.strftime("%H:%M:%S")
        ts_kwargs = {
            "font": ctk.CTkFont(family="Arial", size=9),
            "text_color": colors["text"],
        } if CTK_AVAILABLE else {}
        timestamp_label = ctk.CTkLabel(bottom_frame, text=time_str, **ts_kwargs)
        timestamp_label.pack(side="right")

        if self.toast.action_text and self.toast.action_callback:
            action_kwargs = {
                "text": self.toast.action_text,
                "font": ctk.CTkFont(family="Arial", size=10),
                "height": 24,
                "fg_color": colors["border"],
                "hover_color": colors["icon"],
                "command": self._handle_action,
            } if CTK_AVAILABLE else {"text": self.toast.action_text, "command": self._handle_action}
            action_button = ctk.CTkButton(bottom_frame, **action_kwargs)
            action_button.pack(side="left")

    def _handle_action(self):
        """Handle action button click"""
        if self.toast.action_callback:
            try:
                self.toast.action_callback()
            except Exception as e:  # pragma: no cover
                print(f"Toast action callback error: {e}")

        self.dismiss()

    def start_auto_dismiss(self):
        """Start auto-dismiss timer"""
        if self.toast.duration > 0:
            self.auto_dismiss_id = self.after(
                int(self.toast.duration * 1000),
                self.dismiss,
            )

    def dismiss(self):
        """Dismiss this toast"""
        if self.auto_dismiss_id:
            self.after_cancel(self.auto_dismiss_id)
            self.auto_dismiss_id = None

        if self.dismiss_callback:
            self.dismiss_callback(self)


class ToastManager:
    """Manages toast notifications with queue and positioning"""

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.active_toasts: List[ToastWidget] = []
        self.toast_queue: List[Toast] = []
        self.max_visible_toasts = 5
        self.toast_spacing = 10
        self.position_offset_x = 20
        self.position_offset_y = 20

        self._lock = threading.Lock()
        self.dedupe_window = 5.0
        self.recent_messages: Dict[str, datetime] = {}

    def show_toast(
        self,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration: float = 4.0,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None,
        toast_id: Optional[str] = None,
    ) -> Optional[str]:
        """Show a toast notification"""
        with self._lock:
            if self._is_duplicate_message(message):
                return None

            toast = Toast(
                message=message,
                toast_type=toast_type,
                duration=duration,
                timestamp=datetime.now(),
                action_text=action_text,
                action_callback=action_callback,
                toast_id=toast_id or f"toast_{len(self.toast_queue)}",
            )

            self.toast_queue.append(toast)
            self._process_queue()
            return toast.toast_id

    def _is_duplicate_message(self, message: str) -> bool:
        """Check if message was recently shown"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.dedupe_window)
        self.recent_messages = {
            msg: ts for msg, ts in self.recent_messages.items() if ts > cutoff
        }
        if message in self.recent_messages:
            return True
        self.recent_messages[message] = now
        return False

    def _process_queue(self):
        """Process toast queue"""
        while self.toast_queue and len(self.active_toasts) < self.max_visible_toasts:
            toast = self.toast_queue.pop(0)
            toast_widget = self._create_toast_widget(toast)
            if toast_widget:
                self.active_toasts.append(toast_widget)
                self._position_toast(toast_widget)

    def _create_toast_widget(self, toast: Toast) -> Optional[ToastWidget]:
        """Create toast widget"""
        try:
            toast_widget = ToastWidget(
                self.parent_window,
                toast,
                self._handle_toast_dismissed,
            )
            return toast_widget
        except Exception as e:  # pragma: no cover
            print(f"Failed to create toast widget: {e}")
            return None

    def _handle_toast_dismissed(self, toast_widget: ToastWidget):
        """Handle toast dismissal"""
        try:
            if toast_widget in self.active_toasts:
                self.active_toasts.remove(toast_widget)
                toast_widget.destroy()
            self._reposition_toasts()
            self._process_queue()
        except Exception as e:  # pragma: no cover
            print(f"Error handling toast dismissal: {e}")

    def _position_toast(self, toast_widget: ToastWidget):
        """Position toast widget on screen"""
        try:
            parent_x = self.parent_window.winfo_x()
            parent_y = self.parent_window.winfo_y()
            parent_width = self.parent_window.winfo_width()
            parent_height = self.parent_window.winfo_height()

            toast_width = 350
            toast_height = 80

            x = parent_x + parent_width - toast_width - self.position_offset_x
            y = (
                parent_y
                + parent_height
                - toast_height
                - self.position_offset_y
                - (len(self.active_toasts) - 1) * (toast_height + self.toast_spacing)
            )

            toast_widget.place(x=x, y=y)
        except Exception as e:  # pragma: no cover
            print(f"Error positioning toast: {e}")

    def _reposition_toasts(self):
        """Reposition all active toasts"""
        for i, toast_widget in enumerate(self.active_toasts):
            try:
                parent_x = self.parent_window.winfo_x()
                parent_y = self.parent_window.winfo_y()
                parent_width = self.parent_window.winfo_width()
                parent_height = self.parent_window.winfo_height()

                toast_width = 350
                toast_height = 80

                x = parent_x + parent_width - toast_width - self.position_offset_x
                y = (
                    parent_y
                    + parent_height
                    - toast_height
                    - self.position_offset_y
                    - i * (toast_height + self.toast_spacing)
                )

                toast_widget.place(x=x, y=y)
            except Exception as e:  # pragma: no cover
                print(f"Error repositioning toast {i}: {e}")

    def clear_all_toasts(self):
        """Clear all active toasts and queue"""
        with self._lock:
            self.toast_queue.clear()
            for toast_widget in self.active_toasts.copy():
                toast_widget.dismiss()

    def show_info(self, message: str, **kwargs):
        """Convenience method for info toasts"""
        return self.show_toast(message, ToastType.INFO, **kwargs)

    def show_success(self, message: str, **kwargs):
        """Convenience method for success toasts"""
        return self.show_toast(message, ToastType.SUCCESS, **kwargs)

    def show_warning(self, message: str, **kwargs):
        """Convenience method for warning toasts"""
        return self.show_toast(message, ToastType.WARNING, **kwargs)

    def show_danger(self, message: str, **kwargs):
        """Convenience method for danger toasts"""
        return self.show_toast(message, ToastType.DANGER, **kwargs)


toast_manager: Optional[ToastManager] = None


def initialize_toast_manager(parent_window) -> ToastManager:
    """Initialize global toast manager"""
    global toast_manager
    toast_manager = ToastManager(parent_window)
    return toast_manager


def show_toast(message: str, toast_type: ToastType = ToastType.INFO, **kwargs):
    """Global convenience function for showing toasts"""
    if toast_manager:
        return toast_manager.show_toast(message, toast_type, **kwargs)
    print(f"Toast Manager not initialized: {message}")
    return None


def show_info(message: str, **kwargs):
    return show_toast(message, ToastType.INFO, **kwargs)


def show_success(message: str, **kwargs):
    return show_toast(message, ToastType.SUCCESS, **kwargs)


def show_warning(message: str, **kwargs):
    return show_toast(message, ToastType.WARNING, **kwargs)


def show_danger(message: str, **kwargs):
    return show_toast(message, ToastType.DANGER, **kwargs)
