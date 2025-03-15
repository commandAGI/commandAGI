import json
import os
from pathlib import Path
from typing import Dict, Optional

import platformdirs
from pydantic import BaseModel, BaseSettings, EmailStr, Field, root_validator


class UserProfile(BaseModel):
    """Schema for user profile"""

    name: str = Field(default="default")
    email: str = Field(default="default")
    api_key: str = Field(default="")


class AuthState(BaseModel):
    """Schema for persistent auth state"""

    profiles: Dict[str, UserProfile] = Field(default_factory=dict)
    active_api_key: Optional[str] = Field(default=None)

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
    api_base_url: str = Field(
        default="https://api.commandagi.com", env="COMMANDAGI_BASE_URL"
    )

    # Auth state
    auth_state: AuthState = Field(default_factory=AuthState)

    @property
    def active_api_key(self) -> Optional[str]:
        """Get the active API key from environment or saved state"""
        # First check environment variable
        env_key = os.getenv("COMMANDAGI_API_KEY")
        if env_key:
            return env_key
        # Fall back to saved state
        return self.auth_state.active_api_key

    @active_api_key.setter
    def active_api_key(self, value: Optional[str]):
        self.auth_state.active_api_key = value
        self.save_auth_state()

    @active_api_key.deleter
    def active_api_key(self):
        self.auth_state.active_api_key = None
        self.save_auth_state()

    @property
    def current_profile(self) -> Optional[UserProfile]:
        """Get the current active profile"""
        key = self.active_api_key
        if not key:
            return None
        return self.profiles.get(key)

    @property
    def profiles(self) -> Dict[str, UserProfile]:
        return self.auth_state.profiles

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
