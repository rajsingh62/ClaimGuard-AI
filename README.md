# ClaimGuard AI v4.0

## Blockchain-Verified Insurance Intelligence

ClaimGuard AI is a **production-ready** FastAPI application that uses AI (Llama3) to analyze insurance policies and repair bills, providing detailed coverage analysis with **immutable blockchain proof** on Solana.

---

## Features

### Core Capabilities
- **AI-Powered Analysis**: Uses Llama3 8B via Ollama to analyze policy documents and repair bills
- **OCR Extraction**: Extracts text from PDF, PNG, JPG files using OCR.space API
- **Risk Assessment**: Calculates coverage gaps and provides detailed breakdowns
- **Immutable Proof**: Records every evaluation hash on Solana blockchain for tamper-proof audit trails

### Blockchain Integration
- **Solana Devnet**: All evaluations recorded on Solana devnet with transaction signatures
- **Proof Verification**: Each analysis includes a blockchain explorer link for verification
- **Audit Trail**: Complete history of AI decisions permanently stored on-chain

### UI/UX
- **3-Page Application**:
  - `/` - Landing page with animated geometric visualization
  - `/lab` - Document upload and analysis interface
  - `/results` - Detailed results with blockchain proof display
- **Glassmorphism Design**: Modern dark theme with glass-card effects
- **Real-time Processing**: Animated loading states during analysis

---

## Project Structure

```
ClaimGuard AI/
├── main.py                    # FastAPI application with Solana integration
├── engine.py                  # AI evaluation and OCR logic
├── solana_integration.py      # Solana blockchain recording functions
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── README.md                 # This file
├── stitch/                   # Frontend templates
│   ├── hero_experience/      # Landing page
│   ├── analysis_lab/         # Upload interface
│   └── results_dashboard/    # Results display
└── tmp_uploads/              # Temporary file storage (auto-created)
```

---

## Quick Start

### Prerequisites

1. **Python 3.10+**
2. **Ollama** with Llama3 model installed:
   ```bash
   ollama pull llama3:8b
   ollama serve
   ```
3. **OCR.space API Key** (free tier available)
4. **Poppler** (for PDF processing):
   - Windows: Download from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases)
   - Mac: `brew install poppler`
   - Linux: `sudo apt-get install poppler-utils`

### Installation

```bash
# Clone or navigate to the project
cd "ClaimGuard AI"

# Install dependencies
pip install -r requirements.txt

# Create environment file
copy .env.example .env
# Edit .env with your actual API keys

# Start the server
python main.py
```

The server will start at `http://localhost:8000`

---

## Environment Variables

Create a `.env` file with the following:

```env
# OCR API Key (get free key from https://ocr.space/ocrapi/free)
OCR_SPACE_API_KEY=your_ocr_api_key_here

# Ollama Configuration
OLLAMA_URL=http://localhost:11434/api/generate

# Solana Configuration
SOLANA_MNEMONIC=your_solana_wallet_mnemonic
SOLANA_RPC_URL=https://api.devnet.solana.com

# Optional: For real Solana integration (advanced)
# SOLANA_PRIVATE_KEY=your_private_key_base58
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Landing page |
| `/lab` | GET | Analysis lab interface |
| `/results` | GET | Results dashboard |
| `/api/evaluate` | POST | Main evaluation endpoint (multipart/form-data) |
| `/api/health` | GET | Health check |
| `/api/blockchain/status` | GET | Blockchain connection status |
| `/api/verify-gap` | POST | Record coverage gap on blockchain |

### Example API Usage

```bash
# Health check
curl http://localhost:8000/api/health

# Evaluate claim
curl -X POST http://localhost:8000/api/evaluate \
  -F "policy_file=@policy.pdf" \
  -F "bill_file=@repair_bill.pdf"
```

---

## API Response Format

```json
{
  "success": true,
  "timestamp": "2024-01-15T10:30:00",
  "processing_time_ms": 2450,
  "files": {
    "policy": "policy.pdf",
    "bill": "repair_bill.pdf"
  },
  "evaluation": {
    "total_bill_amount": 5000,
    "total_covered_amount": 3500,
    "total_not_covered_amount": 1500,
    "final_payable_by_insurer": 3500,
    "breakdown": [...],
    "summary": {...},
    "human_readable_summary": "Insurance will pay: $3,500..."
  },
  "blockchain": {
    "network": "solana-devnet",
    "signature": "5Kx...xyz",
    "hash": "a1b2c3d4...",
    "explorer_url": "https://explorer.solana.com/tx/...?cluster=devnet",
    "verified": true
  },
  "trust": {
    "ai_verified": true,
    "blockchain_verified": true,
    "audit_trail": "Proof: 5Kx..."
  }
}
```

---

## How It Works

### 1. Document Upload
User uploads policy and bill documents (PDF, PNG, JPG) via the `/lab` interface.

### 2. OCR Processing
Documents are processed using OCR.space API to extract text content.

### 3. AI Analysis
Extracted text is sent to Llama3 via Ollama for intelligent analysis:
- Compares bill items against policy coverage
- Identifies uncovered items
- Calculates totals and risk scores

### 4. Blockchain Recording
A hash of the evaluation is recorded on Solana blockchain, creating an immutable proof that can be verified later.

### 5. Results Display
Results are shown in `/results` with:
- Financial breakdown
- Risk gauge
- Blockchain verification card with explorer link
- Coverage gap details

---

## Logo & Branding

The new **CG.AI** logo features:
- **Shield shape**: Represents protection and insurance security
- **Checkmark**: Symbolizes verification and approval
- **Circuit lines**: Represents AI and technology
- **Gradient colors**: Blue (#0070f3) to Cyan (#4cd7f6) gradient

The logo appears in:
- Navbar on all pages
- Footer branding
- Browser favicon (can be added)

---

## Troubleshooting

### Common Issues

**OCR not working (PDFs)**
- Ensure Poppler is installed and in PATH
- Try converting PDF to image first

**Ollama connection error**
- Verify Ollama is running: `ollama serve`
- Check Llama3 is pulled: `ollama list`

**Blockchain recording fails**
- Currently uses mock signatures for demo
- For real Solana integration, install `solana` Python package

**Port already in use**
- Change port in `main.py` or kill existing process

---

## Development

### Adding New Features

1. **New API Endpoint**: Add to `main.py`
2. **AI Logic**: Modify `engine.py`
3. **Blockchain Functions**: Extend `solana_integration.py`
4. **Frontend**: Edit files in `stitch/` folders

### Testing

```bash
# Health check
curl http://localhost:8000/api/health

# Test with sample files
curl -X POST http://localhost:8000/api/evaluate \
  -F "policy_file=@test_policy.pdf" \
  -F "bill_file=@test_bill.pdf"
```

---

## Production Deployment

### Recommended Stack
- **Server**: Uvicorn with Gunicorn
- **Reverse Proxy**: Nginx
- **SSL**: Let's Encrypt
- **Monitoring**: Prometheus/Grafana

### Environment
```bash
# Production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Security Considerations
- Use production Solana mainnet for real proofs
- Add API authentication
- Implement rate limiting
- Use secure file upload validation
- Add CORS restrictions

---

## License

MIT License - See LICENSE file

## Support

For issues or questions:
- Check the health endpoint: `/api/health`
- Review server logs
- Verify all prerequisites are installed

---

**Built with**: FastAPI, Llama3, Solana, TailwindCSS
**Version**: 4.0.0
**Last Updated**: 2024
"# ClaimGuard-AI" 
