import openai
import os
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.env_base import Action, Observation
from langchain.chat_models import ChatOpenAI, ChatAnthropic, ChatHuggingFaceHub
from langchain.schema import HumanMessage

# New custom chat model class for the custom_openai_compat provider.
class ChatOpenAICompat(ChatOpenAI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set a flag or perform adjustments unique to custom compatibility mode.
        self.compat_mode = True


class SimpleComputerAgent(BaseAgent):

    model_provider: str = "openai"
    model_provider_options: dict = {}

    def __init__(self):
        self.total_reward = 0.0

    @property
    def main_chat_model(self):
        extra_args = self.model_provider_options  # Additional model options for all providers.
        if self.model_provider == "openai":
            self.chat_model = ChatOpenAI(
                model_name=self.openai_model_name,
                openai_api_key=self.openai_api_key,
                **extra_args
            )
        elif self.model_provider == "custom_openai_compat":
            self.chat_model = ChatOpenAICompat(
                model_name=self.openai_model_name,
                openai_api_key=self.openai_api_key,
                **extra_args
            )
        elif self.model_provider == "anthropic":
            anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if not anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not set for Anthropic provider")
            self.chat_model = ChatAnthropic(
                model=self.openai_model_name,
                anthropic_api_key=anthropic_api_key,
                **extra_args
            )
        elif self.model_provider == "huggingface":
            huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
            if not huggingface_api_key:
                raise ValueError("HUGGINGFACE_API_KEY not set for HuggingFace provider")
            self.chat_model = ChatHuggingFaceHub(
                repo_id=self.openai_model_name,
                huggingfacehub_api_token=huggingface_api_key,
                **extra_args
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")
        return self.chat_model  # Ensure the instantiated model is returned.

    def reset(self):
        """Reset agent state"""
        self.total_reward = 0.0

    def act(self, observation: Observation) -> Action:
        """Analyze screenshot and decide on next action using LangChain chat model."""
        prompt = (
            f"Look at this screenshot and suggest a single action to take. "
            f"Respond with just the action in a simple format like 'click 100,200' or 'type Hello'. "
            f"The screenshot is located at file://{observation}"
        )
        response = self.chat_model([HumanMessage(content=prompt)])
        return response.content.strip()

    def update(self, reward: float):
        """Update agent with reward feedback"""
        self.total_reward += reward
