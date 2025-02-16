import tkinter as tk
from PIL import Image, ImageTk

class TkRender:
    """
    A Tkinter-based renderer that updates its display every 100ms.
    Expects the environment (env) to have a _get_observation() method that returns
    the path to the current screenshot image.
    """
    def __init__(self, env):
        self.env = env
        self.root = tk.Tk()
        self.root.title("Environment Render")
        self.label = tk.Label(self.root)
        self.label.pack(fill="both", expand=True)
        # Kick off the update loop
        self._update_render()

    def _update_render(self):
        """
        Update the label with a new screenshot and reschedule after 100ms.
        """
        image_path = self.env._get_observation()
        try:
            image = Image.open(image_path)
            # Use current window dimensions (or fallback to 800x600)
            width = self.root.winfo_width() or 800
            height = self.root.winfo_height() or 600
            image = image.resize((width, height), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(image)
            self.label.configure(image=photo)
            self.label.image = photo  # keep a reference to prevent garbage collection
        except Exception as e:
            print(f"Failed to update render: {e}")
        
        # Schedule the next update in 100ms
        self.root.after(100, self._update_render)

    def run(self):
        """
        Run the Tkinter main loop.
        """
        self.root.mainloop() 