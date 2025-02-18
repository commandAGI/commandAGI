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
from commandagi_j2.envs.lxde_vnc_kubernetes_computer_env import LXDEVNCKubernetesComputerEnv

def run_single_test(agent_class, agent_params, env_class, env_params, test_name):
    """Helper function to run a single test combination"""
    try:
        print(f"\nRunning test: {test_name}")
        print(f"Initializing {env_class.__name__} with params: {env_params}")
        env = env_class(**env_params)
        agent = agent_class(**agent_params)
        driver = BasicDriver(env=env, agent=agent)
        
        driver.reset()
        reward = driver.run_episode(max_steps=5, episode_num=None)
        print(f"{agent_class.__name__} × {env_class.__name__} → reward = {reward}")
        return True
        
    except NotImplementedError as e:
        print(f"Skipping {test_name} due to NotImplementedError: {e}")
        return False
    except Exception as e:
        print(f"Failed {test_name}: {str(e)}")
        return False
    finally:
        try:
            env.close()
        except Exception as e:
            print(f"Warning: Error during environment cleanup: {str(e)}")

def test_all_combinations():
    # Claude Sonnet Agent Tests
    claude_params = {
        "chat_model_options": {
            "model_provider": "anthropic",
            "model": "claude-3-sonnet-20240229",
            "temperature": 0.7
        }
    }
    
    # GPT-4 Turbo Agent Tests
    gpt4o_params = {
        "chat_model_options": {
            "model_provider": "openai", 
            "model": "gpt-4o",
            "temperature": 0.2
        }
    }

    # Test LocalPynputComputeEnv
    run_single_test(
        SimpleComputerAgent, claude_params,
        LocalPynputComputeEnv, {},
        "Claude + LocalPynputComputeEnv"
    )
    
    run_single_test(
        SimpleComputerAgent, gpt4o_params,
        LocalPynputComputeEnv, {},
        "GPT-4o + LocalPynputComputeEnv"
    )

    # Test LocalPyAutoGUIComputeEnv
    run_single_test(
        SimpleComputerAgent, claude_params,
        LocalPyAutoGUIComputeEnv, {},
        "Claude + LocalPyAutoGUIComputeEnv"
    )
    
    run_single_test(
        SimpleComputerAgent, gpt4o_params,
        LocalPyAutoGUIComputeEnv, {},
        "GPT-4o + LocalPyAutoGUIComputeEnv"
    )

    # Test E2BDesktopEnv (with and without video stream)
    for video_stream in [False, True]:
        run_single_test(
            SimpleComputerAgent, claude_params,
            E2BDesktopEnv, {"video_stream": video_stream},
            f"Claude + E2BDesktopEnv (video_stream={video_stream})"
        )
        
        run_single_test(
            SimpleComputerAgent, gpt4o_params,
            E2BDesktopEnv, {"video_stream": video_stream},
            f"GPT-4o + E2BDesktopEnv (video_stream={video_stream})"
        )

    # Test VNCComputerEnv
    vnc_params = {"host": "localhost", "port": 5900, "password": "secret"}
    run_single_test(
        SimpleComputerAgent, claude_params,
        VNCComputerEnv, vnc_params,
        "Claude + VNCComputerEnv"
    )
    
    run_single_test(
        SimpleComputerAgent, gpt4o_params,
        VNCComputerEnv, vnc_params,
        "GPT-4o + VNCComputerEnv"
    )

    # Test LXDEVNCDockerComputerEnv
    docker_params = {"user": "root", "password": "secret", "vnc_port": 5900}
    run_single_test(
        SimpleComputerAgent, claude_params,
        LXDEVNCDockerComputerEnv, docker_params,
        "Claude + LXDEVNCDockerComputerEnv"
    )
    
    run_single_test(
        SimpleComputerAgent, gpt4o_params,
        LXDEVNCDockerComputerEnv, docker_params,
        "GPT-4o + LXDEVNCDockerComputerEnv"
    )

    # Test KubernetesComputerEnv
    k8s_params = {
        "pod_name": "test-pod",
        "image": "test-image",
        "namespace": "default",
        "env_vars": {"TEST_VAR": "test_value"},
        "ports": {"5900": 5900}
    }
    run_single_test(
        SimpleComputerAgent, claude_params,
        KubernetesComputerEnv, k8s_params,
        "Claude + KubernetesComputerEnv"
    )
    
    run_single_test(
        SimpleComputerAgent, gpt4o_params,
        KubernetesComputerEnv, k8s_params,
        "GPT-4o + KubernetesComputerEnv"
    )

    # Test VNCKubernetesComputerEnv
    vnc_k8s_params = {
        "pod_name": "vnc-test-pod",
        "image": "vnc-test-image",
        "namespace": "default",
        "vnc_port": 5900,
        "password": "secret"
    }
    run_single_test(
        SimpleComputerAgent, claude_params,
        VNCKubernetesComputerEnv, vnc_k8s_params,
        "Claude + VNCKubernetesComputerEnv"
    )
    
    run_single_test(
        SimpleComputerAgent, gpt4o_params,
        VNCKubernetesComputerEnv, vnc_k8s_params,
        "GPT-4o + VNCKubernetesComputerEnv"
    )

    # Test LXDEVNCKubernetesComputerEnv
    lxde_k8s_params = {
        "pod_name": "lxde-test-pod",
        "namespace": "default",
        "user": "root",
        "password": "secret",
        "vnc_port": 5900
    }
    run_single_test(
        SimpleComputerAgent, claude_params,
        LXDEVNCKubernetesComputerEnv, lxde_k8s_params,
        "Claude + LXDEVNCKubernetesComputerEnv"
    )
    
    run_single_test(
        SimpleComputerAgent, gpt4o_params,
        LXDEVNCKubernetesComputerEnv, lxde_k8s_params,
        "GPT-4o + LXDEVNCKubernetesComputerEnv"
    )

if __name__ == "__main__":
    test_all_combinations() 