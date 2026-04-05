"""
ClaimGuard AI — Kaggle Execution Bridge
Triggers Kaggle notebook execution via the Kaggle CLI API,
polls for completion, and fetches results.

Workflow:
  1. Frontend uploads files → Backend does OCR (lightweight API call)
  2. Backend creates a Kaggle kernel script with embedded text (base64)
  3. Pushes kernel via `kaggle kernels push`
  4. Polls `kaggle kernels status` until done
  5. Fetches output via `kaggle kernels output`
  6. Returns parsed JSON to frontend
"""

import os
import json
import time
import uuid
import base64
import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# ---------------------------------------------------------------------------
# In-memory job store (production would use Redis / DB)
# ---------------------------------------------------------------------------
_jobs: Dict[str, Dict] = {}

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KAGGLE_PROJECTS_DIR = os.path.join(BASE_DIR, "kaggle_projects")
KAGGLE_OUTPUT_DIR = os.path.join(BASE_DIR, "kaggle_output")

os.makedirs(KAGGLE_PROJECTS_DIR, exist_ok=True)
os.makedirs(KAGGLE_OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Kaggle Config Helpers
# ---------------------------------------------------------------------------
def get_kaggle_username() -> str:
    """Get Kaggle username from env or ~/.kaggle/kaggle.json"""
    username = os.environ.get("KAGGLE_USERNAME", "")
    if not username:
        kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
        if kaggle_json.exists():
            with open(kaggle_json, "r") as f:
                data = json.load(f)
                username = data.get("username", "")
    return username


def get_kaggle_cmd() -> str:
    """Find Kaggle executable path."""
    cmd = shutil.which("kaggle")
    if cmd: return cmd
    # Try common local bin paths on Windows
    local_scripts = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Python", "Python314", "Scripts", "kaggle.exe")
    if os.path.exists(local_scripts): return local_scripts
    return "kaggle"

KAGGLE_CMD = get_kaggle_cmd()

def is_kaggle_configured() -> bool:
    """Check if Kaggle CLI is available and configured"""
    try:
        result = subprocess.run(
            [KAGGLE_CMD, "--version"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Job Management
# ---------------------------------------------------------------------------
def create_job(operation: str, params: dict = None) -> str:
    job_id = uuid.uuid4().hex[:8]
    _jobs[job_id] = {
        "job_id": job_id,
        "operation": operation,
        "status": "pending",       # pending → running → complete / error
        "progress": 0,
        "steps": [],
        "result": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "params": params or {},
    }
    return job_id


def update_job(job_id: str, **kwargs):
    if job_id in _jobs:
        _jobs[job_id].update(kwargs)
        _jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()


def get_job(job_id: str) -> dict:
    return _jobs.get(job_id, {"error": "Job not found", "status": "unknown"})


def add_step(job_id: str, message: str, progress: int = None):
    if job_id in _jobs:
        _jobs[job_id]["steps"].append({
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        })
        if progress is not None:
            _jobs[job_id]["progress"] = progress
        _jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()


def list_jobs(limit: int = 20) -> list:
    """Return most recent jobs"""
    jobs = sorted(_jobs.values(), key=lambda j: j["created_at"], reverse=True)
    return jobs[:limit]


# ---------------------------------------------------------------------------
# Kernel Script Generation
# ---------------------------------------------------------------------------
def _b64(text: str) -> str:
    """Safely encode text for embedding in Python scripts"""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


_KERNEL_SETUP = r'''#!/usr/bin/env python3
"""ClaimGuard AI — Kaggle Kernel (auto-generated)"""
import os, json, time, base64, subprocess, requests

# ── Install & start Ollama ──
print("⬇️  Installing Ollama...")
os.system("curl -fsSL https://ollama.com/install.sh | sh 2>/dev/null")

print("🚀 Starting Ollama server...")
ollama_env = os.environ.copy()
ollama_env["CUDA_VISIBLE_DEVICES"] = "0"
ollama_env["OLLAMA_NUM_PARALLEL"] = "1"
ollama_env["OLLAMA_MAX_LOADED_MODELS"] = "1"
ollama_env["OLLAMA_HOST"] = "0.0.0.0:11434"

log_file = open("/tmp/ollama_serve.log", "w")
ollama_proc = subprocess.Popen(
    ["/usr/local/bin/ollama", "serve"],
    env=ollama_env,
    stdout=log_file,
    stderr=log_file,
    preexec_fn=os.setpgrp,
)

def _check_ollama():
    try:
        return requests.get("http://127.0.0.1:11434/api/tags", timeout=5).status_code == 200
    except:
        return False

ready = False
for _attempt in range(12):
    if _check_ollama():
        ready = True
        break
    time.sleep(5)

if not ready:
    os.system(
        "CUDA_VISIBLE_DEVICES=0 OLLAMA_NUM_PARALLEL=1 "
        "OLLAMA_MAX_LOADED_MODELS=1 OLLAMA_HOST=0.0.0.0:11434 "
        "nohup /usr/local/bin/ollama serve > /tmp/ollama_serve2.log 2>&1 &"
    )
    time.sleep(10)

os.system("ollama pull llama3:8b")
print("✅ Ollama + Llama3 ready!" if _check_ollama() else "⚠️ Ollama may need retry")

OLLAMA = "http://127.0.0.1:11434/api/generate"

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
    except requests.exceptions.ConnectionError:
        print("🔄 Ollama connection lost. Restarting server...")
        os.system(
            "CUDA_VISIBLE_DEVICES=0 OLLAMA_HOST=0.0.0.0:11434 "
            "nohup /usr/local/bin/ollama serve > /tmp/ollama_retry.log 2>&1 &"
        )
        time.sleep(8)
        try:
            r = requests.post(OLLAMA, json=payload, timeout=300)
            r.raise_for_status()
            return r.json().get("response", "{}")
        except Exception as e2:
            print(f"Ollama error (retry): {e2}")
            return "{}"
    except Exception as e:
        print(f"Ollama error: {e}")
        return "{}"

def b64d(s):
    return base64.b64decode(s).decode("utf-8")

'''


def _generate_evaluate_script(policy_text: str, bill_text: str) -> str:
    return _KERNEL_SETUP + f'''
# ══════════ EVALUATE ══════════
policy_text = b64d("{_b64(policy_text)}")
bill_text   = b64d("{_b64(bill_text)}")

SYS = """You are an Automated Car Insurance Claim Evaluation Engine.
Analyze the policy and bill. Return ONLY this JSON:
{{
  "total_bill_amount": number,
  "total_covered_amount": number,
  "total_not_covered_amount": number,
  "final_payable_by_insurer": number,
  "breakdown": [{{"item":"...","cost":number,"covered":true/false,"payable_amount":number,"reason":"...","category":"repair/part/labor/service"}}],
  "summary": {{"covered_items":[],"not_covered_items":[],"key_reasons":[]}},
  "human_readable_summary": "Insurance will pay: X | You must pay: Y | Main uncovered items: ..."
}}
RULES: Be precise, no text outside JSON, if unclear mark NOT covered."""

raw = call_ollama(f"POLICY:\\n{{policy_text}}\\n\\nBILL:\\n{{bill_text}}", SYS)
try:
    result = json.loads(raw)
except:
    result = {{"error": "JSON parse failed", "raw": raw}}

with open("/kaggle/working/output.json", "w") as f:
    json.dump({{"status": "success", "result": result}}, f, indent=2)
print("✅ Evaluation complete!")
'''


def _generate_simulate_script(policy_text: str, user_query: str) -> str:
    return _KERNEL_SETUP + f'''
# ══════════ SIMULATE ══════════
policy_text = b64d("{_b64(policy_text)}")
user_query  = b64d("{_b64(user_query)}")

# Parse scenario
parse_sys = "Convert user insurance scenario to JSON with keys: treatment, hospital, urgency, input_raw, estimated_cost."
raw_s = call_ollama(user_query, parse_sys)
try:
    scenario = json.loads(raw_s)
except:
    scenario = {{"input_raw": user_query, "hospital": "Unknown", "treatment": "Unknown"}}

# Run elite engine
engine_sys = """You are an Elite AI Risk Analyst and Insurance Claim Auditor.
OUTPUT STRICTLY IN THIS JSON FORMAT:
{{
  "assumptions": ["Assumption: [...] Reason: [...]"],
  "calculation_steps": ["Step 1: ...", "Step 2: ..."],
  "final_payout": "string",
  "deductions": ["deduction list"],
  "risks": ["rejection risks"],
  "hidden_insights": ["insights"],
  "claim_probability": "string",
  "risk_score": "string",
  "coverage_efficiency": "string",
  "future_prediction": "string",
  "optimization_suggestions": ["strategies"]
}}"""
prompt = f"INPUT:\\n1. Scenario:\\n{{json.dumps(scenario, indent=2)}}\\n\\n2. Policy Text:\\n{{policy_text[:3000]}}\\n\\nExecute analysis. Return ONLY JSON."
raw_e = call_ollama(prompt, engine_sys)
try:
    result = json.loads(raw_e)
except:
    result = {{"error": "Parse failed", "raw": raw_e}}

with open("/kaggle/working/output.json", "w") as f:
    json.dump({{"status": "success", "result": result}}, f, indent=2)
print("✅ Simulation complete!")
'''


def _generate_compare_script(policy_texts: List[str], preferences: dict) -> str:
    # Encode each policy text
    encoded_policies = [_b64(t) for t in policy_texts]
    encoded_json = json.dumps(encoded_policies)
    prefs_json = json.dumps(preferences)
    num = len(policy_texts)
    policy_cols = ", ".join([f'"policy_{i+1}": "value"' for i in range(num)])

    return _KERNEL_SETUP + f'''
# ══════════ SMART COMPARE ══════════
import json as _json

encoded_policies = _json.loads('{encoded_json}')
policy_texts = [b64d(e) for e in encoded_policies]
preferences = _json.loads('{prefs_json}')

budget = preferences.get("budget", "")
coverage_type = preferences.get("coverage_type", "")
priority = preferences.get("priority", "balanced")
num = len(policy_texts)

pref_instruction = ""
if budget: pref_instruction += f"User budget range: {{budget}}. "
if coverage_type: pref_instruction += f"Coverage type needed: {{coverage_type}}. "
if priority: pref_instruction += f"User priority: {{priority}}. "

sys_prompt = f"""You are an Elite AI Insurance Policy Advisor and Comparison Engine.
Compare {{num}} insurance policies based on the user's specific needs.

{{pref_instruction}}

SCORING RULES:
- "low_premium": Lower premium = higher score
- "high_coverage": Broader/higher coverage limits = higher score
- "fast_claims": Faster/easier claim process = higher score
- "balanced": Equal weight to all factors

OUTPUT STRICTLY IN THIS EXACT VALID JSON FORMAT:
{{{{
  "policies_count": {{num}},
  "best_policy": {{{{
    "name": "Policy X", "index": 0, "score": 0,
    "why_best": "Detailed explanation"
  }}}},
  "policy_scores": [
    {{{{"policy": "Policy 1", "score": 0, "strengths": ["..."], "weaknesses": ["..."]}}}}
  ],
  "comparison_table": [
    {{{{"feature": "Premium", {policy_cols}, "best": "Policy X"}}}}
  ],
  "pros_cons": {{{{
    "policy_1": {{{{"pros": ["..."], "cons": ["..."]}}}}
  }}}},
  "personalized_suggestion": "Based on user wanting [priority], Policy X is recommended...",
  "risk_warnings": ["Important risk or caveat"],
  "human_readable_summary": "Quick comparison summary"
}}}}

Score each policy out of 100. Include at least 8 comparison features."""

policies_str = ""
for i, text in enumerate(policy_texts):
    policies_str += f"\\n--- POLICY {{i+1}} ---\\n{{text[:3000]}}\\n"

prompt = f"""USER PREFERENCES:
Budget: {{budget if budget else "Not specified"}}
Coverage Type: {{coverage_type if coverage_type else "General"}}
Priority: {{priority if priority else "Balanced"}}

POLICIES TO COMPARE:
{{policies_str}}

Analyze, score, and compare. Return ONLY valid JSON."""

raw = call_ollama(prompt, sys_prompt)
try:
    result = _json.loads(raw)
except:
    result = {{"error": "Failed to parse smart comparison", "raw": raw}}

with open("/kaggle/working/output.json", "w") as f:
    _json.dump({{"status": "success", "result": result}}, f, indent=2)
print("✅ Comparison complete!")
'''


# ---------------------------------------------------------------------------
# Kaggle Kernel Push / Poll / Fetch
# ---------------------------------------------------------------------------
def _create_kernel_project(job_id: str, operation: str, script_content: str) -> str:
    """Create a kernel project directory with metadata + script"""
    username = get_kaggle_username()
    if not username:
        raise RuntimeError("Kaggle username not configured. Set KAGGLE_USERNAME env var or configure ~/.kaggle/kaggle.json")

    slug = f"claimguard-{operation}-{job_id}"
    project_dir = os.path.join(KAGGLE_PROJECTS_DIR, slug)
    os.makedirs(project_dir, exist_ok=True)

    # Write kernel script
    script_path = os.path.join(project_dir, "script.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    # Write metadata
    metadata = {
        "id": f"{username}/{slug}",
        "title": f"ClaimGuard {operation.title()} {job_id}",
        "code_file": "script.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
    }
    with open(os.path.join(project_dir, "kernel-metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    return project_dir, f"{username}/{slug}"


def _push_kernel(project_dir: str) -> subprocess.CompletedProcess:
    """Push kernel to Kaggle for execution"""
    print(f"[Kaggle Bridge] Executing: python -m kaggle.cli kernels push -p {project_dir}")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        ["python", "-m", "kaggle.cli", "kernels", "push", "-p", project_dir],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, env=env
    )


def _check_kernel_status(kernel_slug: str) -> str:
    """Poll kernel status. Returns: queued, running, complete, error, cancelAcknowledged"""
    result = subprocess.run(
        ["python", "-m", "kaggle.cli", "kernels", "status", kernel_slug],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
    )
    output = result.stdout.strip().lower()
    if "complete" in output:
        return "complete"
    elif "error" in output:
        return "error"
    elif "running" in output:
        return "running"
    elif "queued" in output or "pending" in output:
        return "queued"
    elif "cancel" in output:
        return "cancelled"
    return "unknown"


def _fetch_kernel_output(kernel_slug: str, output_dir: str) -> Optional[dict]:
    """Fetch kernel output.json"""
    os.makedirs(output_dir, exist_ok=True)
    print(f"[Kaggle Bridge] Fetching output: python -m kaggle.cli kernels output {kernel_slug} -p {output_dir}")
    result = subprocess.run(
        ["python", "-m", "kaggle.cli", "kernels", "output", kernel_slug, "-p", output_dir],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60
    )
    if result.returncode != 0:
        print(f"[Kaggle Bridge ERROR] Fetch failed: {result.stderr.strip() or result.stdout.strip()}")
    output_file = os.path.join(output_dir, "output.json")
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            return json.load(f)
    print(f"[Kaggle Bridge ERROR] output.json not found in {output_dir}")
    return None


# ---------------------------------------------------------------------------
# Background Execution Thread
# ---------------------------------------------------------------------------
def _run_kaggle_job(job_id: str, operation: str, script_content: str):
    """Background thread that pushes, polls, and fetches a Kaggle kernel"""
    try:
        update_job(job_id, status="running")
        add_step(job_id, "Preparing Kaggle kernel...", progress=5)

        # Create project
        project_dir, kernel_slug = _create_kernel_project(job_id, operation, script_content)
        add_step(job_id, "Kernel project created.", progress=10)

        # Push
        add_step(job_id, "Pushing kernel to Kaggle...", progress=15)
        push_result = _push_kernel(project_dir)
        if push_result.returncode != 0:
            err_msg = push_result.stderr.strip() or push_result.stdout.strip()
            raise RuntimeError(f"Kaggle push failed: {err_msg}")
        add_step(job_id, "Kernel queued on Kaggle GPU.", progress=20)

        # Poll for completion (max 10 minutes)
        max_wait = 600
        poll_interval = 10
        elapsed = 0
        while elapsed < max_wait:
            status = _check_kernel_status(kernel_slug)
            if status == "complete":
                add_step(job_id, "Kernel execution complete!", progress=80)
                break
            elif status == "error":
                raise RuntimeError("Kaggle kernel execution failed.")
            elif status == "cancelled":
                raise RuntimeError("Kaggle kernel was cancelled.")
            else:
                # Gradually increase progress during polling
                poll_progress = min(75, 20 + int((elapsed / max_wait) * 55))
                add_step(job_id, f"Kernel status: {status}... ({elapsed}s elapsed)", progress=poll_progress)
            time.sleep(poll_interval)
            elapsed += poll_interval

        if elapsed >= max_wait:
            raise RuntimeError("Kaggle execution timed out (10 min limit).")

        # Fetch output
        add_step(job_id, "Fetching results from Kaggle...", progress=85)
        output_dir = os.path.join(KAGGLE_OUTPUT_DIR, job_id)
        output_data = _fetch_kernel_output(kernel_slug, output_dir)

        if not output_data:
            raise RuntimeError("No output.json found in kernel output.")

        add_step(job_id, "Results received successfully!", progress=100)
        update_job(job_id, status="complete", progress=100, result=output_data)

        # Cleanup project dir
        try:
            shutil.rmtree(project_dir, ignore_errors=True)
        except:
            pass

    except Exception as e:
        update_job(job_id, status="error", error=str(e))
        add_step(job_id, f"Error: {str(e)}", progress=0)


# ---------------------------------------------------------------------------
# Public API — Launch Kaggle Jobs
# ---------------------------------------------------------------------------
def launch_kaggle_evaluate(policy_text: str, bill_text: str) -> str:
    """Launch a Kaggle evaluation job. Returns job_id."""
    job_id = create_job("evaluate", {"has_policy": bool(policy_text), "has_bill": bool(bill_text)})
    script = _generate_evaluate_script(policy_text, bill_text)
    thread = threading.Thread(target=_run_kaggle_job, args=(job_id, "evaluate", script), daemon=True)
    thread.start()
    return job_id


def launch_kaggle_simulate(policy_text: str, user_query: str) -> str:
    """Launch a Kaggle simulation job. Returns job_id."""
    job_id = create_job("simulate", {"query": user_query[:100]})
    script = _generate_simulate_script(policy_text, user_query)
    thread = threading.Thread(target=_run_kaggle_job, args=(job_id, "simulate", script), daemon=True)
    thread.start()
    return job_id


def launch_kaggle_compare(policy_texts: List[str], preferences: dict) -> str:
    """Launch a Kaggle comparison job. Returns job_id."""
    job_id = create_job("compare", {"num_policies": len(policy_texts), "priority": preferences.get("priority", "balanced")})
    script = _generate_compare_script(policy_texts, preferences)
    thread = threading.Thread(target=_run_kaggle_job, args=(job_id, "compare", script), daemon=True)
    thread.start()
    return job_id
