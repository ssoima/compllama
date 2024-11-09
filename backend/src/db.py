from abc import ABC, abstractmethod
import chromadb
from chromadb.api.types import EmbeddingFunction
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from typing import List


class ChromaDb(ABC):
    def __init__(
        self,
        embedding_function: EmbeddingFunction = DefaultEmbeddingFunction()
    ):
        self.embedding_function= embedding_function
        # Connect to ChromaDB running in Docker
        self.client = chromadb.HttpClient(
            host="localhost",
            port=8001  # This matches the port in docker-compose.yaml
        )
    
    def create_or_get_collection(self, collection_name: str):
        return self.client.get_or_create_collection(collection_name)

    
    def query(
        self, text: str, 
        max_results: int, 
        collection
    ) -> List[str]:
        response = collection.query(query_texts=[text], n_results=max_results)
        close_results = [
            s 
            for s, d in zip(response['documents'][0], response['distances'][0])
        ]
        return close_results 

    def delete(self):
        super().delete()
        try:
            self.client.delete_collection(name=self.name)
        except ValueError:
            pass

if __name__ == '__main__':
    db = ChromaDb(embedding_function=DefaultEmbeddingFunction)
    # Create a collection and add some test documents
    collection_name = "collection"
    collection = db.create_or_get_collection(collection_name)
    
    # Add some test documents
    collection.add(
        documents=["This is a test document", "This is another test document"],
        metadatas=[{"source": "test1"}, {"source": "test2"}],
        ids=["id1", "id2"]
    )
    
    # Test query
    
    results = db.query("test document", max_results=2, collection=collection)
    print("Query results:", results)
