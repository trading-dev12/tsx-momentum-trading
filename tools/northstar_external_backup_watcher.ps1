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

