import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

def process_abstracts(input_path: str, output_path: str) -> None:
    """
    Process abstracts from a JSON file, categorize them by disease,
    extract NCT IDs, and output a summary.
    
    Args:
        input_path: Path to the input JSON file containing abstracts.
        output_path: Path to the output text file for the summary.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        logging.error(f"Input file not found: {input_path}")
        return

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data: List[Dict[str, Any]] = json.load(f)
            logging.info(f"Successfully loaded {len(data)} records from {input_path}")
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON file {input_path}: {e}")
        return
    except Exception as e:
        logging.error(f"Unexpected error reading {input_path}: {e}")
        return

    diseases: Dict[str, List[str]] = {
        'Influenza': ['influenza', 'flu'],
        'Malaria': ['malaria', 'plasmodium'],
        'Anthrax': ['anthrax', 'bacillus anthracis'],
        'Hepatitis B': ['hepatitis b', 'hbv', 'heplisav'],
        'COVID-19': ['covid', 'sars-cov-2'],
        'Hookworm': ['hookworm', 'necator'],
        'RSV': ['rsv', 'respiratory syncytial'],
        'HPV': ['hpv', 'papillomavirus'],
        'Rabies': ['rabies'],
        'HIV': ['hiv', 'human immunodeficiency'],
        'Tuberculosis': ['tuberculosis', 'tb'],
        'Ebola': ['ebola'],
        'Pertussis': ['pertussis']
    }

    output_file = Path(output_path)
    # Ensure parent directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_file, 'w', encoding='utf-8') as out:
            processed_count = 0
            for item in data:
                title: str = item.get('title', '')
                abstract: str = item.get('abstract', '')
                if not abstract:
                    continue
                
                text: str = f"{title} {abstract}".lower()
                
                # Find NCT IDs
                nct_ids: Set[str] = set(re.findall(r'NCT\d+', abstract))
                
                # Determine disease category
                category: str = 'Other/Unknown'
                for k, v in diseases.items():
                    if any(keyword in text for keyword in v):
                        category = k
                        break
                        
                out.write(f"Category: {category}\n")
                out.write(f"Title: {title}\n")
                out.write(f"PMID: {item.get('pmid')} | DOI: {item.get('doi')}\n")
                out.write(f"NCT IDs: {', '.join(nct_ids) if nct_ids else 'Not found'}\n")
                
                # Extract safety sentences
                sentences: List[str] = abstract.split('.')
                safety_sents: List[str] = [s.strip() for s in sentences if any(kw in s.lower() for kw in ['safe', 'adverse', 'tolerat'])]
                
                if safety_sents:
                    out.write(f"Safety: {'. '.join(safety_sents)}.\n")
                out.write('-'*80 + '\n')
                
                processed_count += 1
                
            logging.info(f"Successfully wrote {processed_count} records to {output_path}")
            
    except IOError as e:
        logging.error(f"Failed to write to {output_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during writing: {e}")

if __name__ == "__main__":
    input_file = r'C:\Users\Administrator\.gemini\antigravity\brain\055f4f97-3ebf-4469-983d-3cf006f715a1\scratch\pubmed_broad_abstracts.json'
    output_file = r'C:\Users\Administrator\.gemini\antigravity\brain\055f4f97-3ebf-4469-983d-3cf006f715a1\scratch\broad_summary.txt'
    process_abstracts(input_file, output_file)
