$ErrorActionPreference='Stop'
$hc5Root=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path.Replace('\','/')
if ($hc5Root -ne 'C:/Users/Stretch/.codex/worktrees/round-progression/Co op Game') { throw 'Wrong workspace' }
if (Get-NetTCPConnection -LocalPort 8041 -State Listen -ErrorAction SilentlyContinue) { throw 'Port already occupied' }
$hc5Command=Join-Path $PSScriptRoot 'command.json'
if (Test-Path -LiteralPath $hc5Command) { Remove-Item -LiteralPath $hc5Command }
$hc5Args=@(('"'+$hc5Root+'/CoopGame.uproject"'),('-ExecutePythonScript="'+$hc5Root+'/Tools/unreal/hc5_rounds/editor_loop.py"'),'-ModelContextProtocolStartServer','-ModelContextProtocolPort=8041','-NullRHI','-unattended','-nosplash','-nop4','-NoRestoreOpenAssetTabs','-ini:EditorPerProjectUserSettings:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:bAutoStartServer=False',('-abslog="'+$hc5Root+'/Saved/Logs/HC5.log"'))
(Start-Process 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' -ArgumentList $hc5Args -WindowStyle Hidden -PassThru).Id
