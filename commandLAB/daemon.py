import typer
import uvicorn
import secrets
from typing import Type, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from commandLAB.computers.base_computer import BaseComputer
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
from commandLAB.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandLAB.types import (
    CommandAction,
    KeyboardHotkeyAction,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
)


class ComputerDaemon:
    def __init__(
        self,
        computer_cls: Type[BaseComputer] = LocalPynputComputer,
        computer_cls_kwargs: Dict[str, Any] = None,
    ):
        app = FastAPI()
        security = HTTPBearer()
        API_TOKEN = secrets.token_urlsafe(32)

        self._computer_cls = computer_cls
        self._computer_cls_kwargs = computer_cls_kwargs or {}
        self._computer = None

        def verify_token(
            credentials: HTTPAuthorizationCredentials = Security(security),
        ):
            if credentials.credentials != API_TOKEN:
                raise HTTPException(status_code=401, detail="Invalid token")
            return credentials.credentials

        @app.post("/reset")
        async def reset(token: str = Depends(verify_token)):
            return self.get_computer().reset()

        @app.post("/execute/command")
        async def execute_command(
            action: CommandAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_command(action)}

        @app.post("/execute/keyboard/key_down")
        async def execute_keyboard_key_down(
            action: KeyboardKeyDownAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_keyboard_key_down(action)}

        @app.post("/execute/keyboard/key_release")
        async def execute_keyboard_key_release(
            action: KeyboardKeyReleaseAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_keyboard_key_release(action)}

        @app.post("/execute/keyboard/key_press")
        async def execute_keyboard_key_press(
            action: KeyboardKeyPressAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_keyboard_key_press(action)}

        @app.post("/execute/keyboard/hotkey")
        async def execute_keyboard_hotkey(
            action: KeyboardHotkeyAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_keyboard_hotkey(action)}

        @app.post("/execute/type")
        async def execute_type(action: TypeAction, token: str = Depends(verify_token)):
            return {"success": self.get_computer().execute_type(action)}

        @app.post("/execute/mouse/move")
        async def execute_mouse_move(
            action: MouseMoveAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_mouse_move(action)}

        @app.post("/execute/mouse/scroll")
        async def execute_mouse_scroll(
            action: MouseScrollAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_mouse_scroll(action)}

        @app.post("/execute/mouse/button_down")
        async def execute_mouse_button_down(
            action: MouseButtonDownAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_mouse_button_down(action)}

        @app.post("/execute/mouse/button_up")
        async def execute_mouse_button_up(
            action: MouseButtonUpAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_mouse_button_up(action)}

        @app.get("/observation")
        async def get_observation(token: str = Depends(verify_token)):
            return self.get_computer().get_observation()

        self.app = app
        self.API_TOKEN = API_TOKEN

    def get_computer(self) -> BaseComputer:
        if self._computer is None:
            self._computer = self._computer_cls(**self._computer_cls_kwargs)
        return self._computer

    def start_server(self):
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)


def main(port: int = 8000, backend: str = "pynput", **kwargs):
    # Configure computer backend
    computer_cls = (
        LocalPynputComputer if backend == "pynput" else LocalPyAutoGUIComputer
    )
    daemon = ComputerDaemon(computer_cls=computer_cls, computer_cls_kwargs=kwargs)

    print(f"Starting daemon on port {port}")
    print(f"API Token: {daemon.API_TOKEN}")
    daemon.start_server()


if __name__ == "__main__":
    typer.run(main)
