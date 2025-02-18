from textwrap import dedent
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.env_base import Action, Observation
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.output_parsers.string import StrOutputParser
from langchain.schema import ChatMessage
from commandagi_j2.utils.chat_model_utils import get_chat_model
import base64


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
        self.chat_model = get_chat_model(**self.chat_model_options)
        self.str_output_parser = StrOutputParser()

    def reset(self):
        """Reset agent state"""
        self.total_reward = 0.0

    def act(self, observation: Observation) -> Action:
        """Analyze screenshot and decide on next action using LangChain chat model."""
        # Convert image to base64
        with open(observation, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

        input_messages = [
            ChatMessage(
                role="user",
                content=[
                    {
                        "type": "text",
                        "text": dedent(
                            """\
                            Look at this screenshot and suggest a single action to take. 
                            Respond with a function call to the action you want to take.

                            Action space:
                            click(x, y)
                            type(text)
                            pass()
                            """
                        ).strip(),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{encoded_image}"},
                    },
                    {
                        "type": "text",
                        "text": dedent(
                            """\
                            Now, please respond with a function call to the action you want to take.
                            """
                        ).strip(),
                    },
                ],
            ),
        ]

        response = self.chat_model.invoke(input_messages)
        response_str = self.str_output_parser.invoke(response.content.strip())
        return response_str

    def update(self, reward: float):
        """Update agent with reward feedback"""
        self.total_reward += reward
