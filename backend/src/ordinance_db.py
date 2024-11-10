# ordinance_db.py
from typing import List, Dict
import uuid
import os
from dotenv import load_dotenv
from db import ChromaDb
from embeddings import TogetherEmbeddingFunction
from parser import extract_ordinance_metadata

# Load environment variables from .env file
load_dotenv()

class OrdinanceDBWithTogether(ChromaDb):
    def __init__(
        self,
        api_key: str = os.getenv('TOGETHER_API_KEY'),
        model_name: str = "togethercomputer/m2-bert-80M-32k-retrieval",
        collection_name: str = "ordinances",
        batch_size: int = 32
    ):
        if not api_key:
            raise ValueError("TOGETHER_API_KEY environment variable is not set")
            
        embedding_function = TogetherEmbeddingFunction(
            api_key=api_key,
            model_name=model_name,
            batch_size=batch_size
        )
        super().__init__(embedding_function=embedding_function)
        
        # Delete existing collection if it exists
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass
            
        # Create new collection with proper settings
        self.collection = self.client.create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        self.name = collection_name

    # ... rest of the class implementation remains the same ...

def main():
    EXCEL_PATH = "../data/CaliforniaCityCACodeofOrdinancesEXPORT20220511.xlsx"
    
    try:
        # Create DB directly from Excel using API key from environment
        print("Creating database and adding ordinances...")
        db = OrdinanceDBWithTogether.from_excel(
            excel_path=EXCEL_PATH,
            api_key=os.getenv('TOGETHER_API_KEY'),
            collection_name="california_city_ordinances"
        )
        
        # Example searches
        print("\nSearching for building regulations...")
        results = db.search_ordinances(
            "building safety requirements",
            max_results=3,
            filter_conditions={"title": "TITLE 8, BUILDING REGULATIONS"}
        )
        
        for r in results:
            print(f"\nRelevance Score: {r['relevance_score']:.2f}")
            print(f"Title: {r['metadata']['title']}")
            print(f"Section: {r['metadata']['section']}")
            print(f"Subtitle: {r['metadata']['subtitle']}")
            print("\nExcerpt:")
            print(r['document'].split("Content:\n")[1][:200] + "...")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()