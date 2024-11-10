from chromadb.api.types import Documents, EmbeddingFunction
from typing import List
from together import Together
import numpy as np

class TogetherEmbeddingFunction(EmbeddingFunction):
    def __init__(
        self, 
        api_key: str,
        model_name: str = "togethercomputer/m2-bert-80M-32k-retrieval",
        batch_size: int = 32  # Together might have rate limits, so we batch
    ):
        """
        Initialize Together AI embedding function
        
        Args:
            api_key: Together AI API key
            model_name: Model to use for embeddings
            batch_size: Number of texts to embed at once
        """
        self.client = Together(api_key=api_key)
        self.model_name = model_name
        self.batch_size = batch_size
    
    def _batch_embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of texts
        
        Args:
            texts: List of strings to embed
            
        Returns:
            List of embeddings
        """
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            # Extract embeddings from response
            embeddings = [data.embedding for data in response.data]
            return embeddings
            
        except Exception as e:
            print(f"Error in batch embedding: {str(e)}")
            # Return zero embeddings in case of error
            # You might want to handle this differently based on your needs
            dim = 1024  # Together model dimension
            return [[0.0] * dim] * len(texts)
    
    def __call__(self, texts: Documents) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of strings to generate embeddings for
            
        Returns:
            List of embeddings, each embedding is a List[float]
        """
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self._batch_embed(batch)
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings