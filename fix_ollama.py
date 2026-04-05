import json
import os

path1 = r"c:\Users\raj17\Desktop\ClaimGuard AI\ClaimGuard_FINAL_Kaggle.ipynb"
with open(path1, "r", encoding="utf-8") as f:
    content = f.read()

# Replace environment variables to increase stability
content = content.replace("env['OLLAMA_NUM_PARALLEL'] = '4'", "env['OLLAMA_NUM_PARALLEL'] = '1'")
content = content.replace("env['OLLAMA_MAX_LOADED_MODELS'] = '2'", "env['OLLAMA_MAX_LOADED_MODELS'] = '1'")

# If Ollama continues to crash, maybe it's the timeout. Let's also increase ollama start timeout wait.
content = content.replace("time.sleep(12)", "time.sleep(15)")

with open(path1, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Updated {path1}")

# Let's also apply to build_kaggle_api_server.py
path2 = r"c:\Users\raj17\Desktop\ClaimGuard AI\build_kaggle_api_server.py"
with open(path2, "r", encoding="utf-8") as f:
    content2 = f.read()

content2 = content2.replace("env['OLLAMA_NUM_PARALLEL'] = '4'", "env['OLLAMA_NUM_PARALLEL'] = '1'")
content2 = content2.replace("env['OLLAMA_MAX_LOADED_MODELS'] = '2'", "env['OLLAMA_MAX_LOADED_MODELS'] = '1'")

with open(path2, "w", encoding="utf-8") as f:
    f.write(content2)

print(f"Updated {path2}")
