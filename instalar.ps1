<#
.SYNOPSIS
  Instala as skills de análise de dados como skills pessoais do Claude Code (e, opcionalmente, do Codex).
.DESCRIPTION
  Copia as pastas de skills/ para ~/.claude/skills. Não sobrescreve skill existente sem -Sobrescrever.
  Não registra MCP nem aceita termos: veja o README para o MCP do Power BI.
.EXAMPLE
  ./instalar.ps1
  ./instalar.ps1 -Codex -Sobrescrever
#>
param(
  [switch]$Codex,
  [switch]$Sobrescrever,
  [switch]$Dependencias
)
$ErrorActionPreference = 'Stop'
$origem = Join-Path $PSScriptRoot 'skills'
$destinos = @(Join-Path $HOME '.claude/skills')
if ($Codex) { $destinos += (Join-Path $HOME '.agents/skills') }

foreach ($dest in $destinos) {
  New-Item -ItemType Directory -Force $dest | Out-Null
  foreach ($skill in Get-ChildItem $origem -Directory) {
    $alvo = Join-Path $dest $skill.Name
    if ((Test-Path $alvo) -and -not $Sobrescrever) {
      Write-Warning "Já existe: $alvo (use -Sobrescrever para atualizar)"
      continue
    }
    if (Test-Path $alvo) {
      $backup = "$alvo.bak-$(Get-Date -Format yyyyMMddHHmmss)"
      Move-Item $alvo $backup
      Write-Host "Versão anterior guardada em $backup"
    }
    Copy-Item $skill.FullName $alvo -Recurse
    Write-Host "Instalada: $alvo"
  }
}

if ($Dependencias) {
  $py = (Get-Command python -ErrorAction SilentlyContinue)
  if (-not $py) { throw 'Python não encontrado no PATH.' }
  python -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
}
Write-Host "`nPronto. Dependências Python: pip install -r requirements.txt (ou rode com -Dependencias)."
