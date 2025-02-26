import typer
import uvicorn
import secrets
from typing import Optional
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
        computer: BaseComputer,
        api_token: Optional[str] = None,
    ):
        self.app = FastAPI()
        self._computer = computer
        self.api_token = api_token or secrets.token_urlsafe(32)

        security = HTTPBearer()

        def verify_token(
            credentials: HTTPAuthorizationCredentials = Security(security),
        ):
            if credentials.credentials != self.api_token:
                raise HTTPException(status_code=401, detail="Invalid token")
            return credentials.credentials

        @self.app.post("/reset")
        async def reset(token: str = Depends(verify_token)):
            return self.get_computer().reset()

        @self.app.post("/execute/command")
        async def execute_command(
            action: CommandAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_command(action)}

        @self.app.post("/execute/keyboard/key_down")
        async def execute_keyboard_key_down(
            action: KeyboardKeyDownAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_keyboard_key_down(action)}

        @self.app.post("/execute/keyboard/key_release")
        async def execute_keyboard_key_release(
            action: KeyboardKeyReleaseAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_keyboard_key_release(action)}

        @self.app.post("/execute/keyboard/key_press")
        async def execute_keyboard_key_press(
            action: KeyboardKeyPressAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_keyboard_key_press(action)}

        @self.app.post("/execute/keyboard/hotkey")
        async def execute_keyboard_hotkey(
            action: KeyboardHotkeyAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_keyboard_hotkey(action)}

        @self.app.post("/execute/type")
        async def execute_type(action: TypeAction, token: str = Depends(verify_token)):
            return {"success": self.get_computer().execute_type(action)}

        @self.app.post("/execute/mouse/move")
        async def execute_mouse_move(
            action: MouseMoveAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_mouse_move(action)}

        @self.app.post("/execute/mouse/scroll")
        async def execute_mouse_scroll(
            action: MouseScrollAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_mouse_scroll(action)}

        @self.app.post("/execute/mouse/button_down")
        async def execute_mouse_button_down(
            action: MouseButtonDownAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_mouse_button_down(action)}

        @self.app.post("/execute/mouse/button_up")
        async def execute_mouse_button_up(
            action: MouseButtonUpAction, token: str = Depends(verify_token)
        ):
            return {"success": self.get_computer().execute_mouse_button_up(action)}

        @self.app.get("/observation")
        async def get_observation(token: str = Depends(verify_token)):
            return self.get_computer().get_observation()


    def get_computer(self) -> BaseComputer:
        if self._computer is None:
            self._computer = self._computer_cls(**self._computer_cls_kwargs)
        return self._computer

    def start_server(self, host="0.0.0.0", port=8000):
        uvicorn.run(self.app, host=host, port=port)
