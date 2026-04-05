import json

# Fix Kaggle server files to use 127.0.0.1 instead of localhost for Ollama,
# and ensure ollama serve is completely detached so it doesn't die.

def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace localhost with 127.0.0.1
    content = content.replace("http://localhost:11434", "http://127.0.0.1:11434")

    # In cell 2, let's use nohup to ensure ollama stays alive forever
    # We will replace the subprocess block
    old_subprocess = """ollama_proc = subprocess.Popen(
    ['/usr/local/bin/ollama', 'serve'],
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)"""
    new_subprocess = """os.system('nohup /usr/local/bin/ollama serve > /tmp/ollama.log 2>&1 &')"""
    
    # Actually wait, the notebook has it json encoded with \n
    old_encoded = "        \"ollama_proc = subprocess.Popen(\\n\",\n        \"    ['/usr/local/bin/ollama', 'serve'],\\n\",\n        \"    env=env,\\n\",\n        \"    stdout=subprocess.DEVNULL,\\n\",\n        \"    stderr=subprocess.DEVNULL\\n\",\n        \")\\n\","
    new_encoded = "        \"with open('/tmp/env.sh', 'w') as f:\\n\",\n        \"    f.write('export OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1 CUDA_VISIBLE_DEVICES=0\\\\n')\\n\",\n        \"os.system('source /tmp/env.sh && nohup /usr/local/bin/ollama serve > /tmp/ollama.log 2>&1 &')\\n\","

    if old_encoded in content:
        content = content.replace(old_encoded, new_encoded)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Fixed {path}")

fix_file(r"c:\Users\raj17\Desktop\ClaimGuard AI\ClaimGuard_FINAL_Kaggle.ipynb")
fix_file(r"c:\Users\raj17\Desktop\ClaimGuard AI\build_kaggle_api_server.py")
