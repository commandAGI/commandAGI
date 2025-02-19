from typing import Literal, Unpack
from langchain_openai.chat_models import ChatOpenAI
from langchain_anthropic.chat_models import ChatAnthropic
from langchain_huggingface.chat_models import ChatHuggingFace


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
            # keep for now
            return ChatOpenAI(**options)
        case "anthropic":
            return ChatAnthropic(**options)
        case "huggingface":
            return ChatHuggingFace(**options)
        case _:
            raise ValueError(f"Unsupported model provider: {model_provider}")
