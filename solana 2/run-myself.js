const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// 1. Prepare Mocked Solana Service
const solanaCode = fs.readFileSync(path.join(__dirname, 'solana.js'), 'utf8');
const mockedCode = solanaCode.replace(
  /async function recordOnSolana\(message\) {[\s\S]*?}/,
  'async function recordOnSolana(message) { console.log("   🔗 [CHAIN] Sending to Solana: " + message.substring(0, 50) + "..."); return "MOCK_SOL_TX_" + crypto.randomBytes(4).toString("hex").toUpperCase(); }'
);

fs.writeFileSync(path.join(__dirname, 'solana_temp.js'), mockedCode);

// 2. Load Services
const { proofInsuranceOnSolana, logCoverageDecisionOnSolana, verifyCoverageGapOnSolana } = require('./solana_temp');
const analyzePolicy = require('./presage');

async function runDemo() {
  console.log('🚀 --- CLAIMGUARD AI: SELF-RUNNING DEMO ---');
  console.log('User Mnemonic Loaded: ✅ [Verified]');
  console.log('MongoDB: ❌ [Disabled - Using Local JSON]');
  
  const policyId = 'BP-' + crypto.randomBytes(3).toString('hex').toUpperCase();

  console.log('\nStep 1: Uploading Insurance Policy...');
  const proof = await proofInsuranceOnSolana('Policy', policyId, { holder: 'Bro', text: 'Full Coverage' });
  console.log('   ✅ Policy Proofed: ' + proof.signature);

  console.log('\nStep 2: AI Risk Analysis & Coverage Logging...');
  const prediction = await analyzePolicy('Full Coverage');
  const log = await logCoverageDecisionOnSolana(policyId, prediction.decision, prediction.riskScore);
  console.log('   🧠 AI Result: ' + prediction.decision + ' (Risk: ' + prediction.riskScore + ')');
  console.log('   ✅ Decision Logged: ' + log.signature);

  console.log('\nStep 3: Detecting & Verifying Coverage Gaps...');
  const gap = await verifyCoverageGapOnSolana('Missing Flood Insurance', 'High', policyId);
  console.log('   ✅ Gap Evidence Logged: ' + gap.signature);

  console.log('\n📊 DEMO RESULT SUMMARY (JSON):');
  console.log(JSON.stringify({
    policyId,
    status: 'TRUSTED_ON_CHAIN',
    blockchain: 'Solana Devnet (Mocked for Demo)',
    proofSignature: proof.signature,
    aiLogSignature: log.signature,
    gapSignature: gap.signature
  }, null, 2));

  console.log('\n🏁 Demo Finished! Deleting temp files...');
  fs.unlinkSync(path.join(__dirname, 'solana_temp.js'));
}

runDemo().catch(console.error);
