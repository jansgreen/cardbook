param(
    [string]$PublicBaseUrl = "https://incardbook.com",
    [string]$ExpectedVersion = "",
    [switch]$AllowDeploymentPending,
    [switch]$AllowReadinessWarnings
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

function Read-ErrorResponseBody($Response) {
    if (-not $Response) { return "" }
    try {
        $stream = $Response.GetResponseStream()
        if (-not $stream) { return "" }
        $reader = [System.IO.StreamReader]::new($stream)
        $body = $reader.ReadToEnd()
        $reader.Close()
        return $body
    }
    catch {
        return ""
    }
}

function Parse-JsonBody($Body, $Url) {
    if (-not $Body) { return $null }
    try {
        return $Body | ConvertFrom-Json
    }
    catch {
        Fail "Respuesta JSON invalida desde ${Url}: $($_.Exception.Message)"
        return $null
    }
}

function Invoke-CardbookJson($Path, [switch]$AllowHttpError) {
    $url = "$($PublicBaseUrl.TrimEnd('/'))$Path"
    $script:LastJsonStatusCode = 0
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($curl) {
        try {
            $raw = & $curl.Source -s -w "`n__STATUS__:%{http_code}" $url
            $statusLine = $raw | Select-Object -Last 1
            $bodyLines = @($raw | Select-Object -SkipLast 1)
            $body = ($bodyLines -join "`n").Trim()
            if ($statusLine -match "__STATUS__:(\d+)") {
                $script:LastJsonStatusCode = [int]$Matches[1]
            }
            $json = Parse-JsonBody $body $url
            if ($script:LastJsonStatusCode -ge 200 -and $script:LastJsonStatusCode -lt 400) {
                Pass "$url -> $script:LastJsonStatusCode"
                return $json
            }
            if ($AllowHttpError) {
                Warn "$url respondio $script:LastJsonStatusCode"
                return $json
            }
            $details = ""
            if ($json -and $json.production_config_issues) {
                $details = " " + (($json.production_config_issues | ForEach-Object { $_ }) -join " | ")
            }
            Fail "$url respondio $script:LastJsonStatusCode$details"
            return $json
        }
        catch {
            Warn "curl.exe no pudo consultar ${url}: $($_.Exception.Message). Usando Invoke-WebRequest."
        }
    }

    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
        $script:LastJsonStatusCode = [int]$response.StatusCode
        if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 400) {
            if (-not $AllowHttpError) {
                Fail "$url respondio $($response.StatusCode)"
            }
            return $null
        }

        Pass "$url -> $($response.StatusCode)"
        return Parse-JsonBody $response.Content $url
    }
    catch {
        $response = $_.Exception.Response
        $body = Read-ErrorResponseBody $response
        if ($response) {
            $script:LastJsonStatusCode = [int]$response.StatusCode
            $json = Parse-JsonBody $body $url
            if ($AllowHttpError) {
                Warn "$url respondio $($script:LastJsonStatusCode)"
                return $json
            }
            $details = ""
            if ($json -and $json.production_config_issues) {
                $details = " " + (($json.production_config_issues | ForEach-Object { $_ }) -join " | ")
            }
            Fail "No se pudo consultar ${url}: $($_.Exception.Message)$details"
            return $json
        }
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

$ready = Invoke-CardbookJson "/health/ready/" -AllowHttpError
if ($ready) {
    if ($script:LastJsonStatusCode -ge 400) {
        $issues = @()
        if ($ready.production_config_issues) {
            $issues = $ready.production_config_issues | ForEach-Object { $_ }
        }
        if ($AllowReadinessWarnings -and $ready.database -eq "ok") {
            Warn "readiness degradado permitido para beta: $($issues -join ' | ')"
        }
        else {
            Fail "readiness respondio $script:LastJsonStatusCode: $($issues -join ' | ')"
        }
    }
    elseif ($ready.database -eq "ok") {
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
