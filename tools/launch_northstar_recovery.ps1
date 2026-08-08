$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\Chris\Documents\Tsx momentum trading\tsx-momentum-trading-recovered"

$PythonExe = "C:\Users\Chris\AppData\Local\Programs\Python\Python313\python.exe"

$TwsExe = "C:\Jts\tws.exe"

$TwsDirectory = "C:\Jts"


Set-Location $ProjectRoot


# ------------------------------------------------------------
# TWS
# ------------------------------------------------------------

$twsProcess = Get-Process `
    -Name "tws" `
    -ErrorAction SilentlyContinue


if (-not $twsProcess) {

    Start-Process `
        -FilePath $TwsExe `
        -ArgumentList '-J-DjtsConfigDir="C:\Jts"' `
        -WorkingDirectory $TwsDirectory

    Write-Host "TWS launch requested."

    Start-Sleep -Seconds 8
}
else {

    Write-Host (
        "TWS already running. PID: " +
        $twsProcess[0].Id
    )
}


# ------------------------------------------------------------
# NORTHSTAR
# ------------------------------------------------------------

$northstarProcess = Get-CimInstance Win32_Process |
    Where-Object {

        $_.Name -ieq "python.exe" -and

        $_.CommandLine -match `
            '(?i)-m\s+gui\.trading_workstation'
    }


if (-not $northstarProcess) {

    Start-Process `
        -FilePath $PythonExe `
        -ArgumentList @(
            "-m",
            "gui.trading_workstation"
        ) `
        -WorkingDirectory $ProjectRoot

    Write-Host "Northstar launch requested."
}
else {

    Write-Host (
        "Northstar already running. PID: " +
        $northstarProcess[0].ProcessId
    )
}