const { Connection, LAMPORTS_PER_SOL } = require('@solana/web3.js');
const bip39 = require('bip39');
const { derivePath } = require('ed25519-hd-key');
const { Keypair } = require('@solana/web3.js');
const { 
  proofInsuranceOnSolana, 
  logCoverageDecisionOnSolana, 
  verifyCoverageGapOnSolana 
} = require('./solana');
require('dotenv').config();

// Disable TLS cert checks for devnet
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

async function runSelfTest() {
  console.log("[START] ClaimGuard AI Solana Self-Test...");

  // Use the same mnemonic-derived keypair as the main app
  const mnemonic = process.env.SOLANA_MNEMONIC;
  if (!mnemonic) {
    console.log("[ERROR] SOLANA_MNEMONIC not set in .env");
    return;
  }

  const seed = bip39.mnemonicToSeedSync(mnemonic);
  const path = "m/44'/501'/0'/0'";
  const derivedSeed = derivePath(path, seed.toString('hex')).key;
  const keypair = Keypair.fromSeed(derivedSeed);
  const publicKey = keypair.publicKey.toBase58();

  console.log(`[KEY] Using wallet: ${publicKey}`);

  // Check balance
  const connection = new Connection('https://api.devnet.solana.com', 'confirmed');
  try {
    const balance = await connection.getBalance(keypair.publicKey);
    console.log(`[BALANCE] ${balance / LAMPORTS_PER_SOL} SOL (${balance} lamports)`);
    
    if (balance < 5000) {
      console.log("[INFO] Requesting airdrop...");
      try {
        const sig = await connection.requestAirdrop(keypair.publicKey, LAMPORTS_PER_SOL);
        await connection.confirmTransaction(sig);
        console.log("[OK] Airdrop successful!");
      } catch (err) {
        console.log("[WARN] Airdrop failed (rate limited?): " + err.message);
        console.log("[INFO] Continuing... will fallback to hash proofs if tx fails.");
      }
    }
  } catch (err) {
    console.log("[WARN] Balance check failed: " + err.message);
  }

  // Test CAPABILITY 1: Insurance Proofing
  try {
    const proof = await proofInsuranceOnSolana('Policy', 'test-policy-123', {
      holder: 'Test User',
      policyText: 'Self-test coverage'
    });
    const isOnChain = !proof.signature.startsWith('CG_PROOF_');
    console.log(`[CAP1] Insurance Proofing: ${isOnChain ? 'ON-CHAIN' : 'HASH-PROOF'}`);
    if (isOnChain) {
      console.log(`[LINK] https://explorer.solana.com/tx/${proof.signature}?cluster=devnet`);
    } else {
      console.log(`[HASH] ${proof.signature.substring(0, 40)}...`);
    }
  } catch (err) {
    console.log("[FAIL] CAPABILITY 1: " + err.message);
  }

  // Test CAPABILITY 2: Coverage Logging
  try {
    const log = await logCoverageDecisionOnSolana('test-policy-123', 'CLAIM_APPROVED', 'Low Risk');
    const isOnChain = !log.signature.startsWith('CG_PROOF_');
    console.log(`[CAP2] Coverage Logging: ${isOnChain ? 'ON-CHAIN' : 'HASH-PROOF'}`);
    if (isOnChain) {
      console.log(`[LINK] https://explorer.solana.com/tx/${log.signature}?cluster=devnet`);
    }
  } catch (err) {
    console.log("[FAIL] CAPABILITY 2: " + err.message);
  }

  // Test CAPABILITY 3: Gap Verification
  try {
    const gap = await verifyCoverageGapOnSolana('MissingLiability', 'High', 'test-policy-123');
    const isOnChain = !gap.signature.startsWith('CG_PROOF_');
    console.log(`[CAP3] Gap Verification: ${isOnChain ? 'ON-CHAIN' : 'HASH-PROOF'}`);
    if (isOnChain) {
      console.log(`[LINK] https://explorer.solana.com/tx/${gap.signature}?cluster=devnet`);
    }
  } catch (err) {
    console.log("[FAIL] CAPABILITY 3: " + err.message);
  }

  console.log("\n[DONE] Self-Test Complete!");
}

runSelfTest().catch(console.error);
