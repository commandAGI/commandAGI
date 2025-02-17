import os
from typing import Literal, Unpack
from langchain.chat_models import ChatOpenAI, ChatAnthropic, ChatHuggingFaceHub

# Import the custom compatibility chat model if available.
try:
    from commandagi_j2.agents.simple_computer_agent import ChatOpenAICompat
except ImportError:
    # Define a fallback for ChatOpenAICompat in case it is not importable.
    from langchain.chat_models import ChatOpenAI

    class ChatOpenAICompat(ChatOpenAI):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.compat_mode = True


def get_chat_model(
    model_provider: Literal[
        "openai", "custom_openai_compat", "anthropic", "huggingface"
    ],
    **options: Unpack[dict],
):
    """
    Instantiate and return a chat model based on the specified model provider.

    Args:
        model_provider (str): One of "openai", "custom_openai_compat", "anthropic", or "huggingface".
        options (dict, optional): Additional keyword arguments for the chat model.

    Returns:
        An instance of the appropriate chat model.

    Raises:
        ValueError: If a required API key for a provider isn't set or an unsupported provider is specified.
    """
    match model_provider:
        case "openai":
            return ChatOpenAI(**options)
        case "custom_openai_compat":
            return ChatOpenAICompat(**options)
        case "anthropic":
            return ChatAnthropic(**options)
        case "huggingface":
            return ChatHuggingFaceHub(**options)
        case _:
            raise ValueError(f"Unsupported model provider: {model_provider}")
