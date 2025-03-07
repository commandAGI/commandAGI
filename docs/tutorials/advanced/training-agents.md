# Training Agents Tutorial

This tutorial will guide you through the process of training AI agents to use computers with commandAGI's gym framework. You'll learn how to set up environments, create agents, and train them to perform tasks.

## Introduction

commandAGI's gym framework is inspired by OpenAI Gym and provides a standardized interface for training agents to use computers. This allows you to:

- Train agents to automate UI interactions
- Evaluate agent performance on specific tasks
- Compare different agent implementations
- Create benchmarks for computer-using AI

## Prerequisites

Before you begin, make sure you have:

- commandAGI installed with gym and local computer support:

  ```bash
  pip install "commandagi[local,gym]"
  ```

- For vision-language models, you'll need an API key for OpenAI, Anthropic, or another supported provider

## Step 1: Understanding the Gym Framework

The commandAGI gym framework consists of several key components:

- **Environments**: Define the task and interface with computers
- **Agents**: Make decisions based on observations
- **Drivers**: Manage the interaction between agents and environments
- **Episodes**: Sequences of interactions between agents and environments
- **Trainers**: Train agents using episodes

The basic flow is:

1. The environment provides an observation (e.g., a screenshot)
2. The agent selects an action based on the observation
3. The environment executes the action and returns a new observation, reward, and done flag
4. The process repeats until the episode is complete

## Step 2: Setting Up an Environment

Let's start by setting up a simple environment using a local computer:

```python
from commandAGI.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig

# Configure the environment
config = ComputerEnvConfig(
    computer_cls_name="LocalPynputComputer",  # Use local computer with pynput
    on_reset_python="echo 'Environment reset'"  # Command to run on reset
)

# Create the environment
env = ComputerEnv(config)

# Reset the environment to get the initial observation
observation = env.reset()
```

## Step 3: Creating a Simple Agent

Now, let's create a simple agent that uses a vision-language model to make decisions:

```python
from commandAGI.gym.agents.naive_vision_language_computer_agent import NaiveComputerAgent

# Create an agent with OpenAI's GPT-4 Vision
agent = NaiveComputerAgent(chat_model_options={
    "model_provider": "openai",
    "model": "gpt-4-vision-preview",
    "api_key": "your-openai-api-key"  # Replace with your actual API key
})
```

## Step 4: Running an Episode

Let's use a driver to run an episode with our agent and environment:

```python
from commandAGI.gym.drivers import SimpleDriver

# Create a driver
driver = SimpleDriver(env=env, agent=agent)

# Collect an episode
episode = driver.collect_episode()

# Print episode statistics
print(f"Episode length: {episode.num_steps}")
print(f"Total reward: {sum(step.reward for step in episode)}")
```

## Step 5: Analyzing the Episode

Let's analyze what happened during the episode:

```python
# Iterate through the steps in the episode
for i, step in enumerate(episode):
    print(f"Step {i+1}:")
    print(f"  Action: {step.action}")
    print(f"  Reward: {step.reward}")
    print(f"  Info: {step.info}")
```

## Step 6: Training an Agent

Now, let's train an agent using multiple episodes:

```python
from commandAGI.gym.trainer import OnlineTrainer

# Create a trainer
trainer = OnlineTrainer(driver=driver, agent=agent)

# Train the agent for 10 episodes
episodes = trainer.train(num_episodes=10)

# Print training statistics
print(trainer.get_training_stats())
```

## Step 7: Saving and Loading Agents

You can save and load trained agents:

```python
import pickle

# Save the agent
with open("trained_agent.pkl", "wb") as f:
    pickle.dump(agent, f)

# Load the agent
with open("trained_agent.pkl", "rb") as f:
    loaded_agent = pickle.load(f)
```

## Complete Example: Training an Agent to Use a Calculator

Here's a complete example that trains an agent to use the Windows calculator:

```python
import time
from commandAGI.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
from commandAGI.gym.agents.naive_vision_language_computer_agent import NaiveComputerAgent
from commandAGI.gym.drivers import SimpleDriver
from commandAGI.types import CommandAction

# Define a custom environment with a specific reward function
class CalculatorEnv(ComputerEnv):
    def __init__(self):
        super().__init__(ComputerEnvConfig(
            computer_cls_name="LocalPynputComputer",
            on_reset_python="start calc",  # Start calculator on reset
            on_stop_python="taskkill /f /im calculator.exe"  # Kill calculator on stop
        ))
        self.target_result = 42
        self.current_result = 0
        
    def get_reward(self, action):
        # Extract the current result from the calculator display
        # This is a simplified example - in a real implementation,
        # you would use OCR to extract the number from the screenshot
        screenshot = self._computer.get_screenshot()
        # ... OCR logic to extract result ...
        
        # For this example, we'll just simulate it
        if isinstance(action.command, CommandAction):
            if "=" in action.command.command:
                # Simulate calculating the result
                self.current_result = eval(action.command.command.split("=")[0])
        
        # Calculate reward based on how close we are to the target
        distance = abs(self.current_result - self.target_result)
        reward = 1.0 / (1.0 + distance)
        
        # Bonus reward for exact match
        if self.current_result == self.target_result:
            reward += 10.0
            
        return reward
    
    def get_done(self, action):
        # Episode is done if we reach the target or after 20 steps
        return self.current_result == self.target_result or self.num_steps >= 20

# Create the environment
env = CalculatorEnv()

# Create an agent
agent = NaiveComputerAgent(chat_model_options={
    "model_provider": "openai",
    "model": "gpt-4-vision-preview",
    "api_key": "your-openai-api-key"  # Replace with your actual API key
})

# Create a driver
driver = SimpleDriver(env=env, agent=agent)

# Train the agent
trainer = OnlineTrainer(driver=driver, agent=agent)
episodes = trainer.train(num_episodes=5)

# Print training statistics
print(trainer.get_training_stats())

# Test the trained agent
observation = env.reset()
done = False
total_reward = 0

while not done:
    action = agent.act(observation)
    observation, reward, done, info = env.step(action)
    total_reward += reward
    
print(f"Test episode complete. Total reward: {total_reward}")
```

## Advanced: Custom Agents

You can create custom agents by implementing the `BaseComputerAgent` interface:

```python
from commandAGI.gym.agents.base_agent import BaseComputerAgent
from commandAGI.types import ComputerObservation, ComputerAction, ClickAction

class MyCustomAgent(BaseComputerAgent):
    def reset(self):
        """Reset agent state"""
        self.total_reward = 0.0
        
    def act(self, observation: ComputerObservation) -> ComputerAction:
        """Given an observation, determine the next action"""
        # Simple agent that always clicks in the center of the screen
        screenshot = observation.screenshot
        if screenshot:
            # Get the dimensions of the screenshot
            # In a real implementation, you would parse the base64 image
            width, height = 1920, 1080  # Placeholder values
            
            # Click in the center
            return ComputerAction(
                click=ClickAction(x=width//2, y=height//2)
            )
        return None
        
    def update(self, reward: float):
        """Update agent state based on reward"""
        self.total_reward += reward
        
    def train(self, episodes: list):
        """Train the agent on episodes"""
        # Training logic here
        pass
```

## Advanced: Custom Environments

You can create custom environments by extending the `ComputerEnv` class:

```python
from commandAGI.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig
from commandAGI.types import ComputerAction

class WebBrowserEnv(ComputerEnv):
    def __init__(self, url="https://www.google.com"):
        super().__init__(ComputerEnvConfig(
            computer_cls_name="LocalPynputComputer",
            on_reset_python=f"start chrome {url}",
            on_stop_python="taskkill /f /im chrome.exe"
        ))
        self.target_text = "commandAGI"
        
    def get_reward(self, action: ComputerAction) -> float:
        """Custom reward function based on whether the target text is visible"""
        screenshot = self._computer.get_screenshot()
        # Use OCR to check if target text is visible
        # For this example, we'll just return a placeholder reward
        return 1.0
        
    def get_done(self, action: ComputerAction) -> bool:
        """Episode is done when target text is found or max steps reached"""
        return self.num_steps >= 20
```

## Advanced: Distributed Training

For large-scale training, you can use the `MultiprocessDriver`:

```python
from commandAGI.gym.drivers import MultiprocessDriver
from commandAGI.gym.trainer import BatchTrainer

# Create a multiprocess driver with 4 workers
driver = MultiprocessDriver(env=env, agent=agent, max_workers=4)

# Create a batch trainer
trainer = BatchTrainer(driver=driver, agent=agent, batch_size=10)

# Train the agent for 100 episodes
episodes = trainer.train(num_episodes=100)
```

## Troubleshooting

### Agent Not Learning

If your agent isn't learning:

1. **Check Reward Function**: Make sure your reward function provides meaningful feedback
2. **Increase Episode Length**: Allow more steps per episode
3. **Adjust Learning Rate**: If using a learning-based agent, adjust the learning rate
4. **Improve Observations**: Make sure the agent has enough information to make decisions

### Performance Issues

If you're experiencing performance issues:

1. **Reduce Screenshot Size**: Use smaller screenshots to reduce memory usage
2. **Optimize Reward Function**: Make sure your reward function is efficient
3. **Use Threaded Driver**: Use `ThreadedDriver` for better performance
4. **Limit API Calls**: If using an API-based model, limit the number of calls

## Exercises

1. **Calculator Agent**: Train an agent to perform calculations on a calculator app
2. **Web Navigation**: Train an agent to navigate a website and find specific information
3. **Text Editor**: Train an agent to open a text editor and write a specific message
4. **Custom Agent**: Implement a custom agent using a different vision-language model

## Next Steps

- Learn about [Vision-Language Models](../guides/vision_language_models.md)
- Explore [Reinforcement Learning](../guides/reinforcement_learning.md)
- Try the [Custom Agents Guide](../guides/custom_agents.md)
