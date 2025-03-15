from typing import Optional
from commandAGI._internal.config import Config

class Client:
    _manually_set_api_key: str | None = None
    _client_config: Config | None = None

    def __init__(self, api_key: str):
        self._manually_set_api_key = api_key

    @property
    def api_key(self) -> str:
        if self._manually_set_api_key:
            return self._manually_set_api_key
        # otherwise, use the default config
    
    @api_key.setter
    def api_key(self, value: str):
        self._manually_set_api_key = value

    def save_api_key(self):
        pass

    def login(self):
        pass

    def current_profile(self):
        pass

    def switch_account(self):
        pass

    def logout(self):
        pass
    
    def act(
        self,
        prompt: str,
        tools: list[BaseTool],
        output_schema: Optional[type[TSchema]] = None,
    ) -> TSchema|None:
        pass
    
    def start_computer(self, ..., host: Literal["local", "commandagi", "aws", "gcp", "azure"] = "local"): ...
    def start_ubuntu(self, ..., host: Literal["local", "commandagi", "aws", "gcp", "azure"] = "local"): ...
    def start_macos(self, ..., host: Literal["local", "commandagi", "aws", "gcp", "azure"] = "local"): ...
    def start_windows(self, ..., host: Literal["local", "commandagi", "aws", "gcp", "azure"] = "local"): ...
    def start_web_browser(self, ..., host: Literal["local", "commandagi", "aws", "gcp", "azure"] = "local"): ...
    def start_terminal(self, ..., host: Literal["local", "commandagi", "aws", "gcp", "azure"] = "local"): ...
    
