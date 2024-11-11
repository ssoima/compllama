import json
import asyncio
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from llama_stack_client import LlamaStackClient
from pydantic import BaseModel
import time
from restack_ai import Restack
import uvicorn
from llama_stack_client.lib.inference.event_logger import EventLogger
from .data_ingestion import init_database  
from llama_stack_client import LlamaStackClient
from .ordinance_db import OrdinanceDBWithTogether
from .rag import OrdinanceRAG
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define request model
class QueryRequest(BaseModel):
    query: str
    count: int

app = FastAPI()
client = LlamaStackClient(base_url="http://localhost:5050")
db = init_database(
        collection_name="combined_ordinances"
)

# Initialize RAG system
rag = OrdinanceRAG(
    ordinance_db=db,
    llama_client=client
)

class OrdinanceQuery(BaseModel):
    query: str
    state: Optional[str] = None
    city: Optional[str] = None
    filter_conditions: Optional[dict] = None
    stream: Optional[bool] = False


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
    # TODO: Do request to RAG

    # Use the provided LlamaStack client code snippet
    response = client.inference.chat_completion(
        messages=[
            {"role": "system", "content": "You are a helpful lady. Answer the asked question as faithfully as possible."},
            {"role": "user", "content": user_message}
        ],
        model="Llama3.1-405B-Instruct",
        stream=True
    )
    # Define an async generator to stream each log message
    async def event_generator():
        async for log in EventLogger().log(response):
            if hasattr(log, "content"):
                yield json.dumps({"content": log.content}) + "\n"

    # Return the StreamingResponse using the async generator
    return StreamingResponse(event_generator(), media_type="application/json")

@app.post("/query")
async def query_ordinances(request: OrdinanceQuery):
    try:
        if request.stream:
            # Return streaming response
            async def generate():
                result = await rag.aquery(
                    query_str=request.query,
                    state=request.state,
                    city=request.city,
                    filter_conditions=request.filter_conditions,
                    stream=True
                )
               
                # First yield the sources
                yield json.dumps({
                    "type": "sources",
                    "content": result["sources"]
                }) + "\n"
               
                # Then yield the content chunks
                async for chunk in result["generator"]:
                    yield json.dumps({
                        "type": "content",
                        "content": chunk
                    }) + "\n"
           
            return StreamingResponse(
                generate(),
                media_type="application/json"
            )
        else:
            # Return regular response with sources
            result = await rag.aquery(
                query_str=request.query,
                state=request.state,
                city=request.city,
                filter_conditions=request.filter_conditions,
                stream=False
            )
            return {
                "response": result["answer"],
                "sources": result["sources"]
            }
           
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run_parser")
async def run_parser():
    try:
        client = Restack()
        workflow_id = f"{int(time.time() * 1000)}-llm_complete_workflow"

        runId = await client.schedule_workflow(
            workflow_name="municode_parser",
            workflow_id=workflow_id,
        )
        print("Scheduled workflow", runId)

        result = await client.get_workflow_result(
            workflow_id=workflow_id,
            run_id=runId
        )

        return {
            "result": result,
            "workflow_id": workflow_id,
            "run_id": runId
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/run_campbellca_parser")
async def run_parser():
    try:
        client = Restack()
        workflow_id = f"{int(time.time() * 1000)}-llm_complete_workflow"

        runId = await client.schedule_workflow(
            workflow_name="campbellca_parser",
            workflow_id=workflow_id,
        )
        print("Scheduled workflow", runId)

        result = await client.get_workflow_result(
            workflow_id=workflow_id,
            run_id=runId
        )

        return {
            "result": result,
            "workflow_id": workflow_id,
            "run_id": runId
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



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
