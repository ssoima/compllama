from dotenv import load_dotenv
import os
from .ordinance_db import OrdinanceDBWithTogether
from typing import List
from pathlib import Path


def get_files_under_dir(directory: str) -> List[str]:
    """
    Get all files from a directory recursively.
    
    Args:
        directory (str): Path to the directory to search
        
    Returns:
        List[str]: List of file paths as strings
    """
    try:
        # Convert directory to Path object
        dir_path = Path(directory)
        
        # Check if directory exists
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
            
        # Get all files recursively
        all_files = list(dir_path.rglob("*"))
        
        # Filter out directories, keep only files
        files = [str(f) for f in all_files if f.is_file()]
        
        return files
        
    except Exception as e:
        print(f"Error reading directory {directory}: {str(e)}")
        raise

def init_database(collection_name: str = "ordinances_collection"):
    load_dotenv()

    try:
        directory = "data/raw_files"
        excel_paths = get_files_under_dir(directory)
        print("Initializing database...")
        # Initialize database with first file then interate over the other files and add them to the database
        first_file = directory + "/CaliforniaCityCACodeofOrdinancesEXPORT20220511.xlsx"
        db = OrdinanceDBWithTogether.from_excel(
            excel_path=first_file,
            api_key=os.getenv('TOGETHER_API_KEY'),
            collection_name=collection_name,
            force_recreate=True  # Create fresh database for first file
        )
        
        # Add remaining files to the existing database
        for excel_path in excel_paths[1:]:
            print(f"\nProcessing file: {excel_path}")
            try:
                # Use update_collection to add new documents
                ordinances = db.extract_ordinance_metadata(excel_path)
                db.update_collection(
                    new_documents=ordinances,
                    batch_size=100,
                    skip_duplicates=True
                )
            except Exception as e:
                print(f"Error processing {excel_path}: {str(e)}")
                continue
        
        # Verify the data was loaded
        info = db.get_collection_info()
        print("\n=== Final Database Information ===")
        print(f"Collection Name: {info['name']}")
        print(f"Total Document Count: {info['document_count']}")
        print(f"States: {', '.join(info['states'])}")
        print(f"Cities: {', '.join(info['cities'])}")
        
        return db
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

def get_excel_files(directory: str) -> List[str]:
    """Get all Excel files from a directory"""
    excel_extensions = ['.xlsx', '.xls']
    excel_files = []
    
    for ext in excel_extensions:
        excel_files.extend(Path(directory).glob(f'**/*{ext}'))
    
    return [str(file) for file in excel_files]

if __name__ == "__main__":
    # Initialize database with all files
    db = init_database(
        collection_name="combined_ordinances"
    )