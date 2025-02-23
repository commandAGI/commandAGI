from typing import List

import openai
from commandLAB.utils.gym2.base_env import Mandate
from commandLAB.utils.gym2.base_episode import BaseEpisode


def evaluate_episode(self, episode: BaseEpisode, mandate: Mandate) -> str:
    """
    Evaluates the given episode's screenshot-action trajectory against a provided mandate.

    Each episode is considered a trajectory made up of multiple steps, where each step is a tuple:
        (observation: Observation, action: Action).

    Parameters:
        episode (Episode): The trajectory of the episode containing lists of observations, actions, rewards, and additional info.
        mandate (Mandate): A string defining the criteria that the episode should satisfy.

    Returns:
        str: A response from the evaluation in the format: 'PASS: explanation' or 'FAIL: explanation'.

    The function constructs a prompt containing the mandate and the full screenshot-action trajectory, then uses OpenAI's API
    to obtain an evaluation which is expected to be a one-word PASS or FAIL followed by a short explanation.
    """
    # Build the trajectory description as a series of steps
    trajectory_lines: List[str] = []
    for i, (obs, action) in enumerate(zip(episode.observations, episode.actions)):
        trajectory_lines.append(f"Step {i+1}:")
        trajectory_lines.append(f"Observation: {obs}")
        trajectory_lines.append(f"Action: {action}")
        trajectory_lines.append("")
    trajectory_text: str = "\n".join(trajectory_lines)

    # Construct the evaluation prompt
    prompt: str = (
        f"You are an evaluator for a computer agent. The mandate for this episode is as follows:\n{mandate}\n\n"
        f"Below is the screenshot-action trajectory for the episode:\n{trajectory_text}\n"
        "Please evaluate whether the episode meets the criteria defined in the mandate. Respond with a single word: PASS or FAIL, followed by a brief explanation."
    )

    # Call the OpenAI ChatCompletion API to evaluate the trajectory
    response = openai.ChatCompletion.create(
        model=self.openai_model_name, messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content.strip()
    self.metrics["last_evaluation"] = result
    return result
