import time
import traceback
from typing import Optional, Union, List, Type
from rich.console import Console
from commandagi_j2.utils.gym2.callbacks import Callback
from commandagi_j2.utils.gym2.collector_base import BaseEpisode
from commandagi_j2.utils.gym2.base_env import Env
from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.driver_base import BaseDriver
from commandagi_j2.utils.gym2.in_memory_collector import InMemoryEpisode

console = Console()


class BasicDriver(BaseDriver):
    """Basic implementation of the BaseDriver for running agent-environment interactions."""

    def __init__(
        self,
        env: Optional[Env],
        agent: Optional[BaseAgent],
        episode_cls: Type[BaseEpisode] = InMemoryEpisode,
        callbacks: Optional[List[Callback]] = None,
    ):
        """Initialize the basic driver.

        Args:
            env (Optional[Env]): The environment to use
            agent (Optional[BaseAgent]): The agent to use
            episode_cls (Type[BaseEpisode]): The episode class to use for data collection
            callbacks (Optional[List[Callback]]): List of callbacks to register
        """
        self.env = env
        self.agent = agent
        self.episode_cls = episode_cls
        self.current_episode: Optional[BaseEpisode] = None
        self._callbacks = callbacks or []

    def reset(self) -> None:
        """Reset the driver's state including environment, agent and episode."""
        console.print("🔄 [cyan]Resetting environment...[/]")
        self.env.reset()
        console.print("🤖 [cyan]Resetting agent...[/]")
        self.agent.reset()
        console.print("📊 [cyan]Creating new episode...[/]")
        self.current_episode = self.episode_cls()
        console.print("✅ [green]Reset complete[/]")

    def run_episode(
        self,
        max_steps: Optional[int] = None,
        episode_name: Optional[str] = None,
        return_episode: bool = False,
    ) -> Union[float, BaseEpisode]:
        """Run a single episode.

        Args:
            max_steps (Optional[int]): Maximum number of steps to run
            episode_name (Optional[str]): Episode identifier for data collection
            return_episode (bool): Whether to return the full episode data

        Returns:
            Union[float, BaseEpisode]: Either the total reward or full episode data
        """
        # Reset environment, agent, and collector
        console.print("\n🎬 [bold blue]Starting new episode...[/]")
        observation = self.env.reset()
        self.agent.reset()

        try:
            step = 0
            for cb in self.callbacks:
                cb.on_episode_start()
            
            while True:
                console.print(f"👉 [yellow]Step {step + 1}/{max_steps}[/]")

                # Agent selects action
                action = self.agent.act(observation)

                # Environment step
                observation, reward, done, info = self.env.step(action)

                # Update agent with reward
                self.agent.update(reward)

                # Collect data
                self.current_episode.append_step(observation, action, reward, info)
                console.print(f"💰 [green]Reward: {reward}[/]")

                for cb in self.callbacks:
                    cb.on_step(observation, action, reward, info, done, step + 1)

                # Optional delay
                time.sleep(2)

                step += 1

                if done:
                    console.print("🏁 [bold green]Episode complete![/]")
                    break

                if max_steps and step >= max_steps:
                    console.print("🏁⏱️ [bold green]Reached max steps![/]")
                    break

        except Exception as e:
            console.print(f"❌ [bold red]Error occurred: {e}[/]")
            console.print(f"[dim red]Stacktrace:\n{''.join(traceback.format_exc())}[/]")
            raise e
        finally:
            for cb in self.callbacks:
                cb.on_episode_end(episode_name)
            # Save episode data if episode name provided
            if episode_name is not None:
                console.print(f"💾 [blue]Saving episode {episode_name} data...[/]")
                self.current_episode.save(episode_name)
            console.print("🔒 [yellow]Closing environment...[/]")
            self.env.close()

        if return_episode:
            return self.current_episode
        else:
            total_reward = self.current_episode.total_reward
            console.print(f"📊 [bold green]Total reward: {total_reward}[/]")
            return total_reward
