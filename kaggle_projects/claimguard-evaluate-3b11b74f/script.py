#!/usr/bin/env python3
"""ClaimGuard AI — Kaggle Kernel (auto-generated)"""
import os, json, time, base64, subprocess, requests

# ── Install & start Ollama ──
print("⬇️  Installing Ollama...")
os.system("curl -fsSL https://ollama.com/install.sh | sh 2>/dev/null")

env = os.environ.copy()
env["CUDA_VISIBLE_DEVICES"] = "0"
env["OLLAMA_NUM_PARALLEL"] = "4"
ollama_proc = subprocess.Popen(
    ["/usr/local/bin/ollama", "serve"],
    env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
time.sleep(12)
os.system("ollama pull llama3:8b")
print("✅ Ollama + Llama3 ready!")

OLLAMA = "http://localhost:11434/api/generate"

def call_ollama(prompt, system_prompt, json_format=True):
    payload = {
        "model": "llama3:8b",
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {"num_gpu": 99, "num_predict": -1},
    }
    if json_format:
        payload["format"] = "json"
    try:
        r = requests.post(OLLAMA, json=payload, timeout=300)
        r.raise_for_status()
        return r.json().get("response", "{}")
    except Exception as e:
        print(f"Ollama error: {e}")
        return "{}"

def b64d(s):
    return base64.b64decode(s).decode("utf-8")


# ══════════ EVALUATE ══════════
policy_text = b64d("QVVUTyBJTlNVUkFOQ0UgUE9MSUNZIERPQ1VNRU5UCkNvdmVyYWdlIExpbWl0OiAkNTAsMDAwCkRlZHVjdGlibGU6ICQ1MDAKQ292ZXJlZCBJdGVtczogQm9keSBkYW1hZ2UsIHBhcnRzIHJlcGxhY2VtZW50LCBPRU0gc3RhbmRhcmQuCk5vdCBDb3ZlcmVkOiBHZW5lcmFsIG1haW50ZW5hbmNlLCBvaWwgY2hhbmdlcy4=")
bill_text   = b64d("QVVUTyBSRVBBSVIgSU5WT0lDRQoxLiBGcm9udCBCdW1wZXIgUmVwbGFjZW1lbnQgOiAkMSwyMDAgKFBhcnQpCjIuIExhYm9yICgzIGhvdXJzKSA6ICQ0NTAgKExhYm9yKQozLiBQYWludCBzY3JhdGNoIGZpbGwgOiAkMzAwIChQYWludCkKVG90YWwgRHVlOiAkMSw5NTA=")

SYS = """You are an Automated Car Insurance Claim Evaluation Engine.
Analyze the policy and bill. Return ONLY this JSON:
{
  "total_bill_amount": number,
  "total_covered_amount": number,
  "total_not_covered_amount": number,
  "final_payable_by_insurer": number,
  "breakdown": [{"item":"...","cost":number,"covered":true/false,"payable_amount":number,"reason":"...","category":"repair/part/labor/service"}],
  "summary": {"covered_items":[],"not_covered_items":[],"key_reasons":[]},
  "human_readable_summary": "Insurance will pay: X | You must pay: Y | Main uncovered items: ..."
}
RULES: Be precise, no text outside JSON, if unclear mark NOT covered."""

raw = call_ollama(f"POLICY:\n{policy_text}\n\nBILL:\n{bill_text}", SYS)
try:
    result = json.loads(raw)
except:
    result = {"error": "JSON parse failed", "raw": raw}

with open("/kaggle/working/output.json", "w") as f:
    json.dump({"success": True, "operation": "evaluate", "result": result}, f, indent=2)
print("✅ Evaluation complete!")
