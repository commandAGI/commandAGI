#!/usr/bin/env python3
"""
CLI for testing, evaluating, and re-watching evaluation episodes 
with various agent/environment combinations.

Subcommands:
  test     Run one or more test episodes with a chosen agent and environment.
  evaluate Run evaluation episodes using an evaluator (e.g. InstructionFollowingEvaluator).
  replay   Replay a saved episode by cycling through its observation screenshots.
"""

import argparse
import json
import os
import time

# Import agents & environments
from commandagi_j2.agents.simple_computer_agent import SimpleComputerAgent
from commandagi_j2.envs.docker_lxde_env import DockerLxdeEnv
from commandagi_j2.envs.e2b_desktop_env import E2BDesktopEnv
from commandagi_j2.envs.local_compute_env import LocalComputeEnv

# Import driver, trainer and evaluator
from commandagi_j2.utils.basic_driver import BasicDriver
from commandagi_j2.agents.trainer import Trainer
from commandagi_j2.evals.instruction_following_evaluator import InstructionFollowingEvaluator

# Mapping from string names to classes so that we can dynamically select them.
AGENTS = {
    "simple": SimpleComputerAgent,
    # add more agents if you implement them
}

ENVS = {
    "docker": DockerLxdeEnv,
    "e2b": E2BDesktopEnv,
    "local": LocalComputeEnv,
    # add other envs as needed
}


def run_test(args):
    """
    Run one or more test episodes with the specified agent and environment.
    """
    agent_cls = AGENTS.get(args.agent.lower())
    env_cls = ENVS.get(args.env.lower())
    if agent_cls is None:
        print(f"Unknown agent: {args.agent}")
        return
    if env_cls is None:
        print(f"Unknown environment: {args.env}")
        return

    total_reward = 0.0
    for ep in range(args.num_episodes):
        print(f"\n=== Starting Test Episode {ep + 1} ===")
        # For each episode, create a new instance of the env and agent (since the environment is closed after each episode)
        env = env_cls()
        agent = agent_cls()
        driver = BasicDriver(env, agent)
        driver.reset()
        reward = driver.run_episode(max_steps=args.max_steps, episode_num=ep)
        print(f"Episode {ep + 1} finished with reward: {reward}")
        total_reward += reward
        # Allow a short break between episodes if desired
        time.sleep(1)
    avg_reward = total_reward / args.num_episodes
    print(f"\nAverage reward over {args.num_episodes} test episodes: {avg_reward}")


def run_evaluate(args):
    """
    Run evaluation episodes using the specified agent, environment, and evaluator.
    """
    agent_cls = AGENTS.get(args.agent.lower())
    env_cls = ENVS.get(args.env.lower())
    if agent_cls is None:
        print(f"Unknown agent: {args.agent}")
        return
    if env_cls is None:
        print(f"Unknown environment: {args.env}")
        return

    evaluator = InstructionFollowingEvaluator(openai_model_name=args.model)
    evaluations = []
    rewards = []

    # Here we run episodes one by one and evaluate them using the evaluator.
    # Each episode is gathered by a new driver instance.
    for ep in range(args.num_episodes):
        print(f"\n=== Starting Evaluation Episode {ep + 1} ===")
        env = env_cls()
        agent = agent_cls()
        driver = BasicDriver(env, agent)
        driver.reset()
        # Get the full episode data (including observations, actions, etc.)
        episode_data = driver.run_episode(max_steps=args.max_steps, episode_num=f"eval_{ep}", return_episode=True)
        rewards.append(episode_data.total_reward)
        # Provide a mandate. You can update this string or pass it via the CLI.
        mandate = args.mandate or "Follow the instructions exactly."
        eval_result = evaluator.evaluate_episode(episode_data, mandate)
        print(f"Evaluation result for episode {ep + 1}: {eval_result}")
        evaluations.append(eval_result)

        # Short pause between episodes
        time.sleep(1)

    avg_reward = sum(rewards) / len(rewards) if rewards else 0.0
    print("\n=== Evaluation Summary ===")
    print(f"Episode rewards: {rewards}")
    print(f"Average reward: {avg_reward}")
    print(f"Evaluation results: {evaluations}")
    print(f"Evaluator metrics: {evaluator.get_metrics()}")


def run_replay(args):
    """
    Replay a saved episode by reading its JSON file (saved with the DataCollector)
    and cycling through the observation images.
    """
    # Determine the episode file path. If the provided episode argument is numeric,
    # assume it is an episode number from the default collected_data directory.
    if args.episode.isdigit():
        episode_file = os.path.join("collected_data", f"episode_{args.episode}.json")
    else:
        episode_file = args.episode

    if not os.path.exists(episode_file):
        print(f"Episode file not found: {episode_file}")
        return

    with open(episode_file, "r") as f:
        episode_data = json.load(f)

    observations = episode_data.get("observations", [])
    if not observations:
        print("No observations found in the episode data.")
        return

    try:
        # Import tkinter and PIL for replay rendering
        import tkinter as tk
        from PIL import Image, ImageTk
    except ImportError as e:
        print("tkinter and Pillow (PIL) are required for replaying episodes.")
        return

    # Create a simple Tkinter window to display the images
    root = tk.Tk()
    root.title(f"Replaying episode from {os.path.basename(episode_file)}")

    label = tk.Label(root)
    label.pack(fill="both", expand=True)

    def update_image(index):
        if index >= len(observations):
            # End the replay after the last observation
            root.destroy()
            return

        image_path = observations[index]
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            root.destroy()
            return

        try:
            img = Image.open(image_path)
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            root.destroy()
            return

        # Optionally, you can resize the image to fit the window
        width = root.winfo_width() or 800
        height = root.winfo_height() or 600
        img = img.resize((width, height), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(img)
        label.config(image=photo)
        label.image = photo  # keep a reference so it's not GC'ed
        # schedule the next image update after the specified interval (converted to milliseconds)
        root.after(args.interval * 1000, update_image, index + 1)

    # Start replay from the first image
    update_image(0)
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="CLI for testing, evaluating, and replaying eval episodes.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand to run")

    # Subparser for the test mode
    parser_test = subparsers.add_parser("test", help="Test a single episode with a chosen agent and environment")
    parser_test.add_argument("--agent", type=str, default="simple", help="Agent to use (e.g. simple)")
    parser_test.add_argument("--env", type=str, default="local", help="Environment to use (e.g. local, docker, e2b)")
    parser_test.add_argument("--num_episodes", type=int, default=1, help="Number of test episodes to run")
    parser_test.add_argument("--max_steps", type=int, default=100, help="Maximum steps per episode")
    parser_test.set_defaults(func=run_test)

    # Subparser for the evaluation mode
    parser_eval = subparsers.add_parser("evaluate", help="Run evaluation episodes with an evaluator")
    parser_eval.add_argument("--agent", type=str, default="simple", help="Agent to use")
    parser_eval.add_argument("--env", type=str, default="local", help="Environment to use")
    parser_eval.add_argument("--num_episodes", type=int, default=1, help="Number of evaluation episodes")
    parser_eval.add_argument("--max_steps", type=int, default=100, help="Maximum steps per episode")
    parser_eval.add_argument("--model", type=str, default="o1", help="OpenAI model name to use in evaluator")
    parser_eval.add_argument("--mandate", type=str, default="", help="Mandate string for evaluator (if not provided, a default is used)")
    parser_eval.set_defaults(func=run_evaluate)

    # Subparser for the replay mode
    parser_replay = subparsers.add_parser("replay", help="Replay a saved evaluation episode")
    parser_replay.add_argument("--episode", type=str, required=True,
                               help="Episode file name (or episode number) from collected_data (e.g. 0 for collected_data/episode_0.json)")
    parser_replay.add_argument("--interval", type=int, default=1, help="Time in seconds between observations")
    parser_replay.set_defaults(func=run_replay)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main() 