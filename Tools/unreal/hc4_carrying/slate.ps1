param([string]$Tool='Snapshot',[string]$Arguments='{"ref":"w5","maxDepth":60}',[string]$Filter='',[string]$Toolset='SlateInspectorToolset.SlateInspectorToolset')
$ErrorActionPreference='Stop'
$hc4Root=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ($hc4Root -ne 'C:\Users\Stretch\.codex\worktrees\hc4-carrying\Co op Game') { throw 'Wrong worktree' }
& (Join-Path $PSScriptRoot 'run_editor.ps1') 'verify_identity.py' | Out-Null
$hc4Payload=@{method='tools/call';params=@{name='call_tool';arguments=@{toolset_name=$Toolset;tool_name=$Tool;arguments=($Arguments | ConvertFrom-Json)}}}
$hc4Payload | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $hc4Root 'Saved/HC4/mcp_request.json') -Encoding utf8
& 'C:\Users\Stretch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' (Join-Path $PSScriptRoot 'mcp_call.py') (Join-Path $hc4Root 'Saved/HC4/mcp_request.json') 0
$hc4Resp=Get-Content -LiteralPath (Join-Path $hc4Root 'Saved/HC4/mcp_response.json') -Raw | ConvertFrom-Json
if ($hc4Resp.result.isError -or $hc4Resp.error) { throw ($hc4Resp | ConvertTo-Json -Depth 8 -Compress) }
$hc4Text=($hc4Resp.result.content.text | ConvertFrom-Json).returnValue
if ($Tool -eq 'Snapshot') { $hc4Text | Set-Content -LiteralPath (Join-Path $hc4Root 'Saved/HC4/slate.txt') }
if ($Filter) { ($hc4Text -split "`n") | Select-String -Pattern $Filter } else { $hc4Text }
