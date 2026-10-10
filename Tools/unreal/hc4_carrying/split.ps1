$ErrorActionPreference='Stop'
$hc4Root=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ($hc4Root -ne 'C:\Users\Stretch\.codex\worktrees\hc4-carrying\Co op Game') { throw 'Wrong worktree' }
function Act($v) { & (Join-Path $PSScriptRoot 'action.ps1') ($v | ConvertTo-Json -Compress) }
@{players=3;net='listen'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $hc4Root 'Saved/HC4/test_options.json')
& (Join-Path $PSScriptRoot 'run_editor.ps1') prepare_pie.py -Quiet
& (Join-Path $PSScriptRoot 'slate.ps1') -Tool StartPIE -Arguments '{"options":{"bSimulate":false,"playMode":"PlayMode_InEditorFloating","warmupSeconds":3}}' -Toolset 'EditorToolset.EditorAppToolset'
Start-Sleep -Milliseconds 1800
Act @{command='input';action='/Game/Puzzles/Test/HC4/IA_HC4AddLocal';duration=0.3} | Out-Null
Start-Sleep -Milliseconds 1800
Act @{command='snapshot';label='split_initial'} | Out-Null
Act @{command='setup';player=0;tag='HC4_BP_Statue_0'} | Out-Null
Act @{command='setup';player=3;tag='HC4_BP_Statue_1'} | Out-Null
Start-Sleep -Milliseconds 600
foreach ($hc4I in 0..1) { Act @{command='aim';host=$true;local=$hc4I;tag="HC4_BP_Statue_$hc4I"} | Out-Null }
Start-Sleep -Milliseconds 500
foreach ($hc4I in 0..1) { Act @{command='aim';host=$true;local=$hc4I;tag="HC4_BP_Statue_$hc4I"} | Out-Null }
Start-Sleep -Milliseconds 500
Act @{command='input';action='/Game/Core/Input/IA_Interact';subsystems=@(0,1);duration=0.3} | Out-Null
Start-Sleep -Milliseconds 1300
Act @{command='snapshot';label='split_pickup'} | Out-Null
Act @{command='input';action='/Game/Core/Input/IA_Drop';subsystems=@(0);duration=0.3} | Out-Null
Start-Sleep -Milliseconds 1300
Act @{command='snapshot';label='split_drop_one'} | Out-Null
Act @{command='aim';host=$true;local=0;tag='HC4_BP_Statue_0'} | Out-Null
Start-Sleep -Milliseconds 500
Act @{command='input';action='/Game/Core/Input/IA_Interact';subsystems=@(0);duration=0.3} | Out-Null
Start-Sleep -Milliseconds 1300
Act @{command='snapshot';label='split_repickup'} | Out-Null
Act @{command='input';action='/Game/Puzzles/Test/HC4/IA_HC4Release';subsystems=@(1);duration=0.3} | Out-Null
Start-Sleep -Milliseconds 1300
Act @{command='snapshot';label='split_handoff'} | Out-Null
Act @{command='screenshot'} | Out-Null
Start-Sleep -Milliseconds 800
Act @{command='input';action='/Game/Puzzles/Test/HC4/IA_HC4Reset';subsystems=@(0);duration=0.3} | Out-Null
Start-Sleep -Milliseconds 1300
Act @{command='snapshot';label='split_reset'} | Out-Null
'Split-screen scenarios captured; run independent evidence assertions.'
