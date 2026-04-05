import json
import os

path1 = r"c:\Users\raj17\Desktop\ClaimGuard AI\ClaimGuard_FINAL_Kaggle.ipynb"
with open(path1, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('"from datetime import datetime\\n"', '"from datetime import datetime, timezone\\n"')

with open(path1, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Updated {path1}")
