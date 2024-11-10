import pandas as pd
import json
from pathlib import Path

def extract_ordinance_metadata(excel_path):
    """
    Extract metadata and content from Code of Ordinances Excel file.
    
    Args:
        excel_path (str): Path to the XLSX file
        
    Returns:
        list: List of dictionaries containing metadata and content for each section
    """
    try:
        df = pd.read_excel(excel_path, skiprows=1, header=0)
        df.index = range(1, len(df) + 1)
        current_title = None
        current_chapter = None
        current_title_subtitle = None
        current_chapter_subtitle = None

        # Initialize list to store structured data
        ordinances = []

        # Iterate through rows and extract metadata
        for i, row in df.iterrows():
            curr_t = str(row.get('Title', '')).strip()
            curr_subt = str(row.get('Subtitle', '')).strip()
            if curr_t != "Code of Ordinances":
                if curr_t.startswith("TITLE "):
                    current_title = curr_t
                    current_title_subtitle = curr_subt
                elif curr_t.startswith("CHAPTER"):
                    current_chapter = curr_t
                    current_chapter_subtitle = curr_subt
                else:
                    curr_url = str(row.get('Url', '')).strip()
                    ordinance = {
                        'metadata': {
                            'title': current_title + ', ' + current_title_subtitle,
                            'chapter': current_chapter + ', ' + current_chapter_subtitle,
                            'section': curr_t,
                            'state': curr_url.split('/')[3],
                            'city': curr_url.split('/')[4],
                            'subtitle': curr_subt,
                            'url': curr_url
                        },
                        'content': str(row.get('Content', '')).strip()
                    }
                    # Remove empty metadata fields
                    ordinance['metadata'] = {k: v for k, v in ordinance['metadata'].items() if v}
                    
                    ordinances.append(ordinance)
                    
        # Save to JSON file
        output_path = Path(excel_path).with_suffix('.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(ordinances, f, indent=2, ensure_ascii=False)
            
        print(f"Successfully processed {len(ordinances)} ordinances")
        print(f"Output saved to: {output_path}")
        
        return ordinances
                
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None

def main():
    # Example usage
    file_path = '../data/CaliforniaCityCACodeofOrdinancesEXPORT20220511.xlsx'
    results = extract_ordinance_metadata(file_path)
    
    if results:
        # Print first ordinance as example
        print("\nExample of first ordinance:")
        print(json.dumps(results[0], indent=2))

if __name__ == "__main__":
    main()