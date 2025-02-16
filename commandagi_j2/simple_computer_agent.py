import openai

class SimpleComputerAgent:
    def __init__(self):
        self.total_reward = 0.0

    def reset(self):
        """Reset agent state"""
        self.total_reward = 0.0

    def act(self, observation: str) -> str:
        """Analyze screenshot and decide on next action"""
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Look at this screenshot and suggest a single action to take. Respond with just the action in a simple format like 'click 100,200' or 'type Hello'"
                        },
                        {
                            "type": "image_url",
                            "image_url": f"file://{observation}"
                        }
                    ]
                }
            ]
        )
        return response.choices[0].message.content.strip()

    def update(self, reward: float):
        """Update agent with reward feedback"""
        self.total_reward += reward 