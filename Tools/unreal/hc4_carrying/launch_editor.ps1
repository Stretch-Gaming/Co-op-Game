$ErrorActionPreference = 'Stop'
$hc4Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ($hc4Root -ne 'C:\Users\Stretch\.codex\worktrees\hc4-carrying\Co op Game') { throw 'Wrong workspace' }
if (Get-NetTCPConnection -LocalPort 8024 -State Listen -ErrorAction SilentlyContinue) { throw 'Port already occupied' }
$hc4Args = @(('"' + $hc4Root + '/CoopGame.uproject"'), ('-ExecutePythonScript="' + $PSScriptRoot + '/editor_loop.py"'), '-ModelContextProtocolStartServer', '-ModelContextProtocolPort=8024', '-nosplash', '-nop4', '-NoRestoreOpenAssetTabs', '-ini:EditorPerProjectUserSettings:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:bAutoStartServer=False', ('-abslog="' + $hc4Root + '/Saved/Logs/HC4.log"'))
(Start-Process -FilePath 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' -ArgumentList $hc4Args -WindowStyle Hidden -PassThru).Id
