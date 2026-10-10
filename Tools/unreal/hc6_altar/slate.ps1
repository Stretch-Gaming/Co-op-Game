param([string]$Tool='Snapshot',[string]$Arguments='{"ref":"w5","maxDepth":60}',[string]$Filter='',[string]$Toolset='SlateInspectorToolset.SlateInspectorToolset')
$ErrorActionPreference='Stop'
$hc6Root=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ($hc6Root -ne 'C:\Users\Stretch\.codex\worktrees\altar-challenge\Co op Game') { throw 'Wrong worktree' }
& (Join-Path $PSScriptRoot 'run_editor.ps1') 'verify_identity.py' | Out-Null
$hc6Payload=@{method='tools/call';params=@{name='call_tool';arguments=@{toolset_name=$Toolset;tool_name=$Tool;arguments=($Arguments | ConvertFrom-Json)}}}
$hc6Payload | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $hc6Root 'Saved/HC6Altar/mcp_request.json') -Encoding utf8
& 'C:\Users\Stretch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' (Join-Path $PSScriptRoot 'mcp_call.py') (Join-Path $hc6Root 'Saved/HC6Altar/mcp_request.json') 0
$hc6Resp=Get-Content -LiteralPath (Join-Path $hc6Root 'Saved/HC6Altar/mcp_response.json') -Raw | ConvertFrom-Json
if ($hc6Resp.result.isError -or $hc6Resp.error) { throw ($hc6Resp | ConvertTo-Json -Depth 8 -Compress) }
$hc6Text=($hc6Resp.result.content.text | ConvertFrom-Json).returnValue
if ($Tool -eq 'Snapshot') { $hc6Text | Set-Content -LiteralPath (Join-Path $hc6Root 'Saved/HC6Altar/slate.txt') }
if ($Filter) { ($hc6Text -split "`n") | Select-String -Pattern $Filter } else { $hc6Text }

