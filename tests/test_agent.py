import pytest
from commandagi_j2.agents.simple_computer_agent import SimpleComputerAgent
from unittest.mock import patch, MagicMock


class TestSimpleComputerAgent:
    @pytest.fixture
    def agent(self):
        return SimpleComputerAgent()

    def test_reset(self, agent):
        agent.total_reward = 10.0
        agent.reset()
        assert agent.total_reward == 0.0

    def test_update(self, agent):
        agent.reset()
        agent.update(1.0)
        agent.update(2.0)
        assert agent.total_reward == 3.0

    @patch("openai.ChatCompletion.create")
    def test_act(self, mock_create, agent):
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "click 100,100"
        mock_create.return_value = mock_response

        action = agent.act("test_screenshot.png")
        assert isinstance(action, str)
        assert action.startswith("click") or action.startswith("type")
