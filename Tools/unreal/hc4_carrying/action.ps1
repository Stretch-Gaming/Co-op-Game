param([Parameter(Mandatory=$true)][string]$Json)
$ErrorActionPreference='Stop'
$hc4Root=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ($hc4Root -ne 'C:\Users\Stretch\.codex\worktrees\hc4-carrying\Co op Game') { throw 'Wrong worktree' }
$Json | Set-Content -LiteralPath (Join-Path $hc4Root 'Saved/HC4/action.json') -Encoding utf8
& (Join-Path $PSScriptRoot 'run_editor.ps1') runtime_action.py -Quiet
$hc4R=(Get-Content -LiteralPath (Join-Path $hc4Root 'Saved/HC4/response.json') -Raw | ConvertFrom-Json).result
if ($hc4R.worlds) {
    foreach ($hc4W in $hc4R.worlds) {
        @{world=$hc4W.world;server=$hc4W.server;players=$hc4W.players;activeItems=@($hc4W.items | Where-Object state -ne 0)} | ConvertTo-Json -Depth 8 -Compress
    }
} else { $hc4R | ConvertTo-Json -Depth 6 -Compress }
