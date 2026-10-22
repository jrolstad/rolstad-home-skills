# Launches a normal Chrome with a remote-debugging port and a dedicated profile.
# This is a real, human-driven browser (no automation flags), so ID.me bot validation
# treats the login like any normal session. After logging into VA.gov here, run
# fetch-va-data.mjs to attach over CDP and pull the data.

$ErrorActionPreference = 'Stop'
$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
if (-not (Test-Path $chrome)) {
    throw "Chrome not found at $chrome. Edit this script with the correct path."
}

$profileDir = Join-Path $PSScriptRoot '.chrome-cdp-profile'
New-Item -ItemType Directory -Force -Path $profileDir | Out-Null

# Port 9222 must match CDP_URL in fetch-va-data.mjs.
& $chrome `
    --remote-debugging-port=9222 `
    --user-data-dir="$profileDir" `
    'https://www.va.gov/my-va/'

Write-Host "Chrome launched on port 9222 with profile: $profileDir"
Write-Host "Log into VA.gov, then run:  node `"$PSScriptRoot\fetch-va-data.mjs`""
