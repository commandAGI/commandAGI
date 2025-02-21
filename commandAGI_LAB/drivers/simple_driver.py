import time
from typing import Optional

from commandAGI_LAB.agents.base_agent import BaseAgent
from commandAGI_LAB.computers.base_computer import BaseComputer
from commandAGI_LAB.drivers.base_driver import BaseDriver


class SimpleDriver(BaseDriver):

    max_steps: Optional[int] = None
    max_duration: Optional[float] = None

    def run(self, computer: BaseComputer, agent: BaseAgent):
        observation = computer.reset()
        done = False
        steps = 0
        start_time = time.time()
        while not done:
            action = agent.act(observation)
            observation, reward, done, info = computer.step(action)
            steps += 1
            if self.max_steps is not None and steps >= self.max_steps:
                done = True
            if self.max_duration is not None and time.time() - start_time >= self.max_duration:
                done = True
        return steps, info
