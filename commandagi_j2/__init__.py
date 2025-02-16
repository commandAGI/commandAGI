from commandagi_j2.agents.trainer import Trainer

def main():
    trainer = Trainer()
    trainer.train(num_episodes=3)
    trainer.evaluate(num_episodes=1)

if __name__ == "__main__":
    main()
