from commandagi_j2.compute_env import ComputeEnv
from commandagi_j2.simple_computer_agent import SimpleComputerAgent
from commandagi_j2.utils.gym2.driver import Driver
from commandagi_j2.utils.gym2.trainer import Trainer

def main():
    trainer = Trainer()
    trainer.train(num_episodes=3)
    trainer.evaluate(num_episodes=1)

if __name__ == "__main__":
    main()
