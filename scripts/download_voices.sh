#!/usr/bin/env bash
set -euo pipefail
voices=(
  en_US-ryan-medium
  en_US-joe-medium
  en_GB-alan-medium
  en_GB-jenny_dioco-medium
  es_ES-davefx-medium
  es_ES-sharvard-medium
  es_MX-ald-medium
  es_AR-daniela-high
)
cd "$(dirname "$0")/.."/models
for v in "${voices[@]}"; do
  # Parse voice ID: e.g., en_US-ryan-medium -> family=en, region=US, voice=ryan, quality=medium
  if [[ $v =~ ^([a-z]+)_([A-Z]+)-([a-z0-9_]+)-([a-z_]+)$ ]]; then
    family="${BASH_REMATCH[1]}"
    region="${BASH_REMATCH[2]}"
    voice_name="${BASH_REMATCH[3]}"
    quality="${BASH_REMATCH[4]}"
    base="https://huggingface.co/rhasspy/piper-voices/resolve/main/$family/${family}_$region/$voice_name/$quality"
    echo "Baixando $v (.onnx e .onnx.json)"
    wget -q -nc "$base/$v.onnx" -O "$v.onnx" || echo "Falha ONNX: $v"
    wget -q -nc "$base/$v.onnx.json" -O "$v.onnx.json" || echo "Falha JSON: $v"
  else
    echo "Formato inválido: $v"
  fi
done
echo "Concluído."