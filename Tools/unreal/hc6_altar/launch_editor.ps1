$ErrorActionPreference = 'Stop'
$hc6Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ($hc6Root -ne 'C:\Users\Stretch\.codex\worktrees\altar-challenge\Co op Game') { throw 'Wrong workspace' }
if (Get-NetTCPConnection -LocalPort 8042 -State Listen -ErrorAction SilentlyContinue) { throw 'Port already occupied' }
$hc6Args = @(('"' + $hc6Root + '/CoopGame.uproject"'), ('-ExecutePythonScript="' + $PSScriptRoot + '/editor_loop.py"'), '-ModelContextProtocolStartServer', '-ModelContextProtocolPort=8042', '-nosplash', '-nop4', '-NoRestoreOpenAssetTabs', '-ini:EditorPerProjectUserSettings:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:bAutoStartServer=False', ('-abslog="' + $hc6Root + '/Saved/Logs/HC6Altar.log"'))
(Start-Process -FilePath 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' -ArgumentList $hc6Args -WindowStyle Hidden -PassThru).Id

