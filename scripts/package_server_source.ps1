param(
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not $OutputPath) {
    $OutputPath = Join-Path $projectRoot "storage\deploy\algowiki-source.tar.gz"
}

$outputDir = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

tar -czf $OutputPath `
    --exclude="frontend/node_modules" `
    --exclude="frontend/dist" `
    --exclude="backend/.env" `
    --exclude="deploy/.env.production" `
    --exclude="deploy/.env.private-validation" `
    --exclude="backend/media" `
    --exclude="backend/staticfiles" `
    --exclude="storage" `
    --exclude=".git" `
    --exclude="backend/.git" `
    --exclude="venv" `
    --exclude="__attachments" `
    -C $projectRoot `
    backend deploy docs frontend scripts .dockerignore .editorconfig .gitignore CONTRIBUTING.md docker-compose.server.yml Dockerfile LICENSE README.md SECURITY.md

Write-Host ("Saved source archive: {0}" -f $OutputPath)
