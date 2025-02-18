import traceback
import pytest
from rich.console import Console

from commandagi_j2.utils.gym2.basic_driver import BasicDriver
from commandagi_j2.agents.simple_computer_agent import SimpleComputerAgent
from commandagi_j2.envs.local_pynput_computer_env import LocalPynputComputeEnv
from commandagi_j2.envs.e2b_desktop_env import E2BDesktopEnv
from commandagi_j2.envs.lxde_vnc_docker_computer_env import LXDEVNCDockerComputerEnv
from commandagi_j2.envs.local_pyautogui_computer_env import LocalPyAutoGUIComputeEnv
from commandagi_j2.envs.vnc_computer_env import VNCComputerEnv
from commandagi_j2.envs.kubernetes_computer_env import KubernetesComputerEnv
from commandagi_j2.envs.vnc_kubernetes_computer_env import VNCKubernetesComputerEnv
from commandagi_j2.envs.lxde_vnc_kubernetes_computer_env import LXDEVNCKubernetesComputerEnv

import docker
import time
import subprocess

from commandagi_j2.utils.gym2.in_memory_episode import InMemoryEpisode

console = Console()

def run_single_test(agent_class, agent_params, env_class, env_params, test_name):
    """Helper function to run a single test combination"""
    try:
        console.print(f"\n🚀 [bold cyan]Running test:[/] {test_name}")
        console.print(f"⚙️  [yellow]Initializing[/] {env_class.__name__} with params: {env_params}")
        env = env_class(**env_params)
        console.print(f"✅ [green]Environment initialized[/]")
        agent = agent_class(**agent_params)
        console.print(f"✅ [green]Agent initialized[/]")
        driver = BasicDriver(env=env, agent=agent)
        console.print(f"✅ [green]Driver initialized[/]")
        driver.reset()
        console.print(f"✅ [green]Driver reset[/]")
        episode = driver.run_episode(max_steps=5, episode_name=test_name, return_episode=True)
        console.print(f"✅ [green]Episode completed[/]")
        console.print(f"✨ [green]{agent_class.__name__} × {env_class.__name__} → reward = {episode.total_reward}[/]")
        episode.save(test_name)
        return True
        
    except NotImplementedError as e:
        console.print(f"⚠️  [yellow]Skipping {test_name} due to NotImplementedError:[/] {e}")
        console.print(f"[dim]Stacktrace:\n{''.join(traceback.format_exc())}[/]")
        return False
    except Exception as e:
        console.print(f"❌ [red]Failed {test_name}:[/] {str(e)}")
        console.print(f"[dim]Stacktrace:\n{''.join(traceback.format_exc())}[/]")
        return False
    finally:
        try:
            env.close()
        except Exception as e:
            console.print(f"⚠️  [yellow]Warning: Error during environment cleanup:[/] {str(e)}")

def setup_vnc_docker_container():
    """Launch a VNC server Docker container for testing"""
    client = docker.from_env()
    container = client.containers.run(
        "consol/ubuntu-xfce-vnc",  # Popular VNC-enabled Docker image
        detach=True,
        ports={'5901/tcp': 5900},  # Map container port 5901 to host port 5900
        environment={
            "VNC_PW": "secret",    # Set VNC password
            "VNC_RESOLUTION": "1280x720"
        },
        remove=True  # Auto-remove container when stopped
    )
    # Wait for VNC server to start
    time.sleep(10)
    return container

def is_kubernetes_available():
    """Check if kubectl is available and can connect to a cluster"""
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

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

    # # Test LocalPynputComputeEnv
    # run_single_test(
    #     SimpleComputerAgent, claude_params,
    #     LocalPynputComputeEnv, {},
    #     "Claude + LocalPynputComputeEnv"
    # )
    
    # run_single_test(
    #     SimpleComputerAgent, gpt4o_params,
    #     LocalPynputComputeEnv, {},
    #     "GPT-4o + LocalPynputComputeEnv"
    # )

    # # Test LocalPyAutoGUIComputeEnv
    # run_single_test(
    #     SimpleComputerAgent, claude_params,
    #     LocalPyAutoGUIComputeEnv, {},
    #     "Claude + LocalPyAutoGUIComputeEnv"
    # )
    
    # run_single_test(
    #     SimpleComputerAgent, gpt4o_params,
    #     LocalPyAutoGUIComputeEnv, {},
    #     "GPT-4o + LocalPyAutoGUIComputeEnv"
    # )

    # # Test E2BDesktopEnv (with and without video stream)
    # for video_stream in [False, True]:
    #     run_single_test(
    #         SimpleComputerAgent, claude_params,
    #         E2BDesktopEnv, {"video_stream": video_stream},
    #         f"Claude + E2BDesktopEnv (video_stream={video_stream})"
    #     )
        
    #     run_single_test(
    #         SimpleComputerAgent, gpt4o_params,
    #         E2BDesktopEnv, {"video_stream": video_stream},
    #         f"GPT-4o + E2BDesktopEnv (video_stream={video_stream})"
    #     )

    # Test VNCComputerEnv
    console.print("\n🔄 [bold blue]Setting up VNC container...[/]")
    vnc_container = setup_vnc_docker_container()
    console.print("✅ [green]VNC container setup complete[/]")
    try:
        console.print("🏃 [cyan]Running VNCComputerEnv tests (1/2)...[/]")
        vnc_params = {"host": "localhost", "port": 5900, "password": "secret"}
        run_single_test(
            SimpleComputerAgent, claude_params,
            VNCComputerEnv, vnc_params,
            "Claude + VNCComputerEnv"
        )
        console.print("✅ [green]VNCComputerEnv tests (1/2) complete[/]")
        
        console.print("🏃 [cyan]Running VNCComputerEnv tests (2/2)...[/]")
        run_single_test(
            SimpleComputerAgent, gpt4o_params,
            VNCComputerEnv, vnc_params,
            "GPT-4o + VNCComputerEnv"
        )
        console.print("✅ [green]VNCComputerEnv tests (2/2) complete[/]")
    finally:
        console.print("🛑 [yellow]Stopping VNC container...[/]")
        vnc_container.stop()  # Cleanup container after tests
        console.print("✅ [green]VNC container stopped[/]")
    console.print("🎉 [bold blue]VNCComputerEnv tests complete[/]")

    # Test LXDEVNCDockerComputerEnv
    console.print("\n[bold blue]=== 🐳 Starting LXDEVNCDockerComputerEnv Tests ===[/]")
    docker_params = {"user": "root", "password": "secret", "vnc_port": 5900}
    console.print(f"⚙️  [yellow]Docker params configured:[/] {docker_params}")

    console.print("\n🤖 [cyan]Running Claude + LXDEVNCDockerComputerEnv test...[/]")
    console.print("🔄 [yellow]Initializing test with Claude agent...[/]")
    run_single_test(
        SimpleComputerAgent, claude_params,
        LXDEVNCDockerComputerEnv, docker_params,
        "Claude + LXDEVNCDockerComputerEnv"
    )
    console.print("✅ [green]Claude + LXDEVNCDockerComputerEnv test completed[/]")
    
    console.print("\n🤖 [cyan]Running GPT-4o + LXDEVNCDockerComputerEnv test...[/]")
    console.print("🔄 [yellow]Initializing test with GPT-4o agent...[/]")
    run_single_test(
        SimpleComputerAgent, gpt4o_params,
        LXDEVNCDockerComputerEnv, docker_params,
        "GPT-4o + LXDEVNCDockerComputerEnv"
    )
    console.print("✅ [green]GPT-4o + LXDEVNCDockerComputerEnv test completed[/]")
    
    console.print("\n🤖 [cyan]Running GPT-4o + LXDEVNCDockerComputerEnv test FOR THE SECOND TIME!!![/]")
    console.print("🔄 [yellow]Initializing test with GPT-4o agent...[/]")
    run_single_test(
        SimpleComputerAgent, gpt4o_params,
        LXDEVNCDockerComputerEnv, docker_params,
        "GPT-4o + LXDEVNCDockerComputerEnv (second time)"
    )
    console.print("✅ [green]GPT-4o + LXDEVNCDockerComputerEnv test completed[/]")
    console.print("[bold blue]=== 🎉 LXDEVNCDockerComputerEnv Tests Completed ===[/]\n")

    # # Test Kubernetes-based environments only if Kubernetes is available
    # console.print("\n[bold blue]=== ⚡ Checking Kubernetes Availability ===[/]")
    # if is_kubernetes_available():
    #     console.print("✅ [green]Kubernetes cluster detected - proceeding with K8s tests[/]")
        
    #     # Test LXDEVNCKubernetesComputerEnv
    #     console.print("\n[bold blue]=== 🚀 Starting LXDEVNCKubernetesComputerEnv Tests ===[/]")
    #     lxde_k8s_params = {
    #         "pod_name": "lxde-test-pod",
    #         "namespace": "default",
    #         "user": "root",
    #         "password": "secret",
    #         "vnc_port": 5900
    #     }
    #     console.print(f"⚙️  [yellow]Kubernetes params configured:[/] {lxde_k8s_params}")

    #     console.print("\n🤖 [cyan]Running Claude + LXDEVNCKubernetesComputerEnv test...[/]")
    #     console.print("🔄 [yellow]Initializing test with Claude agent...[/]")
    #     run_single_test(
    #         SimpleComputerAgent, claude_params,
    #         LXDEVNCKubernetesComputerEnv, lxde_k8s_params,
    #         "Claude + LXDEVNCKubernetesComputerEnv"
    #     )
    #     console.print("✅ [green]Claude + LXDEVNCKubernetesComputerEnv test completed[/]")
        
    #     console.print("\n🤖 [cyan]Running GPT-4o + LXDEVNCKubernetesComputerEnv test...[/]")
    #     console.print("🔄 [yellow]Initializing test with GPT-4o agent...[/]")
    #     run_single_test(
    #         SimpleComputerAgent, gpt4o_params,
    #         LXDEVNCKubernetesComputerEnv, lxde_k8s_params,
    #         "GPT-4o + LXDEVNCKubernetesComputerEnv"
    #     )
    #     console.print("✅ [green]GPT-4o + LXDEVNCKubernetesComputerEnv test completed[/]")
    #     console.print("[bold blue]=== 🎉 LXDEVNCKubernetesComputerEnv Tests Completed ===[/]\n")
    # else:
    #     console.print("❌ [red]No Kubernetes cluster detected[/]")
    #     console.print("⚠️  [yellow]Skipping Kubernetes tests - no Kubernetes cluster available[/]")

if __name__ == "__main__":
    test_all_combinations() 
    print("Done")