# ordinance_db.py
from typing import List, Dict, Optional
import uuid
import os
import json
from dotenv import load_dotenv
from .db import ChromaDb
from .embeddings import TogetherEmbeddingFunction
from .parser import extract_ordinance_metadata

# Load environment variables from .env file
load_dotenv()

class OrdinanceDBWithTogether(ChromaDb):
    def __init__(
        self,
        api_key: str = os.getenv('TOGETHER_API_KEY'),
        model_name: str = "togethercomputer/m2-bert-80M-32k-retrieval",
        collection_name: str = "ordinances",
        batch_size: int = 32,
        force_recreate: bool = False
    ):
        """
        Initialize OrdinanceDB with Together AI embeddings.
        
        Args:
            api_key: Together AI API key
            model_name: Name of the embedding model
            collection_name: Name for the ChromaDB collection
            batch_size: Batch size for processing
            force_recreate: Whether to force create a new collection
        """
        if not api_key:
            raise ValueError("TOGETHER_API_KEY environment variable is not set")
            
        embedding_function = TogetherEmbeddingFunction(
            api_key=api_key,
            model_name=model_name,
            batch_size=batch_size
        )
        super().__init__(embedding_function=embedding_function)
        
        self.name = collection_name
        self.initialize_collection(force_recreate)

    def initialize_collection(self, force_recreate: bool = False):
        """Initialize or get the ChromaDB collection"""
        if force_recreate:
            self.delete_collection()
            self.collection = self.create_new_collection()
        else:
            try:
                self.collection = self.client.get_collection(
                    name=self.name,
                    embedding_function=self.embedding_function
                )
                print(f"Using existing collection: {self.name}")
            except Exception:
                print(f"Creating new collection: {self.name}")
                self.collection = self.create_new_collection()

    def create_new_collection(self):
        """Create a new ChromaDB collection with proper settings"""
        return self.client.create_collection(
            name=self.name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

    def delete_collection(self) -> bool:
        """Delete the current collection if it exists"""
        try:
            self.client.delete_collection(self.name)
            print(f"Successfully deleted collection: {self.name}")
            return True
        except Exception as e:
            print(f"Error deleting collection: {str(e)}")
            return False

    def get_collection_info(self) -> Optional[Dict]:
        """Get information about the current collection"""
        try:
            count = self.collection.count()
            metadata = self.collection.get()
            states = set()
            cities = set()
            
            # Extract unique states and cities from metadata
            if metadata and 'metadatas' in metadata:
                for meta in metadata['metadatas']:
                    if 'state' in meta:
                        states.add(meta['state'])
                    if 'city' in meta:
                        cities.add(meta['city'])
            
            return {
                "name": self.name,
                "document_count": count,
                "metadata": self.collection.metadata,
                "states": sorted(list(states)),
                "cities": sorted(list(cities))
            }
        except Exception as e:
            print(f"Error getting collection info: {str(e)}")
            return None

    def list_collections(self) -> List:
        """List all available collections"""
        try:
            return self.client.list_collections()
        except Exception as e:
            print(f"Error listing collections: {str(e)}")
            return []
    
    def add_ordinances(self, ordinances: List[Dict], batch_size: int = 100):
        """Add multiple ordinances to the collection"""
        documents = []
        metadatas = []
        ids = []
        
        for ordinance in ordinances:
            formatted = self._format_document(ordinance)
            documents.append(formatted)
            metadatas.append(ordinance['metadata'])
            ids.append(str(uuid.uuid4()))
        
        for i in range(0, len(documents), batch_size):
            batch_end = min(i + batch_size, len(documents))
            try:
                self.collection.add(
                    documents=documents[i:batch_end],
                    metadatas=metadatas[i:batch_end],
                    ids=ids[i:batch_end]
                )
                print(f"Added batch {i//batch_size + 1} of {(len(documents)-1)//batch_size + 1}")
            except Exception as e:
                print(f"Error adding batch {i//batch_size + 1}: {str(e)}")
                raise

    def update_collection(
        self,
        new_documents: List[Dict],
        batch_size: int = 100,
        skip_duplicates: bool = True
    ):
        """Update existing collection with new documents"""
        if skip_duplicates:
            existing_docs = set(self.collection.get()['documents'])
            new_documents = [doc for doc in new_documents if doc not in existing_docs]
        
        if new_documents:
            self.add_ordinances(new_documents, batch_size)
            print(f"Added {len(new_documents)} new documents to collection")
        else:
            print("No new documents to add")
    
    def _format_document(self, ordinance: Dict) -> str:
        """Format ordinance for search by combining metadata and content"""
        metadata = ordinance['metadata']
        formatted = f"""
Title: {metadata.get('title', '')}
Chapter: {metadata.get('chapter', '')}
Section: {metadata.get('section', '')}
Location: {metadata.get('state', '')}, {metadata.get('city', '')}
Subtitle: {metadata.get('subtitle', '')}
URL: {metadata.get('url', '')}

Content:
{ordinance.get('content', '')}
        """.strip()
        return formatted
    
    
    def search_ordinances(
        self,
        query: str,
        max_results: int = 5,
        filter_conditions: Dict = None,
        state: str = None,
        city: str = None
    ) -> List[Dict]:
        """
        Search ordinances with optional filtering using ChromaDB's $and operator
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            filter_conditions: Additional filter conditions
            state: Filter by state
            city: Filter by city
        """
        query_params = {
            "query_texts": [query],
            "n_results": max_results
        }
        
        # Combine all filters using ChromaDB's $and operator
        if any([filter_conditions, state, city]):
            where_conditions = []
            
            if filter_conditions:
                for key, value in filter_conditions.items():
                    where_conditions.append({key: value})
            if state:
                where_conditions.append({"state": state})
            if city:
                where_conditions.append({"city": city})
                
            if where_conditions:
                if len(where_conditions) == 1:
                    query_params["where"] = where_conditions[0]
                else:
                    query_params["where"] = {"$and": where_conditions}
        
        results = self.collection.query(**query_params)
        
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
        print(f"Parsing Excel file: {excel_path}")
        ordinances = extract_ordinance_metadata(excel_path)
        if not ordinances:
            raise ValueError("Failed to parse ordinances from Excel file")
        
        print(f"Creating database instance...")
        kwargs['force_recreate'] = True
        db = cls(api_key=api_key, **kwargs)
        
        print(f"Adding {len(ordinances)} ordinances to database...")
        db.add_ordinances(ordinances)
        
        return db

    @classmethod
    def from_json(cls, json_path: str, api_key: str, **kwargs):
        """Create OrdinanceDB instance from JSON file"""
        print(f"Loading JSON file: {json_path}")
        with open(json_path, 'r') as f:
            ordinances = json.load(f)
        
        print(f"Creating database instance...")
        kwargs['force_recreate'] = True
        db = cls(api_key=api_key, **kwargs)
        
        print(f"Adding {len(ordinances)} ordinances to database...")
        db.add_ordinances(ordinances)
        
        return db

def main():
    EXCEL_PATH = "../data/CaliforniaCityCACodeofOrdinancesEXPORT20220511.xlsx"
    
    try:
        # Create DB from Excel
        print("\n=== Creating database from Excel ===")
        db = OrdinanceDBWithTogether.from_excel(
            excel_path=EXCEL_PATH,
            api_key=os.getenv('TOGETHER_API_KEY'),
            collection_name="california_city_ordinances"
        )
        # db = OrdinanceDBWithTogether(force_recreate=False)

        # Get collection info
        print("\n=== Collection Info ===")
        info = db.get_collection_info()
        print(f"Collection Name: {info['name']}")
        print(f"Document Count: {info['document_count']}")
        print(f"Available States: {', '.join(info['states'])}")
        print(f"Available Cities: {', '.join(info['cities'])}")
        
        # Example searches
        print("\n=== Example Searches ===")
        
        # Search with city filter
        results = db.search_ordinances(
            query="building permits",
            max_results=3,
            city="California City"
        )
        
        # Search with multiple filters
        results = db.search_ordinances(
            query="zoning regulations",
            max_results=3,
            filter_conditions={"title": "TITLE 8, BUILDING REGULATIONS"},
            state="CA"
        )
        
        for r in results:
            print(f"\nRelevance Score: {r['relevance_score']:.2f}")
            print(f"Location: {r['metadata']['state']}, {r['metadata']['city']}")
            print(f"Title: {r['metadata']['title']}")
            print(f"Section: {r['metadata']['section']}")
            print(f"URL: {r['metadata'].get('url', 'N/A')}")
            print("\nExcerpt:")
            print(r['document'].split("Content:\n")[1][:200] + "...")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()