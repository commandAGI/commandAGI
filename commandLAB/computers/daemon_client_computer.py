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


class ProvisioningMethod(str, Enum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    MANUAL = "manual"

    def get_provisioner_cls(self) -> type[BaseComputerProvisioner]:
        """Return the appropriate provisioner class based on the provisioning method"""
        match self:
            case ProvisioningMethod.MANUAL:
                from commandLAB.computers.provisioners.manual_provisioner import (
                    ManualProvisioner,
                )

                return ManualProvisioner
            case ProvisioningMethod.DOCKER:
                from commandLAB.computers.provisioners.docker_provisioner import (
                    DockerProvisioner,
                )

                return DockerProvisioner
            case ProvisioningMethod.KUBERNETES:
                from commandLAB.computers.provisioners.kubernetes_provisioner import (
                    KubernetesProvisioner,
                )

                return KubernetesProvisioner
            case ProvisioningMethod.AWS:
                from commandLAB.computers.provisioners.aws_provisioner import (
                    AWSProvisioner,
                )

                return AWSProvisioner
            case ProvisioningMethod.AZURE:
                from commandLAB.computers.provisioners.azure_provisioner import (
                    AzureProvisioner,
                )

                return AzureProvisioner
            case ProvisioningMethod.GCP:
                from commandLAB.computers.provisioners.gcp_provisioner import (
                    GCPProvisioner,
                )

                return GCPProvisioner
            case _:
                raise ImportError(f"No provisioner found for {self}")


class DaemonClientComputer(BaseComputer):
    daemon_base_url: str = "http://localhost"
    daemon_port: int = 8000
    provisioner: Optional[BaseComputerProvisioner] = None

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        provisioning_method: ProvisioningMethod = ProvisioningMethod.MANUAL,
        **data,
    ):
        # Initialize the base model first to ensure all fields are set
        super().__init__(**data)
        # Now we can safely access daemon_port
        self.provisioner = provisioning_method.get_provisioner_cls()(
            port=self.daemon_port
        )
        self.provisioner.setup()

    def close(self):
        """Cleanup resources when the object is destroyed"""
        if self.provisioner:
            self.provisioner.teardown()

    def _get_endpoint_url(self, endpoint: str) -> str:
        """Helper method to construct endpoint URLs"""
        return f"{self.daemon_base_url}:{self.daemon_port}/{endpoint}"

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
            self._get_endpoint_url("command"), json=action.model_dump()
        )
        return response.status_code == 200

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("keyboard/key/down"), json=action.model_dump()
        )
        return response.status_code == 200

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("keyboard/key/release"), json=action.model_dump()
        )
        return response.status_code == 200

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("mouse/move"), json=action.model_dump()
        )
        return response.status_code == 200

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("mouse/scroll"), json=action.model_dump()
        )
        return response.status_code == 200

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("mouse/button/down"), json=action.model_dump()
        )
        return response.status_code == 200

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        response = requests.post(
            self._get_endpoint_url("mouse/button/up"), json=action.model_dump()
        )
        return response.status_code == 200
