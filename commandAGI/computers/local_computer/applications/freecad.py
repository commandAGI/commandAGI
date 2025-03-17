import subprocess
from pathlib import Path
from typing import Dict, Optional, Union, Any

from commandAGI.computers.base_computer.applications.base_freecad import BaseFreeCAD


class FreeCAD(BaseFreeCAD):
    """Implementation of FreeCAD operations for local computer."""

    def __init__(self):
        super().__init__()
        self.process = None
        self.current_document = None

    def start(self) -> bool:
        """Start the FreeCAD application in GUI mode."""
        try:
            # Start FreeCAD with Python console
            self.process = subprocess.Popen(
                ["freecad", "--console"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return True
        except Exception as e:
            print(f"Failed to start FreeCAD: {e}")
            return False

    def open_project(self, file_path: Union[str, Path]) -> bool:
        file_path = str(Path(file_path).absolute())
        command = f"FreeCAD.open('{file_path}')"
        return self.send_command(command)

    def save_project(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        if file_path:
            file_path = str(Path(file_path).absolute())
            command = f"FreeCAD.ActiveDocument.saveAs('{file_path}')"
        else:
            command = "FreeCAD.ActiveDocument.save()"
        return self.send_command(command)

    def create_document(self, name: str) -> bool:
        command = f"FreeCAD.newDocument('{name}')"
        return self.send_command(command)

    def add_geometry(self, geometry_type: str, parameters: Dict[str, Any]) -> bool:
        commands = [
            "import Part",
            f"doc = FreeCAD.ActiveDocument",
        ]

        if geometry_type.lower() == "box":
            length = parameters.get("length", 10)
            width = parameters.get("width", 10)
            height = parameters.get("height", 10)
            commands.extend(
                [
                    f"box = Part.makeBox({length}, {width}, {height})",
                    "obj = doc.addObject('Part::Feature', 'Box')",
                    "obj.Shape = box",
                ]
            )
        # Add more geometry types as needed

        commands.append("doc.recompute()")
        return all(self.send_command(cmd) for cmd in commands)

    def execute_macro(self, macro_path: Union[str, Path]) -> bool:
        macro_path = str(Path(macro_path).absolute())
        command = f"FreeCAD.openDocument('{macro_path}')"
        return self.send_command(command)

    def export_step(self, output_path: Union[str, Path]) -> bool:
        output_path = str(Path(output_path).absolute())
        commands = [
            "import Import",
            f"Import.export([FreeCAD.ActiveDocument.Objects], '{output_path}')",
        ]
        return all(self.send_command(cmd) for cmd in commands)

    def send_command(self, command: str) -> bool:
        """Send a Python command to FreeCAD's Python console."""
        if not self.process:
            return False

        try:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
            return True
        except Exception as e:
            print(f"Failed to send command: {e}")
            return False

    def stop(self) -> bool:
        """Stop the FreeCAD application."""
        if self.process:
            try:
                self.send_command("FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)")
                self.send_command("FreeCAD.closeApplication()")
                self.process.terminate()
                self.process = None
                return True
            except Exception as e:
                print(f"Failed to stop FreeCAD: {e}")
                return False
        return True
