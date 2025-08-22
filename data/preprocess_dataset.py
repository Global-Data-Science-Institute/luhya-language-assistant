# preprocess_dataset.py - Run this locally to prepare your dataset
import json
import re
import pandas as pd
from datasets import load_dataset

def clean_luhya_text(text):
    """Clean Luhya text by removing dialect tags and extra formatting"""
    if not text or pd.isna(text):
        return ""
    
    # Remove dialect tags like <luy_bukusu>, <luy_maragoli>, etc.
    text = re.sub(r'<luy_[^>]*>\s*', '', text)
    
    # Clean up extra whitespace
    text = ' '.join(text.split())
    
    return text.strip()

def process_luhya_dataset():
    """Download and process the Luhya dataset"""
    print("Loading dataset from HuggingFace...")
    
    # Load your dataset
    dataset = load_dataset("mamakobe/luhya-multilingual-dataset")
    
    # Combine all splits
    all_data = []
    for split_name in dataset.keys():
        print(f"Processing {split_name} split...")
        split_data = dataset[split_name].to_pandas()
        all_data.append(split_data)
    
    import pandas as pd
    df = pd.concat(all_data, ignore_index=True)
    
    print(f"Total rows: {len(df)}")
    
    # Process each row
    processed_data = []
    
    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"Processed {idx}/{len(df)} rows...")
        
        # Skip if essential fields are missing
        if pd.isna(row['source_text']) or pd.isna(row['target_text']):
            continue
        
        # Clean the texts
        source_text = clean_luhya_text(str(row['source_text']))
        target_text = clean_luhya_text(str(row['target_text']))
        
        if not source_text or not target_text:
            continue
        
        # Extract dialect from target_text if it has tags, otherwise use dialect field
        dialect = str(row.get('dialect', '')).strip()
        if dialect in ['null', 'nan', ''] or pd.isna(dialect):
            # Try to extract from text tags
            if '<luy_' in str(row['target_text']):
                match = re.search(r'<luy_([^>]+)>', str(row['target_text']))
                if match:
                    dialect = match.group(1).title()
            else:
                dialect = 'General'
        
        # Create processed entry
        entry = {
            'source_text': source_text,
            'target_text': target_text,
            'source_lang': str(row.get('source_lang', 'unknown')).strip(),
            'target_lang': str(row.get('target_lang', 'luy')).strip(),
            'dialect': dialect,
            'domain': str(row.get('domain', 'general')).strip(),
            'id': f"entry_{idx}"
        }
        
        processed_data.append(entry)
    
    print(f"Successfully processed {len(processed_data)} entries")
    
    # Save to JSON
    output_file = 'luhya_dataset.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    print(f"Dataset saved to {output_file}")
    
    # Generate some statistics
    dialects = {}
    domains = {}
    lang_pairs = {}
    
    for entry in processed_data:
        # Count dialects
        dialect = entry['dialect']
        dialects[dialect] = dialects.get(dialect, 0) + 1
        
        # Count domains
        domain = entry['domain']
        domains[domain] = domains.get(domain, 0) + 1
        
        # Count language pairs
        pair = f"{entry['source_lang']}-{entry['target_lang']}"
        lang_pairs[pair] = lang_pairs.get(pair, 0) + 1
    
    print("\n=== Dataset Statistics ===")
    print(f"Total entries: {len(processed_data)}")
    print(f"\nDialects: {dict(sorted(dialects.items(), key=lambda x: x[1], reverse=True))}")
    print(f"\nDomains: {dict(sorted(domains.items(), key=lambda x: x[1], reverse=True))}")
    print(f"\nLanguage pairs: {dict(sorted(lang_pairs.items(), key=lambda x: x[1], reverse=True))}")
    
    # Create a smaller sample for testing
    sample_data = processed_data[:500]  # First 500 entries
    sample_file = 'luhya_dataset_sample.json'
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nSample dataset (500 entries) saved to {sample_file}")
    
    return processed_data

if __name__ == "__main__":
    # Install required packages first:
    # pip install datasets pandas
    
    processed_data = process_luhya_dataset()
    print("Dataset preprocessing complete!")