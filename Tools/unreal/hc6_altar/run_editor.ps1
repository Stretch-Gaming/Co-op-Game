param([Parameter(Mandatory=$true)][string]$Script,[switch]$Quiet)
$ErrorActionPreference = 'Stop'
$hc6Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ($hc6Root -ne 'C:\Users\Stretch\.codex\worktrees\altar-challenge\Co op Game') { throw 'Wrong worktree' }
$hc6Queue = Join-Path $hc6Root 'Saved/HC6Altar'
$hc6Identity = Get-Content -LiteralPath (Join-Path $hc6Queue 'identity.json') -Raw | ConvertFrom-Json
if ($hc6Identity.project.Replace('/', '\') -ne (Join-Path $hc6Root 'CoopGame.uproject')) { throw 'Wrong editor identity' }
$hc6Process = Get-CimInstance Win32_Process -Filter "name = 'UnrealEditor.exe'" | Where-Object { $_.CommandLine.Replace('\','/') -like '*worktrees/altar-challenge*' -and $_.CommandLine -like '*ModelContextProtocolPort=8042*' }
if (@($hc6Process).Count -ne 1) { throw 'Dedicated editor missing or ambiguous' }
$hc6Response = Join-Path $hc6Queue 'response.json'
if (Test-Path -LiteralPath $hc6Response) { Remove-Item -LiteralPath $hc6Response }
$hc6Request=Join-Path $hc6Queue 'request.json'
if (Test-Path -LiteralPath $hc6Request) { throw 'An editor command is already queued' }
@{script=('Tools/unreal/hc6_altar/' + $Script)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $hc6Queue 'request.tmp') -Encoding utf8
Move-Item -LiteralPath (Join-Path $hc6Queue 'request.tmp') -Destination $hc6Request
$hc6Deadline = (Get-Date).AddSeconds(55)
while (!(Test-Path -LiteralPath $hc6Response) -and (Get-Date) -lt $hc6Deadline) { Start-Sleep -Milliseconds 300 }
if (!(Test-Path -LiteralPath $hc6Response)) { throw 'Editor response pending; do not enqueue another command' }
$hc6Result=Get-Content -LiteralPath $hc6Response -Raw
if (!$Quiet -or !(($hc6Result | ConvertFrom-Json).ok)) { $hc6Result }
if (!(($hc6Result | ConvertFrom-Json).ok)) { throw 'Editor command failed; inspect response.json' }

