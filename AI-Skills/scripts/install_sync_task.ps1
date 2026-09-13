$ErrorActionPreference = 'Stop'

$taskName = 'AI-Skills Sync to localnet'
$syncScript = Join-Path $PSScriptRoot 'sync_localnet.py'
$pythonw = 'C:\Python314\pythonw.exe'
if (-not (Test-Path -LiteralPath $syncScript -PathType Leaf)) {
    throw "Synchronizer not found: $syncScript"
}
if (-not (Test-Path -LiteralPath $pythonw -PathType Leaf)) {
    throw "Python background executable not found: $pythonw"
}

$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing -and @($existing.Actions | Where-Object {
    $_.Execute -ne $pythonw -or $_.Arguments -ne ('"{0}"' -f $syncScript)
}).Count -gt 0) {
    throw 'An unrelated scheduled task uses this name; it was left unchanged.'
}

$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction -Execute $pythonw -Argument ('"{0}"' -f $syncScript) -WorkingDirectory $PSScriptRoot
$triggers = @(
    (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 15))
    (New-ScheduledTaskTrigger -AtLogOn -User $currentUser)
)
$principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -Hidden -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 3)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Description 'Synchronize the curated AI-Skills catalog to localnet every 15 minutes and at login while Jason is signed in. Uses existing SSH key authentication.' -Force | Out-Null
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State, @{Name='User'; Expression={$_.Principal.UserId}}
