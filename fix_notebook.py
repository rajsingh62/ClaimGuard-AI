import json

def fix_notebook(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for cell in data['cells']:
        if cell['cell_type'] == 'code':
            new_source = []
            for line in cell['source']:
                line = line.replace('from datetime import datetime\\n', 'from datetime import datetime, timezone\\n')
                line = line.replace('datetime.utcnow().isoformat()', 'datetime.now(timezone.utc).isoformat()')
                
                # Replace the Popen block with nohup
                if "subprocess.Popen(" in line:
                    line = "os.system('nohup ollama serve > /tmp/ollama.log 2>&1 &')\\n# " + line
                
                new_source.append(line)
            cell['source'] = new_source

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
fix_notebook('ClaimGuard_FINAL_Kaggle.ipynb')
fix_notebook('ClaimGuard_AI_Kaggle_API_Server.ipynb')
print("Notebooks updated successfully!")
