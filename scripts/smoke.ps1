# PyroScope Deployment Smoke Test (PowerShell)
# Usage: .\scripts\smoke.ps1 [-ApiUrl http://localhost:8000]
param (
    [string]$ApiUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"
Write-Host "==> PyroScope Smoke Verification: Testing API at $ApiUrl" -ForegroundColor Cyan

$FailedCount = 0

function Test-Endpoint {
    param (
        [string]$Name,
        [string]$Url,
        [string]$ExpectedProperty,
        [string]$Method = "GET",
        [string]$Body = $null
    )

    Write-Host -NoNewline "  Testing $Name... "
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            TimeoutSec = 10
            ErrorAction = "Stop"
        }
        if ($Body) {
            $params["ContentType"] = "application/json"
            $params["Body"] = $Body
        }

        $res = Invoke-RestMethod @params
        $json = $res | ConvertTo-Json -Depth 5 -Compress

        if ($json -match $ExpectedProperty) {
            Write-Host "[OK]" -ForegroundColor Green
        } else {
            Write-Host "[FAILED] Missing keyword '$ExpectedProperty'" -ForegroundColor Red
            $script:FailedCount++
        }
    } catch {
        Write-Host "[FAILED] $($_.Exception.Message)" -ForegroundColor Red
        $script:FailedCount++
    }
}

Test-Endpoint -Name "1. Health Endpoint (/api/health)" `
              -Url "$ApiUrl/api/health" `
              -ExpectedProperty "healthy"

Test-Endpoint -Name "2. Meta & Manifest (/api/meta)" `
              -Url "$ApiUrl/api/meta" `
              -ExpectedProperty "dataVersion"

Test-Endpoint -Name "3. Heatmap Grid (/api/heatmap)" `
              -Url "$ApiUrl/api/heatmap?bbox=88.0,20.5,92.8,26.7&from=2020-05&to=2020-05&metric=harmonized&res=7" `
              -ExpectedProperty "cells"

Test-Endpoint -Name "4. FireCalendar Grid (/api/calendar)" `
              -Url "$ApiUrl/api/calendar?area_id=BGD-ADM2-alpha" `
              -ExpectedProperty "grid"

Test-Endpoint -Name "5. Ask Assistant (/api/ask in replay mode)" `
              -Url "$ApiUrl/api/ask" `
              -Method "POST" `
              -Body '{"question": "When does fire season start in alpha and was 2020 unusual?", "area_id": "BGD-ADM2-alpha"}' `
              -ExpectedProperty "replay"

Write-Host "--------------------------------------------------------"
if ($FailedCount -eq 0) {
    Write-Host "==> All deployment smoke tests PASSED successfully." -ForegroundColor Green
    exit 0
} else {
    Write-Host "==> Deployment smoke tests FAILED ($FailedCount errors)." -ForegroundColor Red
    exit 1
}
