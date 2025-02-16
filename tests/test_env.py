import pytest
from commandagi_j2.utils.gym2.env_base import Env
from commandagi_j2.envs.local_compute_env import LocalComputeEnv
from pathlib import Path

class TestComputeEnv:
    @pytest.fixture
    def env(self):
        env = LocalComputeEnv()
        yield env
        env.close()
    
    def test_env_implements_base(self, env):
        assert isinstance(env, Env)
    
    def test_reset(self, env):
        observation = env.reset()
        assert isinstance(observation, str)
        assert Path(observation).exists()
    
    def test_step_click(self, env):
        env.reset()
        observation, reward, done, info = env.step("click 100,100")
        assert isinstance(observation, str)
        assert isinstance(reward, float)
        assert isinstance(done, bool)
        assert isinstance(info, dict)
        assert "action_success" in info
    
    def test_step_type(self, env):
        env.reset()
        observation, reward, done, info = env.step("type hello")
        assert isinstance(observation, str)
        assert isinstance(reward, float)
        assert isinstance(done, bool)
        assert isinstance(info, dict)
        assert "action_success" in info 