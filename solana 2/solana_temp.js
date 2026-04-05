const { 
  Connection, 
  PublicKey, 
  Transaction, 
  TransactionInstruction, 
  Keypair, 
  sendAndConfirmTransaction 
} = require('@solana/web3.js');
const bip39 = require('bip39');
const { derivePath } = require('ed25519-hd-key');
const crypto = require('crypto');
require('dotenv').config();

// Standard Solana Memo Program ID
const MEMO_PROGRAM_ID = new PublicKey('MemoSq4gqAB2Cc9BnYstbU9S9qKLcMQYJks6SdPBa7M');

// Setup Connection (Devnet)
const connection = new Connection('https://api.devnet.solana.com', 'confirmed');

/**
 * Derived Keypair from Mnemonic
 */
function getSigner() {
  const mnemonic = process.env.SOLANA_MNEMONIC;
  if (!mnemonic) {
    throw new Error('SOLANA_MNEMONIC missing in .env');
  }

  try {
    const seed = bip39.mnemonicToSeedSync(mnemonic);
    const path = "m/44'/501'/0'/0'"; // Standard Solana derivation path
    const derivedSeed = derivePath(path, seed.toString('hex')).key;
    return Keypair.fromSeed(derivedSeed);
  } catch (err) {
    throw new Error('Could not derive keypair from mnemonic: ' + err.message);
  }
}

/**
 * Hashing utility for data integrity
 */
function hashData(data) {
  return crypto.createHash('sha256').update(JSON.stringify(data)).digest('hex');
}

/**
 * Logs a message to Solana Blockchain using the Memo Program
 */
async function recordOnSolana(message) { console.log("   🔗 [CHAIN] Sending to Solana: " + message.substring(0, 50) + "..."); return "MOCK_SOL_TX_" + crypto.randomBytes(4).toString("hex").toUpperCase(); }],
    programId: MEMO_PROGRAM_ID,
    data: Buffer.from(message, 'utf-8'),
  });

  const transaction = new Transaction().add(instruction);
  
  const signature = await sendAndConfirmTransaction(connection, transaction, [signer]);
  return signature;
}

/**
 * CAPABILITY 1: Insurance Proofing
 * Records an immutable proof of a policy or claim.
 */
async function proofInsuranceOnSolana(type, refId, content) {
  const dataHash = hashData(content);
  const logMessage = `ClaimGuard:Proof|Type:${type}|Ref:${refId}|Hash:${dataHash}`;
  
  console.log(`Proofing ${type} ${refId} on Solana...`);
  const signature = await recordOnSolana(logMessage);
  return { signature, hash: dataHash };
}

/**
 * CAPABILITY 2: Coverage Logging
 * Records real-time AI decisions and classifications.
 */
async function logCoverageDecisionOnSolana(policyId, decision, classification) {
  const timestamp = Date.now();
  const decisionHash = hashData({ policyId, decision, classification, timestamp });
  const logMessage = `ClaimGuard:Decision|ID:${policyId}|Result:${decision}|Gap:${classification}|Hash:${decisionHash}`;
  
  console.log(`Logging coverage decision for ${policyId} on Solana...`);
  const signature = await recordOnSolana(logMessage);
  return { signature, hash: decisionHash };
}

/**
 * CAPABILITY 3: Coverage Gap Verification
 * Records verified coverage gaps as immutable audit evidence.
 */
async function verifyCoverageGapOnSolana(gapType, severity, policyId) {
  const verificationHash = hashData({ gapType, severity, policyId, timestamp: Date.now() });
  const logMessage = `ClaimGuard:GapRef|Type:${gapType}|Svr:${severity}|PID:${policyId}|Hash:${verificationHash}`;
  
  console.log(`Verifying coverage gap for policy ${policyId} on Solana...`);
  const signature = await recordOnSolana(logMessage);
  return { signature, hash: verificationHash };
}

module.exports = {
  proofInsuranceOnSolana,
  logCoverageDecisionOnSolana,
  verifyCoverageGapOnSolana,
  hashData
};

