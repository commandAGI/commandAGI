import time
import traceback
from typing import Optional, Union
from rich.console import Console
from commandagi_j2.utils.gym2.collector_base import BaseCollector, BaseEpisode
from commandagi_j2.utils.gym2.base_env import Env
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.driver_base import BaseDriver
from commandagi_j2.utils.gym2.in_memory_collector import (
    InMemoryDataCollector,
)

console = Console()

class BasicDriver(BaseDriver):
    """Basic implementation of the BaseDriver for running agent-environment interactions."""

    def __init__(
        self,
        env: Optional[Env],
        agent: Optional[BaseAgent],
        collector: Optional[BaseCollector] = None,
    ):
        """Initialize the basic driver.

        Args:
            env (Optional[Env]): The environment to use
            agent (Optional[BaseAgent]): The agent to use
            collector (Optional[BaseCollector]): The data collector to use, defaults to InMemoryDataCollector
        """
        self.env = env
        self.agent = agent
        self.collector = collector or InMemoryDataCollector()

    def reset(self) -> None:
        """Reset the driver's state including environment, agent and collector."""
        console.print("🔄 [cyan]Resetting environment...[/]")
        self.env.reset()
        console.print("🤖 [cyan]Resetting agent...[/]")
        self.agent.reset()
        console.print("📊 [cyan]Resetting collector...[/]")
        self.collector.reset()
        console.print("✅ [green]Reset complete[/]")

    def run_episode(
        self,
        max_steps: Optional[int] = None,
        episode_num: Optional[int] = None,
        return_episode: bool = False,
    ) -> Union[float, BaseEpisode]:
        """Run a single episode.

        Args:
            max_steps (Optional[int]): Maximum number of steps to run
            episode_num (Optional[int]): Episode identifier for data collection
            return_episode (bool): Whether to return the full episode data

        Returns:
            Union[float, BaseEpisode]: Either the total reward or full episode data
        """
        # Reset environment, agent, and collector
        console.print("\n🎬 [bold blue]Starting new episode...[/]")
        observation = self.env.reset()
        self.agent.reset()
        self.collector.reset()

        try:
            step = 0
            while True:
                console.print(f"👉 [yellow]Step {step + 1}/{max_steps}[/]")
                
                # Agent selects action
                action = self.agent.act(observation)

                # Environment step
                observation, reward, done, info = self.env.step(action)

                # Update agent with reward
                self.agent.update(reward)

                # Collect data
                self.collector.add_step(observation, action, reward, info)
                console.print(f"💰 [green]Reward: {reward}[/]")

                # Optional delay
                time.sleep(2)

                step += 1

                if done:
                    console.print("🏁 [bold green]Episode complete![/]")
                    break

                if  max_steps and step >= max_steps:
                    console.print("🏁⏱️ [bold green]Reached max steps![/]")
                    break

        except Exception as e:
            console.print(f"❌ [bold red]Error occurred: {e}[/]")
            console.print(f"[dim red]Stacktrace:\n{''.join(traceback.format_exc())}[/]")
            raise e
        finally:
            # Save episode data if episode number provided
            if episode_num is not None:
                console.print(f"💾 [blue]Saving episode {episode_num} data...[/]")
                self.collector.save_episode(episode_num)
            console.print("🔒 [yellow]Closing environment...[/]")
            self.env.close()

        if return_episode:
            return self.collector.current_episode
        else:
            total_reward = self.collector.current_episode.total_reward
            console.print(f"📊 [bold green]Total reward: {total_reward}[/]")
            return total_reward
