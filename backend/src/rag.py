# rag.py
from typing import List, Optional, Dict, Any
from llama_index.core import Settings
from llama_index.core.schema import TextNode, NodeWithScore
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.callbacks import CallbackManager
from llama_index.core.llms import CustomLLM
from llama_index.core.embeddings import BaseEmbedding
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.inference.event_logger import EventLogger
from .ordinance_db import OrdinanceDBWithTogether
from dotenv import load_dotenv
from pydantic import Field

# Load environment variables
load_dotenv()

class LlamaStackLLM(CustomLLM):
    """Custom LLM class for LlamaStack integration"""
    
    client: LlamaStackClient = Field(description="LlamaStack client instance")
    model_name: str = Field(default="Llama3.2-90B-Vision-Instruct", description="Model name")
    system_prompt: str = Field(
        default="You are a helpful assistant specialized in municipal ordinances. Answer questions accurately based on the provided context.",
        description="System prompt"
    )
    temperature: float = Field(default=0.1, description="Temperature for generation")
    
    model_config = {"protected_namespaces": ()}  # Remove model_ namespace protection
    
    def __init__(
        self,
        client: LlamaStackClient,
        model_name: str = "Llama3.2-90B-Vision-Instruct",
        system_prompt: str = "You are a helpful assistant specialized in municipal ordinances. Answer questions accurately based on the provided context.",
        temperature: float = 0.1,
        **kwargs: Any
    ):
        super().__init__(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            temperature=temperature,
            **kwargs
        )

    @property
    def metadata(self) -> Dict:
        """Return metadata about the model."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "context_window": 32768,  # Llama3.2 context window
            "max_tokens": 4096,  # Maximum tokens in response
        }

    def stream_complete(self, prompt: str, **kwargs) -> str:
        """Synchronous streaming completion"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.inference.chat_completion(
            messages=messages,
            model=self.model_name,
            stream=True
        )
        
        full_response = ""
        for chunk in response:
            if hasattr(chunk, "content"):
                full_response += chunk.content
        return full_response

    def complete(self, prompt: str, **kwargs) -> str:
        """Complete the prompt using LlamaStack"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.inference.chat_completion(
            messages=messages,
            model=self.model_name
        )
        return response.completion_message.content

    async def acomplete(self, prompt: str, **kwargs) -> str:
        """Async complete - uses regular complete for now"""
        return self.complete(prompt, **kwargs)

    async def astream_complete(self, prompt: str, **kwargs):
        """Stream complete using LlamaStack"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.inference.chat_completion(
            messages=messages,
            model=self.model_name,
            stream=True
        )
        
        async for log in EventLogger().log(response):
            if hasattr(log, "content"):
                yield log.content

class OrdinanceRetriever(BaseRetriever):
    """Custom retriever that wraps OrdinanceDBWithTogether"""
    
    def __init__(
        self,
        ordinance_db: OrdinanceDBWithTogether,
        similarity_top_k: int = 5,
    ):
        self.ordinance_db = ordinance_db
        self.similarity_top_k = similarity_top_k
        super().__init__()

    def _retrieve(self, query_str: str, **kwargs) -> List[NodeWithScore]:
        """Retrieve relevant nodes given a query"""
        filter_conditions = kwargs.get("filter_conditions", None)
        state = kwargs.get("state", None)
        city = kwargs.get("city", None)
        
        results = self.ordinance_db.search_ordinances(
            query=query_str,
            max_results=self.similarity_top_k,
            filter_conditions=filter_conditions,
            state=state,
            city=city
        )
        
        nodes_with_score = []
        for result in results:
            node = TextNode(
                text=result['document'].split("Content:\n")[1] if "Content:\n" in result['document'] else result['document'],
                metadata=result['metadata'],
                id_=result['id']
            )
            node_with_score = NodeWithScore(
                node=node,
                score=result['relevance_score']
            )
            nodes_with_score.append(node_with_score)
            
        return nodes_with_score



class OrdinanceRAG:
    """RAG system for ordinance retrieval and question answering"""
    
    def __init__(
        self,
        ordinance_db: OrdinanceDBWithTogether,
        llama_client: LlamaStackClient,
        model_name: str = "Llama3.2-90B-Vision-Instruct",
        top_k: int = 5
    ):
        self.ordinance_db = ordinance_db
        self.top_k = top_k
        
        # Initialize LlamaStack LLM
        self.llm = LlamaStackLLM(
            client=llama_client,
            model_name=model_name
        )
        
        # Configure global settings without embedding model
        Settings.llm = self.llm
        Settings.callback_manager = CallbackManager()
        Settings.embed_model = None  # Disable default embedding model
        
        # Initialize custom retriever
        self.retriever = OrdinanceRetriever(
            ordinance_db=self.ordinance_db,
            similarity_top_k=self.top_k
        )
    
    async def aquery(
        self,
        query_str: str,
        filter_conditions: Optional[Dict] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        stream: bool = False
    ):
        """Async query with optional streaming"""
        # Get relevant documents
        nodes = self.retriever._retrieve(
            query_str,
            filter_conditions=filter_conditions,
            state=state,
            city=city
        )
        
        # Format context
        context = "\n\n".join([
            f"Document {i+1}:\n{node.node.text}"
            for i, node in enumerate(nodes)
        ])
        
        # Create prompt
        prompt = (
            "Based on the following ordinance documents, please answer the question.\n\n"
            f"Documents:\n{context}\n\n"
            f"Question: {query_str}\n\n"
            "Answer:"
        )
        
        if stream:
            generator = self.llm.astream_complete(prompt)
            return generator  # Return the async generator directly
        else:
            return await self.llm.acomplete(prompt)
    """RAG system for ordinance retrieval and question answering"""
    
    def __init__(
        self,
        ordinance_db: OrdinanceDBWithTogether,
        llama_client: LlamaStackClient,
        model_name: str = "Llama3.2-90B-Vision-Instruct",
        top_k: int = 5
    ):
        self.ordinance_db = ordinance_db
        self.top_k = top_k
        
        # Initialize LlamaStack LLM
        self.llm = LlamaStackLLM(
            client=llama_client,
            model_name=model_name
        )
        
        # Configure global settings without embedding model
        Settings.llm = self.llm
        Settings.callback_manager = CallbackManager()
        Settings.embed_model = None  # Disable default embedding model
        
        # Initialize custom retriever
        self.retriever = OrdinanceRetriever(
            ordinance_db=self.ordinance_db,
            similarity_top_k=self.top_k
        )
    
    async def aquery(
        self,
        query_str: str,
        filter_conditions: Optional[Dict] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        stream: bool = False
    ):
        """Async query with optional streaming"""
        # Get relevant documents
        nodes = self.retriever._retrieve(
            query_str,
            filter_conditions=filter_conditions,
            state=state,
            city=city
        )
        
        # Format context
        context = "\n\n".join([
            f"Document {i+1}:\n{node.node.text}"
            for i, node in enumerate(nodes)
        ])
        
        # Create prompt
        prompt = (
            "Based on the following ordinance documents, please answer the question.\n\n"
            f"Documents:\n{context}\n\n"
            f"Question: {query_str}\n\n"
            "Answer:"
        )
        
        if stream:
            return self.llm.astream_complete(prompt)
        else:
            return await self.llm.acomplete(prompt)