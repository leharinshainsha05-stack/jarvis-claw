# Fix ChromaDB installation
Write-Host "Fixing ChromaDB..." -ForegroundColor Cyan
pip uninstall chromadb -y 2>$null
pip install chromadb --upgrade
Write-Host "ChromaDB reinstalled. Run test_jarvis.py again." -ForegroundColor Green