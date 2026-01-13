import os
import json
import pandas as pd
import glob

# Directory with models
models_dir = 'models'

# Find all .json files
json_files = glob.glob(os.path.join(models_dir, '*.onnx.json'))

for json_file in json_files:
    # Load JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Replace empty dicts with None to avoid Parquet issues
    def replace_empty_dicts(obj):
        if isinstance(obj, dict):
            return {k: replace_empty_dicts(v) if v != {} else None for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_empty_dicts(item) for item in obj]
        else:
            return obj
    
    data = replace_empty_dicts(data)
    
    # Convert to DataFrame (single row)
    df = pd.DataFrame([data])
    
    # Save as Parquet
    parquet_file = json_file.replace('.json', '.parquet')
    df.to_parquet(parquet_file, index=False)
    
    print(f"Converted {json_file} to {parquet_file}")

    # Optionally, remove the JSON file
    # os.remove(json_file)