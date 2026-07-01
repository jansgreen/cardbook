param(
    [string]$PublicBaseUrl = "https://cardbook-45cf0409dc07.herokuapp.com",
    [string]$ExpectedVersion = "",
    [switch]$AllowDeploymentPending
)

$ErrorActionPreference = "Continue"
$failures = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

function Pass($Message) {
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Warn($Message) {
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
    $warnings.Add($Message) | Out-Null
}

function Fail($Message) {
    if ($AllowDeploymentPending) {
        Warn $Message
    }
    else {
        Write-Host "[FAIL] $Message" -ForegroundColor Red
        $failures.Add($Message) | Out-Null
    }
}

function Invoke-CardbookJson($Path) {
    $url = "$($PublicBaseUrl.TrimEnd('/'))$Path"
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
        if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 400) {
            Fail "$url respondio $($response.StatusCode)"
            return $null
        }

        Pass "$url -> $($response.StatusCode)"
        return $response.Content | ConvertFrom-Json
    }
    catch {
        Fail "No se pudo consultar ${url}: $($_.Exception.Message)"
        return $null
    }
}

function Invoke-CardbookPage($Path, $Label) {
    $url = "$($PublicBaseUrl.TrimEnd('/'))$Path"
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
            Pass "$Label -> $($response.StatusCode)"
        }
        else {
            Fail "$Label respondio $($response.StatusCode)"
        }
    }
    catch {
        Fail "No se pudo consultar ${url}: $($_.Exception.Message)"
    }
}

Write-Host "Cardbook production smoke test" -ForegroundColor Cyan
Write-Host "Base URL: $PublicBaseUrl"
Write-Host ""

$health = Invoke-CardbookJson "/health/"
if ($health) {
    if ($health.status -eq "ok") {
        Pass "health status ok"
    }
    else {
        Fail "health status inesperado: $($health.status)"
    }

    if ($ExpectedVersion -and $health.version -ne $ExpectedVersion) {
        Fail "version esperada $ExpectedVersion, recibida $($health.version)"
    }
    elseif ($health.version) {
        Pass "version publica $($health.version)"
    }
}

$ready = Invoke-CardbookJson "/health/ready/"
if ($ready) {
    if ($ready.database -eq "ok") {
        Pass "database ready"
    }
    else {
        Fail "database no esta lista"
    }
}

$apiRoot = Invoke-CardbookJson "/api/v1/"
if ($apiRoot) {
    if ($apiRoot.success -eq $true -and $apiRoot.data.mobile) {
        Pass "api root expone mobile endpoints"
    }
    else {
        Fail "api root no expone estructura esperada"
    }
}

$androidVersion = Invoke-CardbookJson "/android/version/"
if ($androidVersion) {
    if ($androidVersion.latest_version_code -gt 0 -and $androidVersion.download_url) {
        Pass "android version endpoint listo"
    }
    else {
        Fail "android version endpoint incompleto"
    }
}

Invoke-CardbookPage "/" "home"
Invoke-CardbookPage "/android/" "android page"
Invoke-CardbookPage "/privacy/" "privacy page"
Invoke-CardbookPage "/terms/" "terms page"

Write-Host ""
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "Failures: $($failures.Count)"
Write-Host "Warnings: $($warnings.Count)"

if ($failures.Count -gt 0) {
    exit 1
}

exit 0

