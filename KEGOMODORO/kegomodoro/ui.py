"""UI components, dialogs, and styling constants for KEGOMODORO."""

import tkinter as tk
from tkinter import simpledialog
from typing import Optional
from PIL import Image, ImageTk

# ----------------- Palette and Constants (Original Tomato) ----------------- #
PINK = "#e2979c"
RED = "#e7305b"
GREEN = "#77ed95"
YELLOW = "#f7f5dd"
ORANGE = "#fcba03"
DEEP_GOLD_COLOR = "#EFB036"
TOMATO_COLOR = "#f26849"
WHITE = "#feffff"
FONT_NAME = "Courier"

MAIN_MINUTE_FONT_SIZE = 30
MAIN_HOUR_FONT_SIZE = 20
FLOATING_MINUTE_FONT_SIZE = 28
FLOATING_HOUR_FONT_SIZE = 23

HOURS_X = 7
HOURS_Y = 110
MINUTE_X = 38
MINUTE_Y = 110


class DraggableWindow(tk.Toplevel):
    """Draggable, transparent, borderless, always-on-top floating timer window."""

    def __init__(self, master: tk.Misc, image_path: str):
        super().__init__(master)
        self.title("KEGOMODORO Floating Timer")
        self.overrideredirect(True)
        self.geometry("+1150+440")
        self.resizable(False, False)
        self.configure(bg="white")

        try:
            self.lift()
            self.wm_attributes("-topmost", True)
            self.wm_attributes("-transparentcolor", "white")
        except Exception:
            pass

        # Load tomato.gif image
        self.image = ImageTk.PhotoImage(Image.open(image_path))
        self.image_label = tk.Label(
            self, image=self.image, bg="white", highlightthickness=0
        )
        self.image_label.pack()

        # Floating timer label
        self.timer_label = tk.Label(
            self,
            text="00:00",
            font=(FONT_NAME, FLOATING_MINUTE_FONT_SIZE, "bold"),
            foreground=WHITE,
            background=TOMATO_COLOR,
        )
        self.timer_label.place(x=MINUTE_X, y=MINUTE_Y)

        self.start_x = 0
        self.start_y = 0
        self.dragging = False

        for widget in (self, self.image_label, self.timer_label):
            widget.bind("<ButtonPress-1>", self.on_press)
            widget.bind("<B1-Motion>", self.on_drag)
            widget.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event: tk.Event) -> None:
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.dragging = True
        # Keep receiving pointer events when the cursor leaves this small,
        # borderless window while it is being moved.
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def on_drag(self, event: tk.Event) -> None:
        if not self.dragging:
            return

        delta_x = event.x_root - self.start_x
        delta_y = event.y_root - self.start_y
        new_x = self.winfo_x() + delta_x
        new_y = self.winfo_y() + delta_y
        self.geometry(f"+{new_x}+{new_y}")
        self.start_x = event.x_root
        self.start_y = event.y_root

    def on_release(self, _event: tk.Event) -> None:
        self.dragging = False
        try:
            if self.grab_current() == self:
                self.grab_release()
        except tk.TclError:
            pass

    def update_display(self, text: str, show_hours: bool) -> None:
        if show_hours:
            self.timer_label.config(
                text=text, font=(FONT_NAME, FLOATING_HOUR_FONT_SIZE, "bold")
            )
            self.timer_label.place(x=HOURS_X, y=HOURS_Y)
        else:
            self.timer_label.config(
                text=text, font=(FONT_NAME, FLOATING_MINUTE_FONT_SIZE, "bold")
            )
            self.timer_label.place(x=MINUTE_X, y=MINUTE_Y)


class LargeAskStringDialog(simpledialog.Dialog):
    """Multiline plain-text dialog for entering notes without opening a secondary root window."""

    def __init__(
        self, parent: tk.Misc, title: str = "Save your note", prompt: str = "Write your note:"
    ):
        self.prompt_text = prompt
        self.result: Optional[str] = None
        self.text_widget: Optional[tk.Text] = None
        super().__init__(parent, title=title)

    def body(self, master: tk.Frame) -> tk.Widget:
        tk.Label(master, text=self.prompt_text).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.text_widget = tk.Text(master, height=10, width=50)
        self.text_widget.grid(row=1, column=0, padx=5, pady=5)
        self.text_widget.focus_set()
        return self.text_widget

    def apply(self) -> None:
        if self.text_widget is not None:
            self.result = self.text_widget.get("1.0", tk.END).strip()
