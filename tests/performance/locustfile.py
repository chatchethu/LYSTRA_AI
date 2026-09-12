import time
import json
import uuid
from locust import HttpUser, task, between, events
try:
    import sseclient
except ImportError:
    pass # Assume installed in environment

class NovaLoadTest(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """Set up session or authentication here."""
        self.client.headers.update({
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        })
        self.session_id = str(uuid.uuid4())
        
        # Create a chat thread if necessary for tests
        res = self.client.post("/api/v2/chat/thread", json={"title": "Load Test Thread"})
        if res.status_code == 200:
            self.thread_id = res.json().get("id", "test-thread-id")
        else:
            self.thread_id = "test-thread-id"

    @task(3)
    def chat_completion_latency(self):
        """Test chat completion latency including tools"""
        start_time = time.time()
        payload = {
            "messages": [{"role": "user", "content": "What is the weather like in Tokyo?"}],
            "thread_id": self.thread_id,
            "tools": [{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}}
                    }
                }
            }]
        }
        
        with self.client.post("/api/v2/chat/completions", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")

    @task(1)
    def chat_sse_stream(self):
        """Test Server-Sent Events (SSE) streaming"""
        payload = {
            "messages": [{"role": "user", "content": "Write a 100 word essay about artificial intelligence."}],
            "thread_id": self.thread_id,
            "stream": True
        }
        
        start_time = time.time()
        first_token_time = None
        
        with self.client.post("/api/v2/chat/completions", json=payload, stream=True, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"SSE setup failed: {response.status_code}")
                return

            try:
                client = sseclient.SSEClient(response)
                for event in client.events():
                    if not first_token_time:
                        first_token_time = time.time() - start_time
                        events.request.fire(
                            request_type="SSE",
                            name="first_token",
                            response_time=first_token_time * 1000,
                            response_length=len(event.data),
                            exception=None,
                            context={}
                        )
                    if event.data == "[DONE]":
                        break
                
                full_time = time.time() - start_time
                events.request.fire(
                    request_type="SSE",
                    name="full_response",
                    response_time=full_time * 1000,
                    response_length=0,
                    exception=None,
                    context={}
                )
                response.success()
            except Exception as e:
                response.failure(f"SSE stream failed: {str(e)}")

    @task(2)
    def db_memory_load(self):
        """Test memory/DB retrieval latency"""
        with self.client.get(f"/api/v2/chat/thread/{self.thread_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"DB load failed: {response.status_code}")
