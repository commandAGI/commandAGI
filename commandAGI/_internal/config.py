import os
from pathlib import Path
from typing import Dict, Optional

import platformdirs
from pydantic import BaseSettings, EmailStr, Field, root_validator, BaseModel
import json


class UserProfile(BaseModel):
    """Schema for user profile"""

    name: str = Field(default="default")
    email: str = Field(default="default")
    token: str = Field(default="")


class AuthState(BaseModel):
    """Schema for persistent auth state"""

    profiles: Dict[EmailStr, UserProfile] = Field(default_factory=dict)
    active_profile_email: Optional[EmailStr] = Field(default=None)

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "AuthState":
        try:
            return cls.model_validate_json(json_str)
        except json.JSONDecodeError:
            return cls()


class Config(BaseSettings):
    PROJ_DIR: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent,
    )
    APPDIR: Path = Field(
        default=Path(
            platformdirs.user_data_dir(appname="commandAGI", appauthor="commandAGI")
        ),
        env="COMMANDAGI_APPDIR",
    )

    DEV_MODE: bool = Field(default=False, env="COMMANDAGI_DEV_MODE")
    COMMANDAGI_HUB_URL: str = Field(
        default="https://api.commandagi.com", env="COMMANDAGI_HUB_URL"
    )

    # Auth state
    auth_state: AuthState = Field(default_factory=AuthState)

    @property
    def profiles(self) -> Dict[str, UserProfile]:
        return self.auth_state.profiles

    @property
    def active_profile_email(self) -> Optional[EmailStr]:
        return self.auth_state.active_profile_email

    @active_profile_email.setter
    def active_profile_email(self, value: Optional[EmailStr]):
        self.auth_state.active_profile_email = value

    @property
    def current_token(self) -> Optional[str]:
        """Get the current active token"""
        if not self.active_profile_email:
            return None

        if self.active_profile_email not in self.profiles:
            raise ValueError(f"Profile {self.active_profile_email} not found")

        return self.profiles[self.active_profile_email].token

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @root_validator(pre=True)
    def load_auth_state(cls, values):
        """Load auth state from persistent storage"""
        appdir = values.get("APPDIR") or Path(
            platformdirs.user_data_dir(appname="commandAGI", appauthor="commandAGI")
        )
        auth_file = appdir / "auth.json"

        if auth_file.exists():
            auth_state = AuthState.from_json(auth_file.read_text())
            values["auth_state"] = auth_state
        return values

    def save_auth_state(self):
        """Save auth state to persistent storage"""
        self.APPDIR.mkdir(parents=True, exist_ok=True)
        auth_file = self.APPDIR / "auth.json"
        auth_file.write_text(self.auth_state.to_json())


config = Config()
