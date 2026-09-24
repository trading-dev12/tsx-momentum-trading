$Source = "C:\Users\Chris\Documents\Tsx momentum trading\tsx-momentum-trading-recovered"
$VolumeLabel = "Extreme SSD"
$PollSeconds = 5
$MutexName = "Global\NorthstarExternalBackupWatcher"
$CreatedNew = $false

$Mutex = New-Object System.Threading.Mutex(
    $true,
    $MutexName,
    [ref]$CreatedNew
)

if (-not $CreatedNew) {
    exit 0
}

$WasConnected = $false
$WatcherLog = Join-Path $Source "logs\external_backup_watcher.log"

function Write-WatcherLog {
    param([string]$Message)

    $LogDirectory = Split-Path $WatcherLog

    if (-not (Test-Path $LogDirectory)) {
        New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
    }

    Add-Content $WatcherLog "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message"
}

Write-WatcherLog "Backup watcher started."

while ($true) {

    try {

        $Volume = Get-Volume -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FileSystemLabel -eq $VolumeLabel -and
                $_.DriveLetter
            } |
            Select-Object -First 1

        if ($Volume -and -not $WasConnected) {

            $Drive = "$($Volume.DriveLetter):"
            $BackupRoot = Join-Path $Drive "Northstar_Backups"

            New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

            $Timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
            $Destination = Join-Path $BackupRoot "Northstar_$Timestamp"
            $BackupLog = Join-Path $BackupRoot "Northstar_Backup_Log.txt"

            New-Item -ItemType Directory -Path $Destination -Force | Out-Null

            Write-WatcherLog "Extreme SSD detected. Starting backup to $Destination"

            robocopy $Source $Destination `
                /E `
                /COPY:DAT `
                /DCOPY:DAT `
                /FFT `
                /R:2 `
                /W:2 `
                /XJ `
                /XD "$Source\Northstar_Backups" "$Source\__pycache__" "$Source\.pytest_cache" "$Source\.venv" "$Source\venv" `
                /XF *.pyc *.lock `
                /NP `
                /LOG+:$BackupLog

            $ExitCode = $LASTEXITCODE

            if ($ExitCode -le 7) {

                $StatusFile = Join-Path $Destination "_BACKUP_SUCCESS.txt"

                @"
NORTHSTAR EXTERNAL BACKUP SUCCESS

Completed: $(Get-Date)
Source: $Source
Destination: $Destination
Robocopy Exit Code: $ExitCode
"@ | Set-Content $StatusFile

                Write-WatcherLog "BACKUP SUCCESS. Robocopy exit code $ExitCode"

                # Update ONLY physical/external backup health.
                # Do not overwrite daily-local backup metadata.
                try {
                    $BackupStatusFile = Join-Path $Source "data\runtime\backup_status.json"
                    $NowIso = (Get-Date).ToString("o")

                    if (Test-Path $BackupStatusFile) {
                        $DashboardStatus = Get-Content `
                            $BackupStatusFile `
                            -Raw | ConvertFrom-Json
                    }
                    else {
                        $DashboardStatus = [PSCustomObject]@{
                            last_attempt = $null
                            last_success = $null
                            last_backup_type = $null
                            last_backup_path = $null
                            last_backup_success = $null
                            external_available = $true
                            external_backup_root = $BackupRoot
                            last_external_success = $null
                            last_external_backup_path = $null
                            last_local_success = $null
                            last_local_backup_path = $null
                            fallback_reason = $null
                        }
                    }

                    $DashboardStatus.external_available = $true
                    $DashboardStatus.external_backup_root = $BackupRoot
                    $DashboardStatus.last_external_success = $NowIso
                    $DashboardStatus.last_external_backup_path = $Destination

                    $DashboardStatus |
                        ConvertTo-Json -Depth 10 |
                        Set-Content $BackupStatusFile -Encoding UTF8

                    Write-WatcherLog "External backup health status updated."
                }
                catch {
                    Write-WatcherLog "STATUS UPDATE ERROR: $($_.Exception.Message)"
                }

                # Synchronize the dashboard status after a successful
                # automatic external-drive backup.
                try {
                    $BackupStatusFile = Join-Path $Source "data\runtime\backup_status.json"
                    $BackupStatusDirectory = Split-Path $BackupStatusFile

                    if (-not (Test-Path $BackupStatusDirectory)) {
                        New-Item -ItemType Directory `
                            -Path $BackupStatusDirectory `
                            -Force | Out-Null
                    }

                    $PreviousStatus = $null

                    if (Test-Path $BackupStatusFile) {
                        try {
                            $PreviousStatus = Get-Content `
                                $BackupStatusFile `
                                -Raw | ConvertFrom-Json
                        }
                        catch {
                            $PreviousStatus = $null
                        }
                    }

                    $NowIso = (Get-Date).ToString("o")

                    $DashboardStatus = [ordered]@{
                        last_attempt = $NowIso
                        last_success = $NowIso
                        last_backup_type = "EXTERNAL"
                        last_backup_path = $Destination
                        last_backup_success = $true
                        external_available = $true
                        external_backup_root = $BackupRoot
                        last_external_success = $NowIso
                        last_external_backup_path = $Destination
                        last_local_success = if ($PreviousStatus) {
                            $PreviousStatus.last_local_success
                        }
                        else {
                            $null
                        }
                        last_local_backup_path = if ($PreviousStatus) {
                            $PreviousStatus.last_local_backup_path
                        }
                        else {
                            $null
                        }
                        fallback_reason = $null
                    }

                    $DashboardStatus |
                        ConvertTo-Json -Depth 4 |
                        Set-Content $BackupStatusFile -Encoding UTF8

                    Write-WatcherLog "Dashboard backup status updated for external backup."
                }
                catch {
                    Write-WatcherLog "STATUS UPDATE ERROR: $($_.Exception.Message)"
                }

                # After every successful external backup, ask the existing
                # monthly restore verifier whether a restore test is due.
                # NOT_DUE means no restore test is performed.
                try {
                    $PythonCommand = "C:\Users\Chris\AppData\Local\Programs\Python\Python313\python.exe"

                    if (-not (Test-Path $PythonCommand)) {
                        $PythonCommand = (Get-Command python -ErrorAction Stop).Source
                    }

                    $RestoreJson = & $PythonCommand -c "import json,sys; sys.path.insert(0, r'$Source'); from utilities.restore_verifier import run_restore_test_if_due; print(json.dumps(run_restore_test_if_due(backup_path=r'$Destination'), default=str))" 2>&1
                    $RestoreExitCode = $LASTEXITCODE

                    if ($RestoreExitCode -eq 0) {
                        Write-WatcherLog "RESTORE CHECK: $RestoreJson"
                    }
                    else {
                        Write-WatcherLog "RESTORE CHECK ERROR (exit $RestoreExitCode): $RestoreJson"
                    }
                }
                catch {
                    Write-WatcherLog "RESTORE CHECK ERROR: $($_.Exception.Message)"
                }
            }
            else {

                $FailureFile = Join-Path $Destination "_BACKUP_FAILED.txt"

                "Backup failed. Robocopy Exit Code: $ExitCode" |
                    Set-Content $FailureFile

                Write-WatcherLog "BACKUP FAILED. Robocopy exit code $ExitCode"
            }

            $WasConnected = $true
        }

        if (-not $Volume -and $WasConnected) {
            Write-WatcherLog "Extreme SSD disconnected."
            $WasConnected = $false
        }
    }
    catch {
        Write-WatcherLog "WATCHER ERROR: $($_.Exception.Message)"
    }

    Start-Sleep -Seconds $PollSeconds
}
