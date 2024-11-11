# test_rag.py
import os
import asyncio
import json
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.inference.event_logger import EventLogger
from ordinance_db import OrdinanceDBWithTogether
from rag import OrdinanceRAG

# Load environment variables
load_dotenv()

async def test_single_query(rag: OrdinanceRAG, test: dict):
    """Test a single query with proper async handling"""
    print(f"\nTesting: {test['name']}")
    print(f"Query: {test['query']}")
    print(f"State: {test['state']}, City: {test['city']}")
    print("Stream:", test['stream'])
    
    try:
        if test['stream']:
            print("Response:")
            async for chunk in await rag.aquery(
                query_str=test['query'],
                state=test['state'],
                city=test['city'],
                stream=True
            ):
                print(chunk, end='', flush=True)
            print("\n")
        else:
            response = await rag.aquery(
                query_str=test['query'],
                state=test['state'],
                city=test['city'],
                stream=False
            )
            print("Response:", response)
            
        print("✓ Test passed")
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")

async def test_rag():
    print("\n=== Testing RAG System ===")
    
    try:
        # Initialize components
        print("Initializing components...")
        base_url = "http://localhost:5050"
        print(f"Connecting to LlamaStack at {base_url}...")
        
        llama_client = LlamaStackClient(base_url=base_url)
        
        # Test LlamaStack connection
        try:
            # Simple test query to verify connection
            response = llama_client.inference.chat_completion(
                messages=[
                    {"role": "user", "content": "Hi"}
                ],
                model="Llama3.2-90B-Vision-Instruct"
            )
            print("LlamaStack connection successful")
        except Exception as e:
            print(f"Failed to connect to LlamaStack: {str(e)}")
            return
        
        print("Initializing OrdinanceDB...")
        ordinance_db = OrdinanceDBWithTogether(
            api_key=os.getenv('TOGETHER_API_KEY'),
            collection_name="california_city_ordinances"
        )
        
        print("Initializing RAG system...")
        rag = OrdinanceRAG(
            ordinance_db=ordinance_db,
            llama_client=llama_client
        )
        
        # Test queries
        test_queries = [
            {
                "name": "Basic Query",
                "query": "What are the parking requirements for residential areas?",
                "state": "CA",
                "city": None,
                "stream": False
            },
            {
                "name": "City-Specific Query",
                "query": "What are the fire safety requirements?",
                "state": "CA",
                "city": "San Francisco",
                "stream": False
            },
            {
                "name": "Streaming Query",
                "query": "What are the business license requirements?",
                "state": "CA",
                "city": None,
                "stream": True
            }
        ]
        
        # Run tests
        for test in test_queries:
            await test_single_query(rag, test)
                
    except Exception as e:
        print(f"Error initializing components: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_rag())