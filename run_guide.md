# CLAIM GUARD AI — KAGGLE EXECUTION BRIDGE
## Step-by-Step Run Guide

This system enables the frontend to trigger executing AI analysis workloads on Kaggle's GPU directly via the Kaggle API. The backend orchestrates the push, polling, and retrieval.

---

### Step 1: Install Dependencies
First, install the Python libraries needed for FastAPI to communicate with the Kaggle CLI:

```bash
pip install fastapi uvicorn requests kaggle
```

---

### Step 2: Configure Kaggle API
To allow the local server to trigger notebooks on Kaggle, you must authenticate the `kaggle` Python package.

1. Go to your [Kaggle Account Settings](https://www.kaggle.com/settings).
2. Scroll down to the **API** section and click **"Create New Token"**. This will download a `kaggle.json` file.
3. Move `kaggle.json` to the correct hidden folder for your OS:
   - **Windows:** `C:\Users\YOUR_USERNAME\.kaggle\kaggle.json`
   - **Mac/Linux:** `~/.kaggle/kaggle.json`
4. *(Mac/Linux only)* Make sure the file is secure: `chmod 600 ~/.kaggle/kaggle.json`

Check if it works by opening a terminal and running:
```bash
kaggle datasets list
```

---

### Step 3: Run the Backend
Start the FastAPI server. It acts as the bridge connecting your frontend actions to Kaggle.

```bash
cd "c:\Users\raj17\Desktop\ClaimGuard AI"
uvicorn main:app --reload
```
The server will start at `http://localhost:8000`. 
The `kaggle_bridge.py` file uses your Kaggle credentials to manage jobs.

---

### Step 4: Run the Frontend
Because we bundle the frontend static files via FastAPI, simply go to your browser:

**[http://localhost:8000](http://localhost:8000)**

You can navigate to the Analysis Lab (`/lab`) or the Comparator (`/compare`).

---

### Step 5: How it Works End-to-End

When you click **"Initialize Link"** (Evaluate Claim) or **Submit Simulation**, here is the exact flow:

1. **Upload:** Frontend sends the PDFs to standard `/api/run-kaggle/evaluate` local endpoint.
2. **OCR:** Backend extracts text quickly using local pure Python OCR (or API). 
3. **Trigger:** Backend creates a dynamic Kaggle kernel containing your text embedded inside, and uses `kaggle kernels push` to send it to Kaggle.
4. **Poll UI:** Backend returns a `job_id`. The frontend begins polling `/api/job-status/{job_id}`. You'll see updates like *"Kernel queued on Kaggle GPU..."* and progress bar increments.
5. **Execution:** On Kaggle, the notebook script installs Ollama, evaluates the policy using Llama 3 on a P100 GPU, and writes out an `output.json`.
6. **Retrieval:** The backend automatically recognizes the Kaggle notebook completed (`status == 'complete'`), fetches `output.json`, and saves the final AI outcome.
7. **Display:** The frontend polling receives the result and seamlessly renders the Dashboard.

*Note: Executing on Kaggle directly entails 1-5 minutes of latency for container spin up. Polling status updates are displayed transparently to the user.*

--- 

### Step 6: Debugging

**"Kaggle API unauthorized"**
Ensure that `kaggle.json` is correctly placed and exactly named. No extra characters like `.txt`.

**"Kaggle execution timed out"** 
Your job may have hit the GPU wait queue. The app polls for up to 10 minutes. Go to kaggle.com -> Your Work to see your running kernels and check their logs.

**"UI stuck at 15%"**
Watch your backend FastApi terminal logs. The background thread will print if it hits errors authenticating or pushing to kaggle.
