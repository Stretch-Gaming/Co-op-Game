param([string]$Script,[string]$Json='{}')
$ErrorActionPreference='Stop'
$hc3Root=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ($hc3Root -ne 'C:\Users\Stretch\.codex\worktrees\revive-recovery\Co op Game') { throw 'Wrong checkout' }
$hc3Ready=Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'ready.json') | ConvertFrom-Json
if ($hc3Ready.project -ne $hc3Root -or $hc3Ready.port -ne 8043) { throw 'Wrong editor identity' }
$hc3ID=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
@{id=$hc3ID;script=$Script;args=($Json|ConvertFrom-Json)} | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'command.json')
$hc3End=(Get-Date).AddSeconds(90)
while((Get-Date) -lt $hc3End) {
 Start-Sleep -Milliseconds 200
 if(Test-Path (Join-Path $PSScriptRoot 'command-result.json')) {
  $hc3Result=Get-Content -Raw (Join-Path $PSScriptRoot 'command-result.json') | ConvertFrom-Json
  if($hc3Result.id -eq $hc3ID){$hc3Result|ConvertTo-Json -Depth 20;if(-not $hc3Result.ok){throw $hc3Result.error};return}
 }
}
throw 'Isolated editor timeout'
