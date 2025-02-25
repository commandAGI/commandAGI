# Gym Framework

CommandLAB includes a reinforcement learning framework inspired by OpenAI Gym, designed specifically for training agents to use computers.

![Gym Architecture](../assets/images/gym_architecture.png)

## Core Concepts

The gym framework is built around several key concepts:

### Environments

An **Environment** represents a task that an agent can interact with. In CommandLAB, environments typically wrap a computer:

```python
from commandLAB.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig

# Configure the environment
config = ComputerEnvConfig(
    computer_cls_name="LocalPynputComputer",
    on_reset_python="echo 'Environment reset'"
)

# Create the environment
env = ComputerEnv(config)
```

### Agents

An **Agent** is an entity that interacts with an environment by taking actions based on observations:

```python
from commandLAB.gym.agents.naive_vision_language_computer_agent import NaiveComputerAgent

# Create an agent
agent = NaiveComputerAgent(chat_model_options={
    "model": "gpt-4-vision-preview"
})
```

### Episodes and Steps

An **Episode** is a sequence of interactions between an agent and an environment:

```python
from commandLAB.gym.schema import Episode, Step

# A step contains an observation, action, reward, and info
step = Step(
    observation=observation,
    action=action,
    reward=1.0,
    info={"success": True}
)

# An episode is a collection of steps
episode = Episode()
episode.push(step)
```

### Drivers

A **Driver** manages the interaction between agents and environments:

```python
from commandLAB.gym.drivers import SimpleDriver

# Create a driver
driver = SimpleDriver(env=env, agent=agent)

# Collect an episode
episode = driver.collect_episode()
```

## The Reinforcement Learning Loop

The gym framework implements the standard reinforcement learning loop:

1. The environment provides an observation
1. The agent selects an action based on the observation
1. The environment executes the action and returns a new observation, reward, and done flag
1. The process repeats until the episode is complete

```python
# Reset the environment
observation = env.reset()

# Agent-environment loop
done = False
while not done:
    # Agent selects action
    action = agent.act(observation)
    
    # Environment executes action
    observation, reward, done, info = env.step(action)
    
    # Agent updates based on reward
    agent.update(reward)
```

## Available Environments

CommandLAB includes several environment types:

### BaseEnv

The abstract base class for all environments:

```python
class BaseEnv(Generic[ObsType, ActionType], ABC):
    def reset(self) -> ObsType:
        """Reset the environment"""
        
    def step(self, action: ActionType) -> Tuple[ObsType, float, bool, Dict[str, Any]]:
        """Execute action and return (observation, reward, done, info)"""
        
    def close(self):
        """Clean up resources"""
```

### MultiModalEnv

An environment with multiple observation and action types:

```python
class MultiModalEnv(BaseEnv[ObsType, ActT]):
    def __init__(
        self,
        observation_fns: Dict[str, Callable[[], Any]],
        action_fns: Dict[str, Callable[[Any], bool]],
        observation_type: type,
    ):
        # ...
```

### ComputerEnv

An environment specifically for computer interaction:

```python
class ComputerEnv(MultiModalEnv[ComputerObservation, ComputerAction]):
    def __init__(self, config: ComputerEnvConfig, computer: BaseComputer = None):
        # ...
```

## Available Agents

CommandLAB includes several agent implementations:

### BaseComputerAgent

The abstract base class for all computer agents:

```python
class BaseComputerAgent(ABC):
    def reset(self) -> None:
        """Reset the agent's internal state"""
        
    def act(self, observation: ComputerObservation) -> ComputerAction:
        """Given an observation, determine the next action"""
        
    def update(self, reward: float) -> None:
        """Update the agent's internal state based on the reward"""
        
    def train(self, episodes: list[Episode]) -> None:
        """Train the agent on episodes"""
```

### NaiveComputerAgent

A simple agent that uses a vision-language model to control computers:

```python
class NaiveComputerAgent(BaseComputerAgent):
    def __init__(self, chat_model_options: dict):
        self.chat_model = get_chat_model(**chat_model_options)
        # ...
```

### ReactComputerAgent

An agent that uses the ReAct framework for reasoning:

```python
class ReactComputerAgent(BaseComputerAgent):
    def __init__(self, model: str, device: Optional[str] = None):
        self.agent = Agent(model, device=device)
        # ...
```

## Creating Custom Agents and Environments

You can create custom agents and environments by implementing the appropriate interfaces:

```python
# Custom agent
class MyCustomAgent(BaseComputerAgent):
    def act(self, observation: ComputerObservation) -> ComputerAction:
        # Your decision logic here
        
# Custom environment
class MyCustomEnvironment(BaseEnv[MyObsType, MyActionType]):
    def step(self, action: MyActionType) -> Tuple[MyObsType, float, bool, Dict[str, Any]]:
        # Your environment logic here
```

This flexibility allows you to create specialized agents and environments for specific tasks.
