param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Nifti,

    [switch]$Fast
)

$ErrorActionPreference = "Stop"
$python = "C:\Users\respawn\venvs\totalseg\Scripts\python.exe"
$entrada = (Resolve-Path -LiteralPath $Nifti).Path
$bruto = Join-Path $PSScriptRoot "bruto"
$saida = Join-Path $PSScriptRoot "bruto\saida"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Ambiente TotalSegmentator não encontrado: $python"
}
if (-not (Test-Path -LiteralPath $bruto)) {
    New-Item -ItemType Directory -Path $bruto -Force | Out-Null
}
if (-not (Test-Path -LiteralPath $saida)) {
    New-Item -ItemType Directory -Path $saida -Force | Out-Null
} elseif (@(Get-ChildItem -LiteralPath $saida -Force).Count -gt 0) {
    throw "A pasta de saída já contém arquivos. Mova ou arquive-os antes de executar: $saida"
}

$cuda = & $python -I -c "import torch; print('true' if torch.cuda.is_available() else 'false')"
if ($LASTEXITCODE -ne 0) { throw "Não foi possível consultar PyTorch/CUDA." }
$device = if ($cuda.Trim() -eq "true") { "gpu" } else { "cpu" }
$argumentos = @("-i", $entrada, "-o", $saida, "--task", "total", "--device", $device)
if ($Fast) { $argumentos += "--fast" }

Write-Host "Entrada: $entrada"
Write-Host "Dispositivo: $device"
if ($Fast) { Write-Host "Modelo: --fast (3 mm, menor uso de memória)" }
& $python -I -c "from totalsegmentator.bin.TotalSegmentator import main; main()" @argumentos
if ($LASTEXITCODE -ne 0) {
    if ($device -eq "gpu" -and -not $Fast) {
        Write-Warning "A execução normal falhou. Se a saída indicar falta de memória CUDA, repita com -Fast."
    }
    throw "TotalSegmentator terminou com código $LASTEXITCODE."
}
