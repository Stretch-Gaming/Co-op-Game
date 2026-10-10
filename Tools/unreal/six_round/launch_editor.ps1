param([switch]$Graphics)
$sixRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$sixExpected = 'C:\Users\Stretch\.codex\worktrees\six-round-adventure\Co op Game'
if ([IO.Path]::GetFullPath($sixRoot) -ne $sixExpected) { throw 'Wrong checkout' }
$sixRunning = Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe'" | Where-Object { $_.CommandLine -and $_.CommandLine.Replace('\','/').Contains($sixExpected.Replace('\','/')) }
if ($sixRunning) { throw 'This task editor is already running; do not launch another' }
$sixMode = if ($Graphics) { '-d3d11 -noraytracing' } else { '-NullRHI -unattended' }
$sixArgs = '"' + $sixRoot + '/CoopGame.uproject" /Engine/Maps/Entry ' + $sixMode + ' -nosplash -nop4 -NoRestoreOpenAssetTabs -ExecutePythonScript="' + $PSScriptRoot + '/editor_loop.py" -ModelContextProtocolStartServer -ModelContextProtocolPort=8061 -ini:EditorPerProjectUserSettings:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:bAutoStartServer=False -abslog="' + $sixRoot + '/Saved/SixRound/editor-current.log"'
$sixProcess = Start-Process -FilePath 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe' -ArgumentList $sixArgs -WindowStyle Hidden -PassThru
$sixProcess.Id | Set-Content (Join-Path $sixRoot 'Saved/SixRound/editor.pid')
$sixProcess.Id
