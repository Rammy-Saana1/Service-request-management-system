param(
    [Parameter()]
    [ValidateRange(1, 65535)]
    [int]$Port = 8080,

    [Parameter()]
    [string]$ManagerPasscode
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($ManagerPasscode)) {
    $ManagerPasscode = $env:LOCAL_SIM_MANAGER_PASSCODE
}
if ([string]::IsNullOrWhiteSpace($ManagerPasscode)) {
    $securePasscode = Read-Host 'Choose a local manager passcode (at least 12 characters)' -AsSecureString
    $ManagerPasscode = [System.Net.NetworkCredential]::new('', $securePasscode).Password
}
if ($ManagerPasscode.Length -lt 12) {
    throw 'Manager passcode must contain at least 12 characters.'
}

$previousPasscode = $env:LOCAL_SIM_MANAGER_PASSCODE
try {
    $env:LOCAL_SIM_MANAGER_PASSCODE = $ManagerPasscode
    python .\app.py --host 127.0.0.1 --port $Port
} finally {
    $env:LOCAL_SIM_MANAGER_PASSCODE = $previousPasscode
}
