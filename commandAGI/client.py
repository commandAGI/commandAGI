from typing import Optional


class Client:
    _manually_set_api_key: str | None = None

    def __init__(self, api_key: str):
        self._manually_set_api_key = api_key

    @property
    def api_key(self) -> str:
        if self._manually_set_api_key:
            return self._manually_set_api_key
        raise NotImplementedError("API key not set")
    
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
    
    def start_ubuntu(self, ...): ...
    def start_macos(self, ...): ...
    def start_windows(self, ...): ...
    def start_web_browser(self, ...): ...
    def start_terminal(self, ...): ...
    
