import json

notebook_path = "ClaimGuard_AI_Kaggle_API_Server.ipynb"

try:
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
        
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            if "from flask import Flask" in source and "app = Flask(__name__)" in source:
                if "logging.getLogger('werkzeug')" not in source:
                    lines = cell['source']
                    new_lines = []
                    for line in lines:
                        new_lines.append(line)
                        if "app = Flask(__name__)" in line:
                            new_lines.append("import logging\n")
                            new_lines.append("logging.getLogger('werkzeug').setLevel(logging.ERROR)\n")
                            new_lines.append("logging.getLogger('pyngrok').setLevel(logging.ERROR)\n")
                            new_lines.append("os.environ['WERKZEUG_RUN_MAIN'] = 'true'\n")
                    cell['source'] = new_lines
                    
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook API Server patched successfully!")

except Exception as e:
    print(f"Error: {e}")
