"""
Fix the Kaggle FINAL notebook's record_blockchain function.
Problem: It generates fake base58 signatures that look like real Solana tx sigs,
causing "Invalid Signature" errors on Solana Explorer.
Solution: Use SHA-256 hex hash prefixed with CG_PROOF_ so it's clearly a hash proof,
and link to Explorer home page instead of a fake /tx/ URL.
"""
import json

notebook_path = "ClaimGuard_FINAL_Kaggle.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

patched = False
for cell in nb['cells']:
    if cell['cell_type'] != 'code':
        continue
    source = "".join(cell['source'])
    
    if "def record_blockchain(" in source and "base58" in source:
        # Find and replace the blockchain function
        new_lines = []
        skip_until_return_end = False
        i = 0
        lines = cell['source']
        
        while i < len(lines):
            line = lines[i]
            
            # Replace the old function definition block
            if "# BLOCKCHAIN: Mock record (no real wallet)" in line:
                new_lines.append("# BLOCKCHAIN: SHA-256 Hash Proof (clean, no fake signatures)\n")
                i += 1
                continue
            
            if "def record_blockchain(policy_name, bill_name, evaluation):\n" in line:
                # Replace the entire function
                new_lines.append("def record_blockchain(policy_name, bill_name, evaluation):\n")
                new_lines.append("    ts = datetime.now(timezone.utc).isoformat()\n")
                new_lines.append("    record = {'app': 'ClaimGuardAI', 'v': '7.0', 'ts': ts,\n")
                new_lines.append("              'policy': str(policy_name)[:25], 'bill': str(bill_name)[:25],\n")
                new_lines.append("              'payable': evaluation.get('final_payable_by_insurer', 0)}\n")
                new_lines.append("    data_str = json.dumps(record, sort_keys=True, separators=(',',':'))\n")
                new_lines.append("    data_hash = hashlib.sha256(data_str.encode()).hexdigest()[:32]\n")
                new_lines.append("    # Use CG_PROOF_ prefix so it's clearly NOT a Solana tx signature\n")
                new_lines.append("    proof_id = 'CG_PROOF_' + hashlib.sha256(f'{data_hash}{ts}'.encode()).hexdigest()\n")
                new_lines.append("    return {\n")
                new_lines.append("        'success': True, 'signature': proof_id, 'hash': data_hash,\n")
                new_lines.append("        'explorer_url': 'https://explorer.solana.com/?cluster=devnet',\n")
                new_lines.append("        'network': 'solana-devnet', 'on_chain': False,\n")
                new_lines.append("        'proof_type': 'sha256_hash_proof',\n")
                new_lines.append("        'note': 'Cryptographic hash proof. Verifiable offline via SHA-256.'\n")
                new_lines.append("    }\n")
                
                # Skip the old function body
                i += 1
                while i < len(lines):
                    old_line = lines[i]
                    # The function ends after the return block closes with }
                    if old_line.strip() == "}" or "'network': 'solana-devnet'" in old_line:
                        i += 1
                        # Skip the closing brace and newline
                        if i < len(lines) and lines[i].strip() in ["}", "    }", "    }\n"]:
                            i += 1
                        break
                    i += 1
                patched = True
                continue
            
            # Remove the "import base58" line inside the old function
            if "    import base58\n" in line:
                i += 1
                continue
            
            new_lines.append(line)
            i += 1
        
        cell['source'] = new_lines
        break

if patched:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("[OK] Kaggle notebook blockchain function FIXED!")
    print("   - No more fake base58 signatures")
    print("   - Uses CG_PROOF_ prefix for clear hash proofs")
    print("   - Explorer URL points to devnet home, not fake /tx/ URL")
else:
    print("[WARN] Could not find the record_blockchain function to patch")
