import os
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk


class EnvironmentViewer:
    def __init__(self, env, refresh_rate=100, show_mouse=True, show_keyboard=True):
        """
        Initialize the Environment Viewer.

        env: An environment instance that supports _get_observation(), returning a ComputerObservation.
        refresh_rate: Refresh interval in milliseconds.
        show_mouse: Whether to display mouse state information.
        show_keyboard: Whether to display keyboard state information.
        """
        self.env = env
        self.refresh_rate = refresh_rate  # in milliseconds
        self.show_mouse = show_mouse
        self.show_keyboard = show_keyboard

        self.root = tk.Tk()
        self.root.title("Environment Viewer")

        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Image display label
        self.image_label = ttk.Label(self.main_frame)
        self.image_label.pack(side="top", fill="both", expand=True)

        # Info frame for mouse and keyboard states
        self.info_frame = ttk.Frame(self.main_frame)
        self.info_frame.pack(side="bottom", fill="x")

        self.mouse_state_label = ttk.Label(self.info_frame, text="Mouse State: N/A")
        self.keyboard_state_label = ttk.Label(
            self.info_frame, text="Keyboard State: N/A"
        )

        if self.show_mouse:
            self.mouse_state_label.pack(side="left", padx=10, pady=5)
        if self.show_keyboard:
            self.keyboard_state_label.pack(side="left", padx=10, pady=5)

        # Settings button
        self.settings_button = ttk.Button(
            self.main_frame, text="Settings", command=self.open_settings
        )
        self.settings_button.pack(side="bottom", pady=5)

        # For storing image reference
        self.photo_image = None

        # Start update loop
        self.update_view()

    def open_settings(self):
        """Open the settings window to adjust refresh rate and toggle states display."""
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Viewer Settings")

        ttk.Label(self.settings_window, text="Refresh Rate (ms):").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.refresh_rate_var = tk.IntVar(value=self.refresh_rate)
        self.refresh_rate_scale = ttk.Scale(
            self.settings_window,
            from_=50,
            to=1000,
            orient="horizontal",
            variable=self.refresh_rate_var,
        )
        self.refresh_rate_scale.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Checkbuttons for mouse and keyboard
        self.mouse_var = tk.BooleanVar(value=self.show_mouse)
        self.keyboard_var = tk.BooleanVar(value=self.show_keyboard)

        self.mouse_check = ttk.Checkbutton(
            self.settings_window, text="Show Mouse State", variable=self.mouse_var
        )
        self.mouse_check.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        self.keyboard_check = ttk.Checkbutton(
            self.settings_window, text="Show Keyboard State", variable=self.keyboard_var
        )
        self.keyboard_check.grid(
            row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w"
        )

        # Apply button
        apply_button = ttk.Button(
            self.settings_window, text="Apply", command=self.apply_settings
        )
        apply_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Make the grid expand properly
        self.settings_window.columnconfigure(1, weight=1)

    def apply_settings(self):
        """Apply settings from the settings window."""
        self.refresh_rate = int(self.refresh_rate_var.get())
        self.show_mouse = self.mouse_var.get()
        self.show_keyboard = self.keyboard_var.get()

        # Update info labels: pack or forget according to settings
        if self.show_mouse and not self.mouse_state_label.winfo_ismapped():
            self.mouse_state_label.pack(side="left", padx=10, pady=5)
        elif not self.show_mouse and self.mouse_state_label.winfo_ismapped():
            self.mouse_state_label.pack_forget()
            self.mouse_state_label.configure(text="Mouse State: N/A")

        if self.show_keyboard and not self.keyboard_state_label.winfo_ismapped():
            self.keyboard_state_label.pack(side="left", padx=10, pady=5)
        elif not self.show_keyboard and self.keyboard_state_label.winfo_ismapped():
            self.keyboard_state_label.pack_forget()
            self.keyboard_state_label.configure(text="Keyboard State: N/A")

        self.settings_window.destroy()

    def update_view(self):
        """Update the viewer widget with the latest observation from the environment."""
        try:
            observation = self.env._get_observation()
        except Exception as e:
            print(f"Error in _get_observation: {e}")
            observation = None

        # Update screenshot image
        if observation and observation.screenshot:
            # Assuming the screenshot observation has an attribute 'screenshot' that is the file path
            image_path = observation.screenshot.screenshot
            if os.path.exists(image_path):
                try:
                    image = Image.open(image_path)
                    # Resize image based on label dimensions (fallback to 800x600)
                    width = self.image_label.winfo_width() or 800
                    height = self.image_label.winfo_height() or 600
                    image = image.resize((width, height), Image.ANTIALIAS)
                    self.photo_image = ImageTk.PhotoImage(image)
                    self.image_label.configure(image=self.photo_image, text="")
                except Exception as e:
                    print(f"Error loading image: {e}")
                    self.image_label.configure(text="Error loading image")
            else:
                self.image_label.configure(text="Screenshot file not found")
        else:
            self.image_label.configure(text="No screenshot available")

        # Update mouse state information if enabled
        if self.show_mouse:
            if observation and observation.mouse_state:
                mouse_text = f"Mouse Pos: {observation.mouse_state.position}, Buttons: {observation.mouse_state.buttons}"
                self.mouse_state_label.configure(text=mouse_text)
            else:
                self.mouse_state_label.configure(text="Mouse State: N/A")

        # Update keyboard state information if enabled
        if self.show_keyboard:
            if observation and observation.keyboard_state:
                keyboard_text = f"Keys: {observation.keyboard_state.keys}"
                self.keyboard_state_label.configure(text=keyboard_text)
            else:
                self.keyboard_state_label.configure(text="Keyboard State: N/A")

        # Schedule next update
        self.root.after(self.refresh_rate, self.update_view)

    def run(self):
        self.root.mainloop()


# If run as main for testing purposes, use a dummy environment
if __name__ == "__main__":
    import random

    from commandagi_j2.computers.computer_types import (
        ComputerObservation, KeyboardKey, KeyboardStateObservation,
        MouseButton, MouseStateObservation, ScreenshotObservation)

    class DummyEnv:
        def _get_observation(self):
            # For testing, assume there is a valid image file named 'sample.jpg' in the current directory.
            screenshot = ScreenshotObservation(screenshot="sample.jpg")
            mouse_state = MouseStateObservation(
                buttons={MouseButton.LEFT: random.choice([True, False])},
                position=(random.randint(0, 800), random.randint(0, 600)),
            )
            keyboard_state = KeyboardStateObservation(
                keys={
                    KeyboardKey.A: random.choice([True, False]),
                    KeyboardKey.B: random.choice([True, False]),
                }
            )
            return ComputerObservation(
                screenshot=screenshot,
                mouse_state=mouse_state,
                keyboard_state=keyboard_state,
            )

    env = DummyEnv()
    viewer = EnvironmentViewer(
        env, refresh_rate=100, show_mouse=True, show_keyboard=True
    )
    viewer.run()
