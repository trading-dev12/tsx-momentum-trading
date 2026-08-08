$ErrorActionPreference = "Stop"

$TaskName = "Northstar Recovery"

$ProjectRoot = Split-Path `
    -Parent $PSScriptRoot

$RecoveryScript = Join-Path `
    $PSScriptRoot `
    "launch_northstar_recovery.ps1"


if (-not (Test-Path $RecoveryScript)) {
    throw (
        "Recovery launcher not found: " +
        $RecoveryScript
    )
}


$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument (
        '-NoProfile -ExecutionPolicy Bypass -File "' +
        $RecoveryScript +
        '"'
    ) `
    -WorkingDirectory $ProjectRoot


$Trigger = New-ScheduledTaskTrigger `
    -AtLogOn `
    -User $env:USERNAME

$Trigger.Delay = "PT30S"


$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (
        New-TimeSpan -Minutes 1
    )


$Principal = New-ScheduledTaskPrincipal `
    -UserId (
        "$env:USERDOMAIN\$env:USERNAME"
    ) `
    -LogonType Interactive `
    -RunLevel Limited


Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description (
        "Starts TWS and Northstar after Windows logon " +
        "and avoids duplicate instances."
    ) `
    -Force


Write-Host ""
Write-Host "Northstar Recovery task installed."
Write-Host "Task name: $TaskName"
Write-Host "Recovery script: $RecoveryScript"
Write-Host "Startup delay: 30 seconds"
Write-Host "Retry count: 3"