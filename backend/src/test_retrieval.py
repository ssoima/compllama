# test_retrieval.py
from ordinance_db import OrdinanceDBWithTogether
import os
import json
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables
load_dotenv()

def display_results(results: List[Dict], query_description: str, save_to_file: bool = False):
    """
    Display search results in a consistent format with optional file saving
    
    Args:
        results: List of search results
        query_description: Description of the search query
        save_to_file: Whether to save results to a JSON file
    """
    output = []
    
    print(f"\n=== Search Results for: {query_description} ===")
    print(f"Found {len(results)} results\n")
    
    for i, result in enumerate(results, 1):
        result_data = {
            "result_number": i,
            "relevance_score": result['relevance_score'],
            "metadata": result['metadata'],
            "content": result['document'].split("Content:\n")[1] if "Content:\n" in result['document'] else result['document']
        }
        output.append(result_data)
        
        # Print formatted results
        print(f"Result {i}")
        print(f"Relevance Score: {result['relevance_score']:.2f}")
        print(f"Title: {result['metadata']['title']}")
        print(f"Chapter: {result['metadata']['chapter']}")
        print(f"Section: {result['metadata']['section']}")
        print(f"Location: {result['metadata'].get('state', 'N/A')}, {result['metadata'].get('city', 'N/A')}")
        print(f"Subtitle: {result['metadata']['subtitle']}")
        print(f"URL: {result['metadata'].get('url', 'N/A')}")
        print("\nContent:")
        print(result_data['content'])
        print("\n" + "="*80 + "\n")
    
    if save_to_file:
        filename = f"search_results_{query_description.lower().replace(' ', '_')}.json"
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Results saved to {filename}")

def run_search_tests(db: OrdinanceDBWithTogether, save_results: bool = False):
    """Run a series of search tests on the database"""
    
    # Check collection info
    print("\n=== Collection Information ===")
    info = db.get_collection_info()
    print(f"Collection Name: {info['name']}")
    print(f"Document Count: {info['document_count']}")
    print(f"Metadata: {info['metadata']}")
    
    # Test cases
    test_cases = [
        {
            "description": "Parking Requirements in Residential Areas",
            "query": "parking requirements for residential areas",
            "max_results": 3,
            "filter_conditions": None
        },
        {
            "description": "Fire Safety Requirements (Building Regulations Only)",
            "query": "fire safety requirements",
            "max_results": 3,
            "filter_conditions": {"title": "TITLE 8, BUILDING REGULATIONS"}
        },
        {
            "description": "Business License Requirements",
            "query": "business license application process and fees",
            "max_results": 3,
            "filter_conditions": {"chapter": "Business Licenses"}
        },
        {
            "description": "Environmental Regulations",
            "query": "environmental protection and waste management",
            "max_results": 3,
            "filter_conditions": None
        },
        {
            "description": "Zoning Requirements",
            "query": "zoning restrictions for commercial properties",
            "max_results": 3,
            "filter_conditions": None
        }
    ]
    
    # Run tests
    for test in test_cases:
        try:
            results = db.search_ordinances(
                query=test["query"],
                max_results=test["max_results"],
                filter_conditions=test["filter_conditions"]
            )
            display_results(results, test["description"], save_results)
        except Exception as e:
            print(f"\nError in test '{test['description']}': {str(e)}")

def main():
    try:
        # Initialize database connection
        print("Initializing database connection...")
        db = OrdinanceDBWithTogether(
            api_key=os.getenv('TOGETHER_API_KEY'),
            collection_name="california_city_ordinances"
        )
        
        # Optional: Verify database is populated
        info = db.get_collection_info()
        if info['document_count'] == 0:
            print("\nWarning: Database appears to be empty. Please run ordinance_db.py first to populate the database.")
            return
        
        # Run search tests
        run_search_tests(db, save_results=True)
        
    except Exception as e:
        print(f"\nError in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()