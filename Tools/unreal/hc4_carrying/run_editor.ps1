param([Parameter(Mandatory=$true)][string]$Script,[switch]$Quiet)
$ErrorActionPreference = 'Stop'
$hc4Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ($hc4Root -ne 'C:\Users\Stretch\.codex\worktrees\hc4-carrying\Co op Game') { throw 'Wrong worktree' }
$hc4Queue = Join-Path $hc4Root 'Saved/HC4'
$hc4Identity = Get-Content -LiteralPath (Join-Path $hc4Queue 'identity.json') -Raw | ConvertFrom-Json
if ($hc4Identity.project.Replace('/', '\') -ne (Join-Path $hc4Root 'CoopGame.uproject')) { throw 'Wrong editor identity' }
$hc4Process = Get-CimInstance Win32_Process -Filter "name = 'UnrealEditor.exe'" | Where-Object { $_.CommandLine.Replace('\','/') -like '*worktrees/hc4-carrying*' -and $_.CommandLine -like '*ModelContextProtocolPort=8024*' }
if (@($hc4Process).Count -ne 1) { throw 'Dedicated editor missing or ambiguous' }
$hc4Response = Join-Path $hc4Queue 'response.json'
if (Test-Path -LiteralPath $hc4Response) { Remove-Item -LiteralPath $hc4Response }
$hc4Request=Join-Path $hc4Queue 'request.json'
if (Test-Path -LiteralPath $hc4Request) { throw 'An editor command is already queued' }
@{script=('Tools/unreal/hc4_carrying/' + $Script)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $hc4Queue 'request.tmp') -Encoding utf8
Move-Item -LiteralPath (Join-Path $hc4Queue 'request.tmp') -Destination $hc4Request
$hc4Deadline = (Get-Date).AddSeconds(55)
while (!(Test-Path -LiteralPath $hc4Response) -and (Get-Date) -lt $hc4Deadline) { Start-Sleep -Milliseconds 300 }
if (!(Test-Path -LiteralPath $hc4Response)) { throw 'Editor response pending; do not enqueue another command' }
$hc4Result=Get-Content -LiteralPath $hc4Response -Raw
if (!$Quiet -or !(($hc4Result | ConvertFrom-Json).ok)) { $hc4Result }
if (!(($hc4Result | ConvertFrom-Json).ok)) { throw 'Editor command failed; inspect response.json' }
