import openai
import os
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.env_base import Action, Observation


class SimpleComputerAgent(BaseAgent):

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str | None = None
    openai_model_name: str = "gpt-4o"

    def __init__(self):
        self.total_reward = 0.0

    def reset(self):
        """Reset agent state"""
        self.total_reward = 0.0

    def act(self, observation: Observation) -> Action:
        """Analyze screenshot and decide on next action"""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Look at this screenshot and suggest a single action to take. Respond with just the action in a simple format like 'click 100,200' or 'type Hello'",
                    },
                    {"type": "image_url", "image_url": f"file://{observation}"},
                ],
            }
        ]
        response = openai.ChatCompletion.create(
            messages=messages,
            model=self.openai_model_name,
            **({"api_key": self.openai_api_key} if self.openai_api_key else {}),
            **({"base_url": self.openai_base_url} if self.openai_base_url else {}),
        )
        return response.choices[0].message.content.strip()

    def update(self, reward: float):
        """Update agent with reward feedback"""
        self.total_reward += reward
