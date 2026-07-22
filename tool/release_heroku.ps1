param(
    [string]$AppName = "cardbook",
    [string]$SourceRef = "stable/cardbook-core",
    [string]$TargetRef = "main",
    [string]$PublicBaseUrl = "https://cardbook-45cf0409dc07.herokuapp.com",
    [switch]$Deploy,
    [switch]$SkipFlutter,
    [switch]$SkipCollectstatic,
    [switch]$SkipSmokeBeforeDeploy,
    [switch]$AllowDeploymentPending,
    [switch]$AllowReadinessWarnings
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Step($Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Checked([scriptblock]$Command, [string]$FailureMessage) {
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

Push-Location $ProjectRoot
try {
    Step "Release summary"
    Write-Host "Project: $ProjectRoot"
    Write-Host "Heroku app: $AppName"
    Write-Host "Source ref: $SourceRef"
    Write-Host "Target ref: $TargetRef"
    Write-Host "Public URL: $PublicBaseUrl"

    Step "Local production gate"
    $gateArgs = @(
        "-ExecutionPolicy", "Bypass",
        "-File", ".\tool\production_gate.ps1",
        "-ProjectRoot", $ProjectRoot,
        "-PublicBaseUrl", $PublicBaseUrl
    )
    if ($SkipFlutter) { $gateArgs += "-SkipFlutter" }
    if ($SkipCollectstatic) { $gateArgs += "-SkipCollectstatic" }
    if ($SkipSmokeBeforeDeploy) { $gateArgs += "-SkipSmoke" }
    Invoke-Checked { powershell @gateArgs } "production_gate fallo"

    if (-not $Deploy) {
        Step "Dry run listo"
        Write-Host "No se ejecuto deploy. Para desplegar realmente:" -ForegroundColor Yellow
        Write-Host "  .\tool\release_heroku.ps1 -Deploy"
        return
    }

    Step "Push to Heroku"
    Invoke-Checked { git push heroku "${SourceRef}:${TargetRef}" } "git push heroku fallo"

    Step "Run migrations"
    Invoke-Checked { heroku run --app $AppName --exit-code --no-tty -- python manage.py migrate } "heroku migrate fallo"

    Step "Operational snapshot on Heroku"
    Invoke-Checked { heroku run --app $AppName --exit-code --no-tty -- python manage.py ops_snapshot --json } "ops_snapshot remoto fallo"

    Step "Smoke test after deploy"
    $smokeArgs = @(
        "-ExecutionPolicy", "Bypass",
        "-File", ".\mobile-cardbook\tool\smoke_heroku.ps1",
        "-PublicBaseUrl", $PublicBaseUrl
    )
    if ($AllowDeploymentPending) { $smokeArgs += "-AllowDeploymentPending" }
    if ($AllowReadinessWarnings) { $smokeArgs += "-AllowReadinessWarnings" }
    Invoke-Checked { powershell @smokeArgs } "smoke post-deploy fallo"

    Step "Release listo"
    Write-Host "Cardbook quedo validado en produccion." -ForegroundColor Green
}
finally {
    Pop-Location
}
