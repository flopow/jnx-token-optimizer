# powershell / jnx.ps1 / PowerShell 5.1+ / Windows installer / JNX token optimizer
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'JNX'
$bin = Join-Path $root 'bin'
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$source = Join-Path $PSScriptRoot 'jnx.py'
if (!(Test-Path $source)) { throw "jnx.py not found beside installer" }
Copy-Item $source (Join-Path $root 'jnx.py') -Force
$mcp = Join-Path $PSScriptRoot 'mcp.py'
if (Test-Path $mcp) { Copy-Item $mcp (Join-Path $root 'mcp.py') -Force }
$launcher = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } elseif (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { throw 'Python 3.11+ is required. Install it from python.org and rerun.' }
$cmd = "@echo off`r`n$launcher `"$root\jnx.py`" %*`r`n"
Set-Content -Path (Join-Path $bin 'jnx.cmd') -Value $cmd -Encoding ASCII
$mcpCmd = "@echo off`r`n$launcher `"$root\mcp.py`" %*`r`n"
Set-Content -Path (Join-Path $bin 'jnx-mcp.cmd') -Value $mcpCmd -Encoding ASCII
$userPath = [Environment]::GetEnvironmentVariable('Path','User')
if (($userPath -split ';') -notcontains $bin) { [Environment]::SetEnvironmentVariable('Path', (($userPath.TrimEnd(';') + ';' + $bin).Trim(';')), 'User') }
$env:JNX_HOME = Join-Path $env:USERPROFILE '.jnx'
& $launcher (Join-Path $root 'jnx.py') init
Write-Host "JNX installed. Open a new terminal, then run: jnx init"
