import random
import time

from locust import HttpUser, between, task


class ChatUser(HttpUser):
    wait_time = between(5, 20)

    @task
    def ask_question(self):
        self.client.get("/")
        time.sleep(5)
        self.client.post(
            "/chat",
            json={
                "messages": [
                    {
                        "content": random.choice(
                            [ "What is the IOM s policy on remote work and hybrid schedules?",
                                "How do I apply for parental leave, and what are the entitlements?",
                                "What are the procedures for reporting workplace harassment or discrimination?",
                                "Can you explain how performance reviews work at IOM?",
                                "How is paid time off (PTO) calculated and tracked?",
                                "How do vacation policies differ between offices in different countries?",
                                "What are the local public holidays for employees based in Valencia?",
                                "Am I eligible for relocation assistance if I move to a different country office?",
                                "What learning and development programs are available?",
                                "How does internal mobility and job rotation work in this organization?",
                                "How do I update my emergency contact information?",
                                "What documents do I need to submit when requesting a leave of absence?",
                                "What is the code of conduct, and how is it enforced?",
                                "What’s the whistleblower policy, and is it anonymous?",
                            ]
                        ),
                        "role": "user",
                    }
                ],
                "context": {
                    "overrides": {"use_advanced_flow": True, "top": 3, "retrieval_mode": "hybrid", "temperature": 0.3}
                },
            },
        )
        time.sleep(5)
        self.client.post(
            "/chat",
            json={
                "messages": [
                    {"content": "Best shoe for hiking?", "role": "user"},
                    {
                        "content": "For the best shoe for hiking, I recommend the Trailblaze Steel-Blue Hiking Shoes.",
                        "role": "assistant",
                    },
                    {"content": "any other options?", "role": "user"},
                ],
                "context": {
                    "overrides": {"use_advanced_flow": True, "top": 3, "retrieval_mode": "hybrid", "temperature": 0.3}
                },
            },
        )
