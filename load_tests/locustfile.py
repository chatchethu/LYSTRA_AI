from locust import HttpUser, task, between

class NovaChatUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        # Register and login logic would go here
        self.token = "simulated_token"
        
    @task(3)
    def chat_interaction(self):
        # Measure basic stateless endpoint
        self.client.get("/health")
        
        # Measure stateful chat
        payload = {
            "message": "What is the capital of France?",
            "stream": True
        }
        # In a real environment, we would use self.client.post("/api/v1/messages/...", json=payload)
        # And track SSE token latency

    @task(1)
    def document_upload(self):
        # Measure file processing queues
        pass

