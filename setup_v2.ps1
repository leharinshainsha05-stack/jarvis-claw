# ══════════════════════════════════════════════════════════
# JARVIS v2.0 — Windows Setup Script
# Run: PowerShell -ExecutionPolicy Bypass -File setup_v2.ps1
# ══════════════════════════════════════════════════════════

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       JARVIS v2.0 — SETUP SCRIPT         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Activate venv ──
Write-Host "[ 1/5 ] Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "        ✓ venv activated" -ForegroundColor Green
} else {
    Write-Host "        ⚠ venv not found — using system Python" -ForegroundColor Red
}

# ── Step 2: Install v2 dependencies ──
Write-Host ""
Write-Host "[ 2/5 ] Installing v2.0 dependencies..." -ForegroundColor Yellow
pip install sentence-transformers --quiet
Write-Host "        ✓ sentence-transformers" -ForegroundColor Green
pip install groq --quiet
Write-Host "        ✓ groq" -ForegroundColor Green
pip install chromadb --quiet
Write-Host "        ✓ chromadb" -ForegroundColor Green
pip install langdetect --quiet
Write-Host "        ✓ langdetect" -ForegroundColor Green

# ── Step 3: Create folder structure ──
Write-Host ""
Write-Host "[ 3/5 ] Creating v2.0 folder structure..." -ForegroundColor Yellow
$folders = @("router", "brain", "memory", "agentic", "utils", "chroma_db")
foreach ($f in $folders) {
    if (-not (Test-Path $f)) { New-Item -ItemType Directory -Path $f | Out-Null }
}
Write-Host "        ✓ Folders ready" -ForegroundColor Green

# ── Step 4: Set GROQ_API_KEY ──
Write-Host ""
Write-Host "[ 4/5 ] Groq API Key Setup" -ForegroundColor Yellow
Write-Host "        Get your free key at: https://console.groq.com" -ForegroundColor Cyan
$key = Read-Host "        Enter GROQ_API_KEY (press Enter to skip)"
if ($key) {
    [System.Environment]::SetEnvironmentVariable("GROQ_API_KEY", $key, "User")
    Write-Host "        ✓ GROQ_API_KEY saved to user environment" -ForegroundColor Green
} else {
    Write-Host "        ⚠ Skipped — General Brain will fallback to local Ollama" -ForegroundColor Yellow
}

# ── Step 5: Verify Ollama ──
Write-Host ""
Write-Host "[ 5/5 ] Checking Ollama..." -ForegroundColor Yellow
try {
    $ollamaCheck = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -ErrorAction SilentlyContinue
    Write-Host "        ✓ Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "        ⚠ Ollama not running. Start it with: ollama serve" -ForegroundColor Red
    Write-Host "          Also pull model: ollama pull gemma3:1b" -ForegroundColor Yellow
    Write-Host "          For LLaVA vision: ollama pull llava" -ForegroundColor Yellow
}

# ── Done ──
Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║         SETUP COMPLETE — v2.0            ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  Start Jarvis:  python main.py           ║" -ForegroundColor White
Write-Host "║  Frontend:      open jarvis-frontend/    ║" -ForegroundColor White
Write-Host "║                 index.html in browser    ║" -ForegroundColor White
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""