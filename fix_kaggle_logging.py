import json

notebook_path = "ClaimGuard_FINAL_Kaggle.ipynb"

try:
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
        
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            if "from pyngrok import ngrok" in source:
                if "logging.getLogger('pyngrok')" not in source:
                    # Let's add the logging disabling lines
                    lines = cell['source']
                    new_lines = []
                    for line in lines:
                        new_lines.append(line)
                        if "import logging" in line:
                            pass
                        if "logging.getLogger('werkzeug').setLevel(logging.ERROR)" in line:
                            new_lines.append("logging.getLogger('pyngrok').setLevel(logging.ERROR)\n")
                    cell['source'] = new_lines
                    
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook patched pyngrok successfully!")

except Exception as e:
    print(f"Error: {e}")
