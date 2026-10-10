param([string]$Method,[string]$Json='{}')
$ErrorActionPreference='Stop'
$hc3Ready=Get-Content -Raw (Join-Path $PSScriptRoot 'ready.json')|ConvertFrom-Json
if($hc3Ready.project -ne 'C:\Users\Stretch\.codex\worktrees\revive-recovery\Co op Game' -or $hc3Ready.port -ne 8043){throw 'Wrong editor'}
$hc3Headers=@{'Content-Type'='application/json';Accept='application/json, text/event-stream';'Mcp-Session-Id'=(Get-Content -Raw (Join-Path $PSScriptRoot 'mcp-session.txt')).Trim()}
$hc3Payload=@{jsonrpc='2.0';id=3;method='tools/call';params=@{name=$Method;arguments=($Json|ConvertFrom-Json)}}|ConvertTo-Json -Depth 30
$hc3Response=Invoke-WebRequest -Uri http://127.0.0.1:8043/mcp -Method Post -Headers $hc3Headers -Body $hc3Payload
$hc3Response.Content|Set-Content (Join-Path $PSScriptRoot 'mcp-result.json')
$hc3Response.Content
