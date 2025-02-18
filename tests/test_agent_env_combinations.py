import pytest

from commandagi_j2.utils.gym2.basic_driver import BasicDriver
from commandagi_j2.agents.simple_computer_agent import SimpleComputerAgent

# Import environment classes
from commandagi_j2.envs.local_pynput_computer_env import LocalPynputComputeEnv
from commandagi_j2.envs.e2b_desktop_env import E2BDesktopEnv
from commandagi_j2.envs.lxde_vnc_docker_computer_env import LXDEVNCDockerComputerEnv
from commandagi_j2.envs.local_pyautogui_computer_env import LocalPyAutoGUIComputeEnv
from commandagi_j2.envs.vnc_computer_env import VNCComputerEnv
from commandagi_j2.envs.kubernetes_computer_env import KubernetesComputerEnv
from commandagi_j2.envs.vnc_kubernetes_computer_env import VNCKubernetesComputerEnv
from commandagi_j2.envs.lxde_vnc_kubernetes_computer_env import (
    LXDEVNCKubernetesComputerEnv,
)

# Define agent configurations for testing
AGENT_CONFIGS = [
    (SimpleComputerAgent, {
        "chat_model_options": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.7
        }
    }),
    (SimpleComputerAgent, {
        "chat_model_options": {
            "model": "gpt-4",
            "temperature": 0.2
        }
    }),
    # Add other agent configurations here when available
]

# Define environment configurations for testing
ENV_CONFIGS = [
    # Local environments (no special setup required)
    (LocalPynputComputeEnv, {}),
    (LocalPyAutoGUIComputeEnv, {}),
    # E2B environment (requires e2b-desktop)
    (E2BDesktopEnv, {"video_stream": False}),
    (E2BDesktopEnv, {"video_stream": True}),
    # VNC environments
    (VNCComputerEnv, {"host": "localhost", "port": 5900, "password": "secret"}),
    # Docker-based environments
    (
        LXDEVNCDockerComputerEnv,
        {"user": "root", "password": "secret", "vnc_port": 5900},
    ),
    # Kubernetes-based environments
    (
        KubernetesComputerEnv,
        {
            "pod_name": "test-pod",
            "image": "test-image",
            "namespace": "default",
            "env_vars": {"TEST_VAR": "test_value"},
            "ports": {"5900": 5900},
        },
    ),
    (
        VNCKubernetesComputerEnv,
        {
            "pod_name": "vnc-test-pod",
            "image": "vnc-test-image",
            "namespace": "default",
            "vnc_port": 5900,
            "password": "secret",
        },
    ),
    (
        LXDEVNCKubernetesComputerEnv,
        {
            "pod_name": "lxde-test-pod",
            "namespace": "default",
            "user": "root",
            "password": "secret",
            "vnc_port": 5900,
        },
    ),
]


@pytest.mark.parametrize("AgentClass,agent_params", AGENT_CONFIGS)
@pytest.mark.parametrize("EnvClass,env_params", ENV_CONFIGS)
def test_agent_env_combination(AgentClass, agent_params, EnvClass, env_params):
    """
    Test each Agent × Env combination with specific parameters for both.

    Args:
        AgentClass: The agent class to test
        agent_params: Dictionary of parameters for agent initialization
        EnvClass: The environment class to test
        env_params: Dictionary of parameters for environment initialization
    """
    try:
        print(f"Initializing {EnvClass.__name__} with params: {env_params}")
        env = EnvClass(**env_params)
        print(f"Environment initialized: {env}")
    except Exception as e:
        pytest.skip(
            f"Skipping {EnvClass.__name__} because it could not be instantiated: {e}"
        )

    agent = AgentClass(**agent_params)
    driver = BasicDriver(env=env, agent=agent)

    try:
        driver.reset()
        reward = driver.run_episode(max_steps=5, episode_num=None)
        print(f"{AgentClass.__name__} × {EnvClass.__name__} → reward = {reward}")
    except NotImplementedError as e:
        pytest.skip(f"Skipping {EnvClass.__name__} due to NotImplementedError: {e}")
    except Exception as e:
        pytest.fail(
            f"{AgentClass.__name__} × {EnvClass.__name__} raised an unexpected exception: {e}"
        )
    finally:
        try:
            env.close()
        except Exception as e:
            print(f"Warning: Error during environment cleanup: {str(e)}")


# Optional: Add specific test cases for environment-specific features
# @pytest.mark.parametrize("vnc_port", [5900, 5901])
# def test_vnc_docker_different_ports(vnc_port):
#     """Test VNC Docker environment with different port configurations"""
#     env_params = {
#         "dockerfile_path": "dockerfiles/base.Dockerfile",
#         "user": "root",
#         "password": "secret",
#         "vnc_port": vnc_port,
#     }
#     try:
#         env = VNCDockerComputerEnv(**env_params)
#         env.reset()
#         assert env.vnc_port == vnc_port
#     except Exception as e:
#         pytest.skip(f"VNC Docker test failed: {e}")
#     finally:
#         if "env" in locals():
#             env.close()
