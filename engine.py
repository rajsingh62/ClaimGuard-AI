import os
import io
import re
import time
import json
import base64
import requests
from pdf2image import convert_from_path

OCR_SPACE_API_KEY = "K87093604688957"
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"

# ===========================
# MODULE 1: OCR TEXT EXTRACTION
# ===========================
def extract_text_from_file(file_path):
    if not file_path: return ""
    file_path_lower = file_path.lower()
    
    if file_path_lower.endswith(('.png', '.jpg', '.jpeg')):
        print(f"Processing Image '{file_path}' via OCR.space API...")
        with open(file_path, "rb") as f:
            base64_encoded = base64.b64encode(f.read()).decode('utf-8')
        payload = {
            'apikey': OCR_SPACE_API_KEY,
            'base64Image': f"data:image/jpeg;base64,{base64_encoded}",
            'language': 'eng',
            'isOverlayRequired': False
        }
        try:
            response = requests.post('https://api.ocr.space/parse/image', data=payload)
            result = response.json()
            if result.get('IsErroredOnProcessing') == False:
                return result['ParsedResults'][0]['ParsedText']
            else:
                print(f"OCR Image Error: {result.get('ErrorMessage')}")
                return ""
        except Exception as e:
            print(f"Image OCR Request failed: {e}")
            return ""
            
    elif file_path_lower.endswith('.pdf'):
        print(f"Extracting text from PDF '{file_path}'...")
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n\n"
            
            if len(text.strip()) > 30:
                return text
            print(f"PDF seems to be scanned or empty. Falling back to OCR...")
        except Exception as e:
            print(f"PyPDF2 error: {e}. Trying OCR...")

        print(f"Converting PDF '{file_path}' to images for OCR...")
        try:
            images = convert_from_path(file_path, dpi=100) 
            full_text = ""
            for i, img in enumerate(images):
                print(f"Processing PDF Page {i+1} via OCR...")
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=40) 
                base64_encoded = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                payload = {
                    'apikey': OCR_SPACE_API_KEY,
                    'base64Image': f"data:image/jpeg;base64,{base64_encoded}",
                    'language': 'eng',
                    'isOverlayRequired': False
                }
                try:
                    response = requests.post('https://api.ocr.space/parse/image', data=payload)
                    result = response.json()
                    if result.get('IsErroredOnProcessing') == False:
                        parsed_text = result['ParsedResults'][0]['ParsedText']
                        full_text += parsed_text + "\n\n"
                    else:
                        print(f"API Error on Page {i+1}: {result.get('ErrorMessage')}")
                except Exception as e:
                    print(f"Request failed for Page {i+1}: {e}")
                time.sleep(1)
            return full_text
        except Exception as e:
            print(f"PDF processing error (requires poppler for OCR): {e}")
            return ""
    else:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            return "UNSUPPORTED FILE FORMAT"

# ===========================
# MODULE 2: OLLAMA CALLER
# ===========================
def call_ollama(prompt, system_prompt, json_format=True):
    payload = {
        "model": "llama3:8b",
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "format": "json" if json_format else "",
        "options": {
            "num_gpu": 99,
            "num_predict": -1
        }
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=300)
        response.raise_for_status()
        return response.json().get('response', '{}')
    except requests.exceptions.ConnectionError:
        print("🔄 Ollama connection lost. Attempting to restart server...")
        import os, time, subprocess
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        try:
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=300)
            response.raise_for_status()
            return response.json().get('response', '{}')
        except Exception as e2:
            print(f"Ollama inference error (retry): {e2}")
            return "{}"
    except Exception as e:
        print(f"Ollama inference error: {e}")
        return "{}"

# ===========================
# MODULE 3: BILL EVALUATION ENGINE (from Notebook v10)
# ===========================
def car_claim_evaluator(policy_text, bill_text):
    print("Analyzing Scanned Bill against Scanned Policy Rules...")
    sys_prompt = """You are an Automated Car Insurance Claim Evaluation Engine.

Your task is to analyze:
1. Insurance Policy Document
2. Damage Bill / Repair Invoice

You MUST automatically determine:
- What is covered
- What is NOT covered
- Final payable amount by the insurance company

You DO NOT ask the user questions.
You COMPLETE the full evaluation in one go.

FINAL OUTPUT (VERY IMPORTANT)
Return ONLY this JSON:
{
  "total_bill_amount": number,
  "total_covered_amount": number,
  "total_not_covered_amount": number,
  "final_payable_by_insurer": number,
  "breakdown": [{"item": "...", "cost": number, "covered": true/false, "payable_amount": number, "reason": "short explanation", "category": "repair/part/labor/service"}],
  "summary": { "covered_items": [], "not_covered_items": [], "key_reasons": [] },
  "human_readable_summary": "Insurance will pay: XXXXX | You must pay: XXXXX | Main uncovered items: ..."
}

RULES: Be precise, no text outside JSON, no assumptions beyond policy, if unclear mark NOT covered."""

    prompt = f"""
INPUT STRUCTURE

POLICY:
{policy_text}

BILL:
{bill_text}
"""
    raw_json = call_ollama(prompt, sys_prompt)
    try:
        data = json.loads(raw_json)
        return data
    except Exception as e:
        return {"error": "Failed to parse JSON. Try Again.", "raw": raw_json}

# ===========================
# MODULE 4: NLP TEXT PROCESSING (from Notebook 1)
# ===========================
def process_text(raw_text):
    cleaned = re.sub(r'\s+', ' ', raw_text).strip()
    words = cleaned.split()
    chunk_size = 300
    overlap = 50
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size - overlap)]

    categories = {
        "waiting_period": ["waiting", "days from inception", "delay"],
        "exclusion": ["excluded", "not covered", "exclusion", "except"],
        "co_payment": ["co-pay", "copayment", "co payment", "%"],
        "room_rent": ["room rent", "bed charges", "icu"],
        "sub_limit": ["sub-limit", "capped at", "maximum limit"],
        "network_rule": ["network", "empanelled", "hospital"]
    }
    
    structured_clauses = []
    for chunk in chunks:
        cls_tags = []
        lower_chunk = chunk.lower()
        for cat, keywords in categories.items():
            if any(k in lower_chunk for k in keywords):
                cls_tags.append(cat)
        structured_clauses.append({
            "text": chunk,
            "categories": cls_tags if cls_tags else ["general"]
        })
    return structured_clauses

# ===========================
# MODULE 5: SCENARIO SIMULATOR (from Notebook 1)
# ===========================
def parse_scenario(user_query):
    sys_prompt = "Convert user insurance scenario to structured JSON with keys: treatment, hospital, urgency, input_raw, estimated_cost."
    response = call_ollama(user_query, system_prompt=sys_prompt)
    try:
        return json.loads(response)
    except:
        return {"input_raw": user_query, "hospital": "Unknown", "treatment": "Unknown"}

def elite_decision_engine(scenario_json, policy_text):
    sys_prompt = """You are an Elite AI Risk Analyst, Financial Engineer, and Insurance Claim Auditor.
You MUST:
1. Infer missing data with assumptions
2. Perform calculations step-by-step
3. Reveal hidden risks and loopholes
4. Predict future policy states

OUTPUT STRICTLY IN THIS EXACT VALID JSON FORMAT:
{
  "assumptions": ["Assumption Made: [..] Reason: [..]"],
  "calculation_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ...", "Step 4: ..."],
  "final_payout": "string",
  "deductions": ["List of specific deductions"],
  "risks": ["Top 5 rejection risks"],
  "hidden_insights": ["Insights NOT explicitly asked"],
  "claim_probability": "string",
  "risk_score": "string",
  "coverage_efficiency": "string",
  "future_prediction": "string",
  "optimization_suggestions": ["Actionable strategies"]
}"""

    prompt = f"""
INPUT RECEIVED:
1. User Scenario & Partial Financials:
{json.dumps(scenario_json, indent=2)}

2. Policy Document Text:
{policy_text[:3000]}

Execute the Elite Decision Engine protocol now. Return ONLY valid JSON.
"""
    try:
        resp = call_ollama(prompt, system_prompt=sys_prompt, json_format=True)
        return json.loads(resp)
    except Exception as e:
        print(f"Engine Execution Failed: {e}")
        return {"error": str(e)}

def run_simulation(policy_text, user_query):
    scenario = parse_scenario(user_query)
    result = elite_decision_engine(scenario, policy_text)
    return result

# ===========================
# MODULE 6: POLICY COMPARISON ENGINE (ENHANCED)
# ===========================
def compare_policies(policy_texts, comparison_params=""):
    sys_prompt = """You are an Expert Insurance Policy Comparison Engine.
Compare the provided insurance policies and produce a detailed side-by-side analysis.

OUTPUT STRICTLY IN THIS EXACT VALID JSON FORMAT:
{
  "policies_count": number,
  "comparison_parameters": ["param1", "param2", ...],
  "comparison_table": [
    {
      "parameter": "Coverage Limit",
      "policy_1": "value",
      "policy_2": "value",
      "winner": "Policy 1" or "Policy 2" or "Tie",
      "reason": "why"
    }
  ],
  "overall_winner": "Policy 1" or "Policy 2",
  "overall_reason": "Detailed reason",
  "risk_analysis": {
    "policy_1_risks": ["risk1", "risk2"],
    "policy_2_risks": ["risk1", "risk2"]
  },
  "recommendation": "Which policy to choose and why",
  "human_readable_summary": "Policy 1 vs Policy 2: ..."
}"""

    policies_str = ""
    for i, text in enumerate(policy_texts):
        policies_str += f"\n--- POLICY {i+1} ---\n{text[:3000]}\n"

    prompt = f"""
COMPARISON REQUEST:
User Parameters: {comparison_params if comparison_params else "Compare all aspects: coverage, deductibles, exclusions, premiums, limits, special conditions"}

{policies_str}

Analyze and compare these policies exhaustively. Return ONLY valid JSON.
"""
    raw_json = call_ollama(prompt, sys_prompt)
    try:
        return json.loads(raw_json)
    except:
        return {"error": "Failed to parse comparison", "raw": raw_json}


def smart_compare_policies(policy_texts, user_preferences=None):
    """Enhanced comparison that factors in user budget, coverage type, and priority."""
    prefs = user_preferences or {}
    budget = prefs.get("budget", "")
    coverage_type = prefs.get("coverage_type", "")
    priority = prefs.get("priority", "balanced")

    pref_instruction = ""
    if budget:
        pref_instruction += f"User budget range: {budget}. "
    if coverage_type:
        pref_instruction += f"Coverage type needed: {coverage_type}. "
    if priority:
        pref_instruction += f"User priority: {priority}. "

    num = len(policy_texts)
    policy_cols = ", ".join([f'"policy_{i+1}": "value"' for i in range(num)])

    sys_prompt = f"""You are an Elite AI Insurance Policy Advisor and Comparison Engine.
You MUST compare {num} insurance policies based on the user's specific needs and preferences.

{pref_instruction}

SCORING RULES (apply based on user priority):
- "low_premium": Lower premium = higher score
- "high_coverage": Broader/higher coverage limits = higher score
- "fast_claims": Faster/easier claim process = higher score
- "balanced": Equal weight to all factors

OUTPUT STRICTLY IN THIS EXACT VALID JSON FORMAT:
{{
  "policies_count": {num},
  "best_policy": {{
    "name": "Policy X",
    "index": number,
    "score": number,
    "why_best": "Detailed explanation why this is the best choice for this user"
  }},
  "policy_scores": [
    {{"policy": "Policy 1", "score": number, "strengths": ["..."], "weaknesses": ["..."]}}
  ],
  "comparison_table": [
    {{
      "feature": "Premium",
      {policy_cols},
      "best": "Policy X"
    }}
  ],
  "pros_cons": {{
    "policy_1": {{"pros": ["..."], "cons": ["..."]}},
    "policy_2": {{"pros": ["..."], "cons": ["..."]}}
  }},
  "personalized_suggestion": "Based on the user wanting [priority], Policy X is recommended because...",
  "risk_warnings": ["Important risk or caveat"],
  "human_readable_summary": "Quick comparison summary"
}}

IMPORTANT:
- Score each policy out of 100
- Be specific with numbers and amounts
- Include at least 8 comparison features
- Pros/cons must be actionable and specific
"""

    policies_str = ""
    for i, text in enumerate(policy_texts):
        policies_str += f"\n--- POLICY {i+1} ---\n{text[:3000]}\n"

    prompt = f"""
USER PREFERENCES:
Budget: {budget if budget else "Not specified"}
Coverage Type: {coverage_type if coverage_type else "General"}
Priority: {priority if priority else "Balanced"}

POLICIES TO COMPARE:
{policies_str}

Analyze, score, and compare. Return ONLY valid JSON.
"""
    raw_json = call_ollama(prompt, sys_prompt)
    try:
        return json.loads(raw_json)
    except:
        return {"error": "Failed to parse smart comparison", "raw": raw_json}

