import openai
import os
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.env_base import Action, Observation
from langchain.chat_models import ChatOpenAI, ChatAnthropic, ChatHuggingFaceHub
from langchain.schema import HumanMessage
from commandagi_j2.utils.chat_model_utils import get_chat_model


# New custom chat model class for the custom_openai_compat provider.
class ChatOpenAICompat(ChatOpenAI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set a flag or perform adjustments unique to custom compatibility mode.
        self.compat_mode = True


class SimpleComputerAgent(BaseAgent):

    def __init__(self, chat_model_options: dict):
        self.total_reward = 0.0
        self.chat_model_options = chat_model_options

    @property
    def main_chat_model(self):
        self.chat_model = get_chat_model(**self.chat_model_options)
        return self.chat_model

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
