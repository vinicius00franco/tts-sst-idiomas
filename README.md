# TTS-SST Project

Este projeto utiliza o Piper TTS para gerar áudio a partir de texto em português, inglês e espanhol.

## Estrutura do Projeto

- `models/`: Modelos TTS (.onnx e .json)
- `outputs/`: Arquivos de áudio gerados (.flac, .wav)
- `data/`: Dados auxiliares (espeak-ng, listas de texto)
- `scripts/`: Scripts Python e notebooks
- `venv/`: Ambiente virtual Python
- `old/`: Arquivos não utilizados

## Como usar

1. Ative o ambiente virtual: `source venv/bin/activate`
2. Execute o script: `python scripts/tts_test.py`

O script gera:
- Testes unitários em WAV e FLAC para PT e EN
- Áudio multi-voz por idioma (até 3 vozes por gênero)
- Conversação concatenada em FLAC

## Vozes Disponíveis

### Português (PT-BR)
- Masculino: faber, cadu, jeff
- Feminino: (nenhuma disponível no catálogo oficial)

### Inglês (EN-US/GB)
- Masculino: ryan, joe, alan
- Feminino: lessac, amy, jenny_dioco

### Espanhol (ES/MX/AR)
- Masculino: davefx, sharvard, ald
- Feminino: daniela

## Dependências

- piper-tts
- soundfile
- numpy
- ffmpeg (para concatenação)

## Download de Vozes

Para baixar vozes adicionais, use o script `scripts/download_voices.sh` ou baixe manualmente de https://huggingface.co/rhasspy/piper-voices