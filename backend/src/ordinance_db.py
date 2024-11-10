# ordinance_db.py
from typing import List, Dict
import uuid
from db import ChromaDb
from embeddings import TogetherEmbeddingFunction
from parser import extract_ordinance_metadata

class OrdinanceDBWithTogether(ChromaDb):
    def __init__(
        self,
        api_key: str,
        model_name: str = "togethercomputer/m2-bert-80M-32k-retrieval",
        collection_name: str = "ordinances",
        batch_size: int = 32
    ):
        embedding_function = TogetherEmbeddingFunction(
            api_key=api_key,
            model_name=model_name,
            batch_size=batch_size
        )
        super().__init__(embedding_function=embedding_function)
        self.collection = self.create_or_get_collection(collection_name)
        self.name = collection_name
    
    def add_ordinances(self, ordinances: List[Dict]):
        """Add multiple ordinances to the collection"""
        documents = []
        metadatas = []
        ids = []
        
        for ordinance in ordinances:
            # Format document as a searchable text
            formatted = self._format_document(ordinance)
            documents.append(formatted)
            metadatas.append(ordinance['metadata'])  # Use original metadata
            ids.append(str(uuid.uuid4()))
        
        # Add documents in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            self.collection.add(
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )
    
    def _format_document(self, ordinance: Dict) -> str:
        """Format ordinance for search by combining metadata and content"""
        metadata = ordinance['metadata']
        formatted = f"""
Title: {metadata.get('title', '')}
Chapter: {metadata.get('chapter', '')}
Section: {metadata.get('section', '')}
Subtitle: {metadata.get('subtitle', '')}

Content:
{ordinance.get('content', '')}
        """.strip()
        return formatted
    
    def search_ordinances(
        self,
        query: str,
        max_results: int = 5,
        filter_conditions: Dict = None
    ) -> List[Dict]:
        """Search ordinances with optional filtering"""
        where = filter_conditions if filter_conditions else {}
        
        results = self.collection.query(
            query_texts=[query],
            n_results=max_results,
            where=where
        )
        
        formatted_results = []
        for doc, metadata, distance, id_ in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0],
            results['ids'][0]
        ):
            formatted_results.append({
                'document': doc,
                'metadata': metadata,
                'relevance_score': 1 - distance,
                'id': id_
            })
            
        return formatted_results
    
    @classmethod
    def from_excel(cls, excel_path: str, api_key: str, **kwargs):
        """Create OrdinanceDB instance from Excel file"""
        ordinances = extract_ordinance_metadata(excel_path)
        if not ordinances:
            raise ValueError("Failed to parse ordinances from Excel file")
        
        db = cls(api_key=api_key, **kwargs)
        db.add_ordinances(ordinances)
        return db

def main():
    # Example usage
    TOGETHER_API_KEY = "c18c227d834619786cb5509a5ef931838e727bbb6211ad446b144e6d5eed2c52"
    EXCEL_PATH = "../data/CaliforniaCityCACodeofOrdinancesEXPORT20220511.xlsx"
    
    try:
        # Create DB directly from Excel
        db = OrdinanceDBWithTogether.from_excel(
            excel_path=EXCEL_PATH,
            api_key=TOGETHER_API_KEY,
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

if __name__ == "__main__":
    main()