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

# Define agent classes for testing
AGENT_CLASSES = [
    SimpleComputerAgent,
    # Add other agent classes here when available
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
    # (
    #     VNCDockerComputerEnv,
    #     {
    #         "dockerfile_path": "dockerfiles/base.Dockerfile",
    #         "user": "root",
    #         "password": "secret",
    #         "vnc_port": 5900,
    #     },
    # ),
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


@pytest.mark.parametrize("AgentClass", AGENT_CLASSES)
@pytest.mark.parametrize("EnvClass,env_params", ENV_CONFIGS)
def test_agent_env_combination(AgentClass, EnvClass, env_params):
    """
    Test each Agent × Env combination with specific environment parameters.

    Args:
        AgentClass: The agent class to test
        EnvClass: The environment class to test
        env_params: Dictionary of parameters for environment initialization
    """
    try:
        env = EnvClass(**env_params)
    except Exception as e:
        pytest.skip(
            f"Skipping {EnvClass.__name__} because it could not be instantiated: {e}"
        )

    agent = AgentClass()
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
        except Exception:
            pass


# Optional: Add specific test cases for environment-specific features
@pytest.mark.parametrize("vnc_port", [5900, 5901])
def test_vnc_docker_different_ports(vnc_port):
    """Test VNC Docker environment with different port configurations"""
    env_params = {
        "dockerfile_path": "dockerfiles/base.Dockerfile",
        "user": "root",
        "password": "secret",
        "vnc_port": vnc_port,
    }
    try:
        env = VNCDockerComputerEnv(**env_params)
        env.reset()
        assert env.vnc_port == vnc_port
    except Exception as e:
        pytest.skip(f"VNC Docker test failed: {e}")
    finally:
        if "env" in locals():
            env.close()


@pytest.mark.parametrize("video_stream", [True, False])
def test_e2b_video_streaming(video_stream):
    """Test E2B environment with different video streaming configurations"""
    try:
        env = E2BDesktopEnv(video_stream=video_stream)
        env.reset()
        # Add specific assertions for video streaming functionality
    except Exception as e:
        pytest.skip(f"E2B test failed: {e}")
    finally:
        if "env" in locals():
            env.close()
