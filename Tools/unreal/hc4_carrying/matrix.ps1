param([int]$Players=3)
$ErrorActionPreference='Stop'
$hc4Root=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ($hc4Root -ne 'C:\Users\Stretch\.codex\worktrees\hc4-carrying\Co op Game') { throw 'Wrong worktree' }
function Act($value) { & (Join-Path $PSScriptRoot 'action.ps1') ($value | ConvertTo-Json -Compress) }
& (Join-Path $PSScriptRoot 'slate.ps1') -Tool IsPIERunning -Arguments '{}' -Toolset 'EditorToolset.EditorAppToolset' | Out-Null
$hc4Running=((Get-Content -LiteralPath (Join-Path $hc4Root 'Saved/HC4/mcp_response.json') -Raw | ConvertFrom-Json).result.content.text | ConvertFrom-Json).returnValue
if ($hc4Running) { & (Join-Path $PSScriptRoot 'slate.ps1') -Tool StopPIE -Arguments '{}' -Toolset 'EditorToolset.EditorAppToolset' }
@{players=$Players;net='client'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $hc4Root 'Saved/HC4/test_options.json')
& (Join-Path $PSScriptRoot 'run_editor.ps1') prepare_pie.py -Quiet
& (Join-Path $PSScriptRoot 'slate.ps1') -Tool StartPIE -Arguments '{"options":{"bSimulate":false,"playMode":"PlayMode_InEditorFloating","warmupSeconds":2}}' -Toolset 'EditorToolset.EditorAppToolset'
for ($hc4Try=0; $hc4Try -lt 15; $hc4Try++) {
    Act @{command='snapshot'} | Out-Null
    $hc4Read=(Get-Content -LiteralPath (Join-Path $hc4Root 'Saved/HC4/response.json') -Raw | ConvertFrom-Json).result.worlds
    $hc4Ready=@($hc4Read | Where-Object { $_.players.Count -ne $Players -or @($_.players | Where-Object { $null -eq $_.id }).Count }).Count -eq 0
    if ($hc4Ready) { break }
    Start-Sleep -Milliseconds 500
}
if (!$hc4Ready) { throw 'Network players have not finished initializing' }
Act @{command='snapshot';label="initial_$Players"} | Out-Null
$hc4Indices=@(0..($Players-1))
foreach ($hc4I in $hc4Indices) { Act @{command='setup';player=$hc4I;tag="HC4_BP_Carryable_$hc4I"} | Out-Null }
Start-Sleep -Milliseconds 600
foreach ($hc4I in $hc4Indices) { Act @{command='aim';client=$hc4I;tag="HC4_BP_Carryable_$hc4I"} | Out-Null }
Start-Sleep -Milliseconds 400
foreach ($hc4I in $hc4Indices) { Act @{command='aim';client=$hc4I;tag="HC4_BP_Carryable_$hc4I"} | Out-Null }
Start-Sleep -Milliseconds 500
Act @{command='input';action='/Game/Core/Input/IA_Interact';subsystems=$hc4Indices;duration=0.3} | Out-Null
Start-Sleep -Milliseconds 1800
Act @{command='snapshot';label="pickup_$Players"} | Out-Null
Act @{command='input';action='/Game/Core/Input/IA_Drop';subsystems=$hc4Indices;duration=0.2} | Out-Null
Start-Sleep -Milliseconds 1800
Act @{command='snapshot';label="drop_$Players"} | Out-Null
foreach ($hc4I in $hc4Indices) { Act @{command='aim';client=$hc4I;tag="HC4_BP_Carryable_$hc4I"} | Out-Null }
Start-Sleep -Milliseconds 500
Act @{command='input';action='/Game/Core/Input/IA_Interact';subsystems=$hc4Indices;duration=0.3} | Out-Null
Start-Sleep -Milliseconds 1800
Act @{command='snapshot';label="repickup_$Players"} | Out-Null
Act @{command='input';action='/Game/Puzzles/Test/HC4/IA_HC4Reset';duration=0.2} | Out-Null
Start-Sleep -Milliseconds 1800
foreach ($hc4I in $hc4Indices) { Act @{command='setup';player=$hc4I;tag="HC4_BP_KeyRelic_$hc4I"} | Out-Null }
Start-Sleep -Milliseconds 500
foreach ($hc4I in $hc4Indices) { Act @{command='aim';client=$hc4I;tag="HC4_BP_KeyRelic_$hc4I"} | Out-Null }
Start-Sleep -Milliseconds 500
Act @{command='input';action='/Game/Core/Input/IA_Interact';subsystems=$hc4Indices;duration=0.3} | Out-Null
Start-Sleep -Milliseconds 1800
Act @{command='snapshot';label="heavy_$Players"} | Out-Null
Act @{command='input';action='/Game/Puzzles/Test/HC4/IA_HC4Reset';duration=0.2} | Out-Null
Start-Sleep -Milliseconds 1800
Act @{command='snapshot';label="reset_$Players"} | Out-Null
"Completed $Players-player fixture scenarios; independent evidence assertions follow."
