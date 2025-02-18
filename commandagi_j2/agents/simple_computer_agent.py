from textwrap import dedent
from rich.console import Console
from rich.panel import Panel
from commandagi_j2.envs.computer_types import ComputerAction, ComputerObservation
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from langchain_core.output_parsers.string import StrOutputParser
from langchain.schema import ChatMessage
from commandagi_j2.utils.chat_model_utils import get_chat_model
import base64

console = Console()


class SimpleComputerAgent(BaseAgent[ComputerObservation, ComputerAction]):

    def __init__(self, chat_model_options: dict):
        self.total_reward = 0.0
        self.chat_model_options = chat_model_options
        self.chat_model = get_chat_model(**self.chat_model_options)
        self.str_output_parser = StrOutputParser()

    def reset(self):
        """Reset agent state"""
        self.total_reward = 0.0

    def act(self, observation: ComputerObservation) -> ComputerAction:
        """Analyze screenshot and decide on next action using LangChain chat model."""
        # Convert image to base64
        if not observation.screenshot.screenshot:
            return None

        with open(observation.screenshot.screenshot, "rb") as image_file:
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

        # response = self.chat_model.invoke(input_messages)
        # response_str = self.str_output_parser.invoke(response.content.strip())
        # console.print(Panel(f"🤖 [cyan]Agent response:[/] {response_str}"))

        return ComputerAction()

    def update(self, reward: float):
        """Update agent with reward feedback"""
        self.total_reward += reward
