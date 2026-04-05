const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
require('dotenv').config();

const analyzePolicy = require('./presage');
const recordPolicyOnAlgorand = require('./Algorande');
const { 
  proofInsuranceOnSolana, 
  logCoverageDecisionOnSolana, 
  verifyCoverageGapOnSolana 
} = require('./solana');

const app = express();
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));

const DB_FILE = path.join(__dirname, 'db.json');

/**
 * Helper to read local JSON database
 */
function readDB() {
  const data = fs.readFileSync(DB_FILE, 'utf8');
  return JSON.parse(data);
}

/**
 * Helper to write to local JSON database
 */
function writeDB(data) {
  fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
}

/**
 * 1️⃣ Upload Policy + AI + Algorand + Solana Insurance Proofing & Coverage Logging
 */
app.post('/upload-policy', async (req, res) => {
  try {
    const { holder, policyText, senderMnemonic } = req.body;
    const db = readDB();

    // A. Save Locally
    const policy = {
      id: crypto.randomUUID(),
      holder,
      policyText,
      predictions: {},
      createdAt: new Date().toISOString()
    };

    // B. Analyze policy with AI (Presage)
    const prediction = await analyzePolicy(policyText);
    policy.predictions = prediction;

    // C. Solana: Insurance Proofing (Immutable Record of Policy)
    const solanaProof = await proofInsuranceOnSolana('Policy', policy.id, { holder, policyText });
    policy.solanaTxSignature = solanaProof.signature;

    // D. Solana: Coverage Logging (AI Decision Transparency)
    const solanaLog = await logCoverageDecisionOnSolana(
      policy.id, 
      prediction.decision || 'Analyzed', 
      prediction.riskScore || 'Low'
    );

    // E. Algorand: Backward Compatibility
    let algoTxId = null;
    if (senderMnemonic) {
      algoTxId = await recordPolicyOnAlgorand(senderMnemonic, policy.id);
    }

    db.policies.push(policy);
    writeDB(db);

    res.json({ 
      message: "Policy fully proofed on Solana and Algorand!", 
      policy, 
      solanaProofTx: solanaProof.signature,
      solanaLogTx: solanaLog.signature,
      algoTxId 
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

/**
 * 2️⃣ Process Claim + Solana Insurance Proofing (Claims)
 */
app.post('/process-claim', async (req, res) => {
  try {
    const { policyId, claimDetails } = req.body;
    const db = readDB();

    // A. Create Claim
    const claim = {
      id: crypto.randomUUID(),
      policyId,
      claimDetails,
      status: 'Pending',
      createdAt: new Date().toISOString()
    };

    // B. Solana: Insurance Proofing (Proof of Claim Submission)
    const solanaProof = await proofInsuranceOnSolana('Claim', claim.id, { policyId, claimDetails });
    claim.solanaTxSignature = solanaProof.signature;
    claim.hash = solanaProof.hash;

    db.claims.push(claim);
    writeDB(db);

    res.json({ message: "Claim proofed on Solana!", claim, txId: solanaProof.signature });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * 3️⃣ Verify Coverage Gap + Solana Gap Verification Logging
 */
app.post('/verify-gap', async (req, res) => {
  try {
    const { policyId, gapType, severity } = req.body;
    const db = readDB();

    // A. Solana: Gap Verification (Tamper-proof audit trail)
    const solanaGapLog = await verifyCoverageGapOnSolana(gapType, severity, policyId);

    // B. Save local audit record
    const gap = {
      id: crypto.randomUUID(),
      policyId,
      gapType,
      severity,
      verificationHash: solanaGapLog.hash,
      solanaTxSignature: solanaGapLog.signature,
      verifiedAt: new Date().toISOString()
    };

    db.gaps.push(gap);
    writeDB(db);

    res.json({ message: "Coverage Gap verified on Solana!", gap, txId: solanaGapLog.signature });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * Root Redirect for Easy Access (Removed to allow static index.html)
 */
// app.get('/', (req, res) => {
//   res.redirect('/data');
// });

/**
 * Get all Data
 */
app.get('/data', (req, res) => {
  res.json(readDB());
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`🚀 ClaimGuard AI Server (Local Storage) running on port ${PORT}`));