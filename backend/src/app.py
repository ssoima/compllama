import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from llama_stack_client import LlamaStackClient
from pydantic import BaseModel
import time
from restack_ai import Restack
import uvicorn
from llama_stack_client.lib.inference.event_logger import EventLogger


# Define request model
class QueryRequest(BaseModel):
    query: str
    count: int

app = FastAPI()
client = LlamaStackClient(base_url="http://localhost:5050")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return "Welcome to the TogetherAI LlamaIndex FastAPI App!"


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message

    # Use the provided LlamaStack client code snippet
    response = client.inference.chat_completion(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_message}
        ],
        model="Llama3.2-90B-Vision-Instruct",
        stream=True
    )
    # Define an async generator to stream each log message
    async def event_generator():
        async for log in EventLogger().log(response):
            if hasattr(log, "content"):
                yield json.dumps({"content": log.content}) + "\n"

    # Return the StreamingResponse using the async generator
    return StreamingResponse(event_generator(), media_type="application/json")


@app.post("/api/schedule")
async def schedule_workflow(request: QueryRequest):
    try:
        response = client.inference.chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Write a two-sentence poem about llama."}
            ],
            model="Llama3.2-90B-Vision-Instruct",
        )

        return {
            "result": response.completion_message.content
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Remove Flask-specific run code since FastAPI uses uvicorn
def run_app():
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == '__main__':
    run_app()
