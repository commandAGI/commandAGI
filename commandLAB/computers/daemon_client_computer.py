import os
import platform
import subprocess
from enum import Enum
from typing import Optional

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import (
    CommandAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    KeyboardStateObservation,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseStateObservation,
    ScreenshotObservation,
)
import requests
from commandLAB.computers.provisioners.base_provisioner import BaseComputerProvisioner
from commandLAB.computers.provisioners.manual_provisioner import ManualProvisioner
from commandLAB.computers.provisioners.docker_provisioner import DockerProvisioner


class ProvisioningMethod(str, Enum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    MANUAL = "manual"


class DaemonClientComputer(BaseComputer):
    base_url: str = "http://localhost"
    port: int = 8000
    provisioning_method: ProvisioningMethod = ProvisioningMethod.MANUAL
    provisioner: Optional[BaseComputerProvisioner] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.provisioner = self._get_provisioner()
        self._setup_daemon()

    def _get_provisioner(self) -> BaseComputerProvisioner:
        """Get the appropriate provisioner based on the provisioning method"""
        if self.provisioning_method == ProvisioningMethod.MANUAL:
            return ManualProvisioner(port=self.port)
        elif self.provisioning_method == ProvisioningMethod.DOCKER:
            return DockerProvisioner(port=self.port)
        else:
            raise NotImplementedError(f"{self.provisioning_method} provisioning not yet implemented")

    def _setup_daemon(self):
        """Setup the daemon using the selected provisioner"""
        if self.provisioner:
            self.provisioner.setup()

    def __del__(self):
        """Cleanup resources when the object is destroyed"""
        if self.provisioner:
            self.provisioner.teardown()

    def _get_endpoint_url(self, endpoint: str) -> str:
        """Helper method to construct endpoint URLs"""
        return f"{self.base_url}:{self.port}/{endpoint}"

    def get_screenshot(self) -> ScreenshotObservation:
        response = requests.get(self._get_endpoint_url("screenshot"))
        response.raise_for_status()
        return ScreenshotObservation(**response.json())

    def get_mouse_state(self) -> MouseStateObservation:
        response = requests.get(self._get_endpoint_url("mouse/state"))
        response.raise_for_status()
        return MouseStateObservation(**response.json())

    def get_keyboard_state(self) -> KeyboardStateObservation:
        response = requests.get(self._get_endpoint_url("keyboard/state"))
        response.raise_for_status()
        return KeyboardStateObservation(**response.json())

    def execute_command(self, action: CommandAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("command"),
            json=action.model_dump()
        )
        return response.status_code == 200

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("keyboard/key/down"),
            json=action.model_dump()
        )
        return response.status_code == 200

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("keyboard/key/release"),
            json=action.model_dump()
        )
        return response.status_code == 200

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("mouse/move"),
            json=action.model_dump()
        )
        return response.status_code == 200

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("mouse/scroll"),
            json=action.model_dump()
        )
        return response.status_code == 200

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("mouse/button/down"),
            json=action.model_dump()
        )
        return response.status_code == 200

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("mouse/button/up"),
            json=action.model_dump()
        )
        return response.status_code == 200 