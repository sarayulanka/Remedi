# Remedi Backend Installation Script for Windows
# This script installs packages in a specific order to avoid Rust compilation issues

Write-Host "🌱 Installing Remedi Backend Dependencies..." -ForegroundColor Green
Write-Host ""

# Upgrade pip first
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install packages in order, starting with ones that have pre-built wheels
Write-Host ""
Write-Host "Installing core dependencies..." -ForegroundColor Yellow
pip install annotated-types==0.7.0
pip install pydantic-core==2.27.0
pip install pydantic==2.10.3
pip install pydantic-settings==2.6.1

Write-Host ""
Write-Host "Installing FastAPI and Uvicorn..." -ForegroundColor Yellow
pip install fastapi==0.115.0
pip install "uvicorn[standard]==0.32.1"

Write-Host ""
Write-Host "Installing AWS SDK..." -ForegroundColor Yellow
pip install boto3==1.35.0

Write-Host ""
Write-Host "Installing authentication packages..." -ForegroundColor Yellow
pip install "python-jose[cryptography]==3.3.0"
pip install "passlib[bcrypt]==1.7.4"

Write-Host ""
Write-Host "Installing HTTP and API packages..." -ForegroundColor Yellow
pip install requests==2.32.3
pip install httpx==0.27.2
pip install python-multipart==0.0.12

Write-Host ""
Write-Host "Installing OpenAI..." -ForegroundColor Yellow
pip install openai==1.54.0

Write-Host ""
Write-Host "Installing utilities..." -ForegroundColor Yellow
pip install python-dotenv==1.0.1
pip install email-validator==2.2.0

Write-Host ""
Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the backend, run:" -ForegroundColor Cyan
Write-Host "  python main.py" -ForegroundColor White
Write-Host ""
