import os

# Access environment variables
openai.api_key = os.environ.get("OPENAI_API_KEY")
assistant_id = os.environ.get("ASSISTANT_ID")
vector_store_id = os.environ.get("VECTOR_STORE_ID")
thread_id = os.environ.get("Thread_ID")

print(f"API Key: {openai.api_key}")
print(f"Assistant ID: {assistant_id}")
print(f"Vector Store ID: {vector_store_id}")
print(f"Thread ID: {thread_id}")
