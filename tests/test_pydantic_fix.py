import unittest
from pydantic import BaseModel, Field, field_serializer
from typing import Literal, Union, Annotated


class TestPydanticFix(unittest.TestCase):
    def test_discriminator_with_string_literals(self):
        """Test that our fix for the Pydantic discriminator issue works."""

        # Define a base model with a discriminator field
        class BaseAction(BaseModel):
            action_type: str

        # Define subclasses with string literals
        class CommandAction(BaseAction):
            action_type: Literal["command"] = "command"
            command: str

        class TypeAction(BaseAction):
            action_type: Literal["type"] = "type"
            text: str

        # Create instances of the subclasses
        command_action = CommandAction(command="echo hello")
        type_action = TypeAction(text="hello")

        # Check that the instances have the correct type
        self.assertEqual(command_action.action_type, "command")
        self.assertEqual(type_action.action_type, "type")

        # Check that the instances have the correct attributes
        self.assertEqual(command_action.command, "echo hello")
        self.assertEqual(type_action.text, "hello")

        # Test with Union
        ActionUnion = Union[CommandAction, TypeAction]

        # Create a function that accepts the union
        def process_action(action: ActionUnion) -> str:
            if isinstance(action, CommandAction):
                return f"Command: {action.command}"
            elif isinstance(action, TypeAction):
                return f"Type: {action.text}"
            else:
                return "Unknown action"

        # Test the function
        self.assertEqual(process_action(command_action), "Command: echo hello")
        self.assertEqual(process_action(type_action), "Type: hello")


if __name__ == "__main__":
    unittest.main()
