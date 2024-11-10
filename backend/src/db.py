from abc import ABC, abstractmethod
import chromadb
from chromadb.api.types import EmbeddingFunction
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from typing import List, Dict, Union

class ChromaDb(ABC):
    def __init__(
        self,
        embedding_function: EmbeddingFunction = DefaultEmbeddingFunction()
    ):
        self.embedding_function = embedding_function
        # Connect to ChromaDB running in Docker
        self.client = chromadb.HttpClient(
            host="localhost",
            port=8001  # This matches the port in docker-compose.yaml
        )
        self.name = None
    
    def create_or_get_collection(self, collection_name: str):
        """Create or get a collection by name"""
        self.name = collection_name
        return self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
    
    def query(
        self,
        text: str, 
        max_results: int, 
        collection,
        where: Dict = None
    ) -> Union[List[str], Dict]:
        """
        Query the collection. Returns list of strings for backward compatibility
        or full response when where parameter is used.
        """
        response = collection.query(
            query_texts=[text],
            n_results=max_results,
            where=where
        )
        
        # Return full response if where parameter is used
        if where is not None:
            return response
            
        # Return list of documents for backward compatibility
        return [
            s 
            for s, d in zip(response['documents'][0], response['distances'][0])
        ]

    def delete(self):
        """Delete the collection"""
        try:
            self.client.delete_collection(name=self.name)
        except ValueError:
            pass

if __name__ == '__main__':
    class TestDb(ChromaDb):
        """Test class for demonstration"""
        pass
        
    # Create instance with default embedding function
    db = TestDb(embedding_function=DefaultEmbeddingFunction())
    
    # Create a collection and add some test documents
    collection_name = "collection"
    collection = db.create_or_get_collection(collection_name)
    
    # Add some test documents
    collection.add(
        documents=["This is a test document", "This is another test document"],
        metadatas=[{"source": "test1"}, {"source": "test2"}],
        ids=["id1", "id2"]
    )
    
    # Test original query behavior
    results = db.query("test document", max_results=2, collection=collection)
    print("\nOriginal query results:", results)
    
    # Test new query behavior with metadata filtering
    results_with_filter = db.query(
        "test document", 
        max_results=2, 
        collection=collection,
        where={"source": "test1"}
    )
    print("\nQuery results with filter:", results_with_filter)