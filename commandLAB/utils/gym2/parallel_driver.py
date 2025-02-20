import time
import traceback
from typing import Callable, Dict, List, Optional, Union

from commandagi_j2.utils.gym2.base_agent import BaseAgent
from commandagi_j2.utils.gym2.base_episode import BaseEpisode
from commandagi_j2.utils.gym2.callbacks import Callback
from commandagi_j2.utils.gym2.driver_base import BaseDriver
from commandagi_j2.utils.gym2.in_memory_episode import InMemoryEpisode
from commandagi_j2.utils.gym2.parallel_env import ParallelEnv
from rich.console import Console

console = Console()


class ParallelDriver(BaseDriver):
    """Driver for running parallel environments with a single agent that handles batched observations."""

    def __init__(
        self,
        agent: BaseAgent,
        parallel_env: ParallelEnv,
        episode_constructor: Optional[Callable[[], BaseEpisode]] = None,
        callbacks: Optional[List[Callback]] = None,
    ):
        """Initialize the parallel single agent driver.

        Args:
            parallel_env (ParallelEnv): The parallel environment to use
            agent (Optional[BaseAgent]): The agent that can handle batched observations
            episode_constructor (Optional[Callable[[], BaseEpisode]]): Function to create new episodes
            callbacks (Optional[List[Callback]]): List of callbacks to register
        """
        self.agent = agent
        self.env = parallel_env
        self.episode_constructor = episode_constructor or InMemoryEpisode
        self.current_episodes: Dict[str, BaseEpisode] = {}

    def reset(self) -> None:
        """Reset the driver's state including environments, agent and episodes."""
        console.print("🔄 [cyan]Resetting parallel environments...[/]")
        self.env.reset()
        console.print("🤖 [cyan]Resetting agent...[/]")
        self.agent.reset()
        console.print("📊 [cyan]Creating new episodes...[/]")
        self.current_episodes = {
            env_id: self.episode_constructor() for env_id in self.env.envs.keys()
        }
        console.print("✅ [green]Reset complete[/]")

    def run_episode(
        self,
        max_steps: Optional[int] = None,
        episode_name: Optional[str] = None,
        return_episode: bool = False,
    ) -> Union[float, Dict[str, BaseEpisode]]:
        """Run parallel episodes.

        Args:
            max_steps (Optional[int]): Maximum number of steps to run
            episode_name (Optional[str]): Base episode identifier for data collection
            return_episode (bool): Whether to return the full episode data

        Returns:
            Union[float, Dict[str, BaseEpisode]]: Either the total reward (averaged) or dictionary of episode data
        """
        console.print("\n🎬 [bold blue]Starting new parallel episodes...[/]")
        observations = self.env.reset()
        self.agent.reset()

        try:
            step = 0
            for cb in self.callbacks:
                cb.on_episode_start()

            while True:
                console.print(
                    f"👉 [yellow]Step {step + 1}/{max_steps if max_steps is not None else '?'}[/]"
                )

                # Agent selects actions for all active environments
                actions = self.agent.act(observations)

                # Environment steps
                observations, rewards, dones, infos = self.env.step(actions)

                # Update agent with rewards
                self.agent.update(rewards)

                # Collect data for each active environment
                for env_id in self.env.active_envs:
                    self.current_episodes[env_id].append_step(
                        observations[env_id],
                        actions[env_id],
                        rewards[env_id],
                        infos[env_id],
                    )
                    console.print(
                        f"💰 [green]Env {env_id} Reward: {rewards[env_id]}[/]"
                    )

                for cb in self.callbacks:
                    cb.on_step(observations, actions, rewards, infos, dones, step + 1)

                time.sleep(0.1)
                step += 1

                if not self.env.active_envs or (max_steps and step >= max_steps):
                    console.print("🏁 [bold green]Episodes complete![/]")
                    break

        except Exception as e:
            console.print(f"❌ [bold red]Error occurred: {e}[/]")
            console.print(f"[dim red]Stacktrace:\n{''.join(traceback.format_exc())}[/]")
            raise e
        finally:
            for cb in self.callbacks:
                cb.on_episode_end(episode_name)

            if episode_name is not None:
                for env_id, episode in self.current_episodes.items():
                    episode_id = f"{episode_name}_env{env_id}"
                    console.print(f"💾 [blue]Saving episode {episode_id} data...[/]")
                    episode.save(episode_id)

            console.print("🔒 [yellow]Closing environments...[/]")
            self.env.close()

        if return_episode:
            return self.current_episodes
        else:
            total_rewards = [
                episode.total_reward for episode in self.current_episodes.values()
            ]
            avg_reward = sum(total_rewards) / len(total_rewards)
            console.print(f"📊 [bold green]Average total reward: {avg_reward}[/]")
            return avg_reward
