# WhatsEat Backend - Installation & Setup Script
# Run this script to set up the entire environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WhatsEat Backend - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python version
Write-Host "[1/5] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "      $pythonVersion" -ForegroundColor Green

# Step 2: Install dependencies
Write-Host ""
Write-Host "[2/5] Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "      This may take a few minutes..." -ForegroundColor Gray

pip install --upgrade pip

# Core LangGraph dependencies
pip install langgraph>=0.6.0 langchain>=0.3.27 langchain-core>=0.3.40 langchain-openai>=0.3.33

# Database and Vector Store
pip install neo4j>=5.0.0 pinecone-client>=3.0.0

# OpenAI
pip install openai>=1.0.0

# Google APIs
pip install google-api-python-client>=2.0.0 google-auth-httplib2>=0.1.0 google-auth-oauthlib>=1.0.0

# Utilities
pip install requests>=2.31.0

# Testing
pip install pytest>=8.4.1

Write-Host "      ✓ Dependencies installed" -ForegroundColor Green

# Step 3: Setup environment configuration
Write-Host ""
Write-Host "[3/5] Setting up environment configuration..." -ForegroundColor Yellow

$envJsonSource = "whats_eat\.env.json"
$envJsonDest = ".env.json"

if (Test-Path $envJsonSource) {
    Copy-Item $envJsonSource $envJsonDest -Force
    Write-Host "      ✓ Copied .env.json to root directory" -ForegroundColor Green
    
    # Display configuration
    $envContent = Get-Content $envJsonDest | ConvertFrom-Json
    Write-Host ""
    Write-Host "      Environment Configuration:" -ForegroundColor Cyan
    Write-Host "      - Neo4j URI: $($envContent.NEO4J_URI)" -ForegroundColor Gray
    Write-Host "      - Neo4j User: $($envContent.NEO4J_USER)" -ForegroundColor Gray
    Write-Host "      - Neo4j Database: $($envContent.NEO4J_DATABASE)" -ForegroundColor Gray
    Write-Host "      - Pinecone Environment: $($envContent.PINECONE_ENVIRONMENT)" -ForegroundColor Gray
    Write-Host "      - OpenAI API Key: $(if ($envContent.OPENAI_API_KEY) { '✓ Set' } else { '✗ Missing' })" -ForegroundColor Gray
    Write-Host "      - Google Maps API Key: $(if ($envContent.GOOGLE_MAPS_API_KEY) { '✓ Set' } else { '✗ Missing' })" -ForegroundColor Gray
} else {
    Write-Host "      ✗ Warning: .env.json not found in whats_eat directory" -ForegroundColor Red
}

# Step 4: Verify installation
Write-Host ""
Write-Host "[4/5] Verifying installation..." -ForegroundColor Yellow

$packages = @(
    "langgraph",
    "langchain",
    "langchain-openai",
    "neo4j",
    "pinecone-client",
    "openai",
    "google-api-python-client"
)

foreach ($package in $packages) {
    $installed = pip show $package 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      ✓ $package" -ForegroundColor Green
    } else {
        Write-Host "      ✗ $package (not installed)" -ForegroundColor Red
    }
}

# Step 5: Run test
Write-Host ""
Write-Host "[5/5] Running test suite..." -ForegroundColor Yellow
Write-Host ""

python tests\test_rag_agent.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review .env.json and ensure all API keys are set" -ForegroundColor White
Write-Host "  2. Run tests: pytest tests/" -ForegroundColor White
Write-Host "  3. Start development: python -m whats_eat.app.run" -ForegroundColor White
Write-Host ""
Write-Host "Documentation: See SETUP.md for detailed information" -ForegroundColor Gray
Write-Host ""
