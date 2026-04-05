const mongoose = require('mongoose');

const ClaimSchema = new mongoose.Schema({
  policyId: { type: mongoose.Schema.Types.ObjectId, ref: 'Policy', required: true },
  claimDetails: { type: String, required: true },
  status: { type: String, default: 'Pending' },
  solanaTxSignature: { type: String }, // Digital proof on Solana
  hash: { type: String }, // Local data integrity hash
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Claim', ClaimSchema);
