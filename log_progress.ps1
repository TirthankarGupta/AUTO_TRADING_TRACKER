# log_progress.ps1
# Usage: ./log_progress.ps1 "your session notes here"
# Appends a new dated log entry to journal/Progress_Log.md

param(
    [string]$Notes
)

$journalPath = "journal\Progress_Log.md"

# Make sure journal folder exists
if (!(Test-Path "journal")) {
    New-Item -ItemType Directory -Path "journal" | Out-Null
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$entry = @"
---

## Session: $timestamp

$Notes

"@

Add-Content -Path $journalPath -Value $entry
Write-Host "Progress logged to $journalPath"
