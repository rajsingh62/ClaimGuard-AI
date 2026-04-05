import json
import re

files = ["ClaimGuard_FINAL_Kaggle.ipynb", "ClaimGuard_AI_Kaggle_API_Server.ipynb"]

for fname in files:
    try:
        with open(fname, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for cell in data.get("cells", []):
            if cell["cell_type"] == "code":
                new_source = []
                # Simple line processing
                for i, line in enumerate(cell["source"]):
                    # Fix timezone import
                    if line == "from datetime import datetime\\n":
                        line = "from datetime import datetime, timezone\\n"
                    elif line == "from datetime import datetime":
                        line = "from datetime import datetime, timezone"
                        
                    # Fix datetime.now(timezone.utc) if someone had it without importing timezone
                    # It was already replaced in my previous fix.
                    
                    # Fix Ollama Popen
                    line = line.replace("stdout=subprocess.DEVNULL", "stdout=subprocess.DEVNULL") # just in case
                    
                    new_source.append(line)
                    
                # Fix the Ollama start command using string replacement on whole cell text
                cell_text = "".join(new_source)
                
                # If timezone is still not imported but datetime.now(timezone.utc) is used
                if "timezone.utc" in cell_text and "from datetime import datetime, timezone" not in cell_text:
                    cell_text = cell_text.replace("from datetime import datetime\\n", "from datetime import datetime, timezone\\n")
                    cell_text = cell_text.replace("from datetime import datetime", "from datetime import datetime, timezone")

                # Replace Popen with nohup
                popen_pattern = r"ollama_process = subprocess\.Popen\([^)]+\)"
                popen_pattern2 = r"ollama_proc = subprocess\.Popen\([^)]+\)"
                
                if "subprocess.Popen" in cell_text and "/usr/local/bin/ollama" in cell_text:
                    if "ollama_proc =" in cell_text:
                        import_part = "import os, subprocess, time, requests\n"
                        # We will replace the whole block
                        block = '''ollama_proc = subprocess.Popen(
    ['/usr/local/bin/ollama', 'serve'],
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)'''
                        block_pipe = '''ollama_proc = subprocess.Popen(
    ['/usr/local/bin/ollama', 'serve'],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)'''
                        cell_text = cell_text.replace(block, 'os.system("nohup ollama serve >/dev/null 2>&1 &")')
                        cell_text = cell_text.replace(block_pipe, 'os.system("nohup ollama serve >/dev/null 2>&1 &")')
                    if "ollama_process =" in cell_text:
                        block2 = '''ollama_process = subprocess.Popen(
    ['/usr/local/bin/ollama', 'serve'],
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)'''
                        block2_pipe = '''ollama_process = subprocess.Popen(
    ['/usr/local/bin/ollama', 'serve'],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)'''
                        cell_text = cell_text.replace(block2, 'os.system("nohup ollama serve >/dev/null 2>&1 &")')
                        cell_text = cell_text.replace(block2_pipe, 'os.system("nohup ollama serve >/dev/null 2>&1 &")')

                # Re-split by lines, keeping trailing newlines
                lines = []
                import io
                buf = io.StringIO(cell_text)
                while True:
                    line = buf.readline()
                    if not line: break
                    lines.append(line)
                
                cell["source"] = lines
                
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Fixed {fname}")
    except Exception as e:
        print(f"Failed {fname}: {e}")
