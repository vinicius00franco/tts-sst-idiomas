# Interface Web TTS-SST

Esta interface web permite testar as funcionalidades da API TTS-SST de forma visual e interativa.

## Funcionalidades

### 1. Sugerir Tópicos
- Permite sugerir tópicos de conversa baseados em um assunto
- Configurável por modelo (fast/reasoning), especialista (daily/grammar) e idioma (en/es)
- Clique em um tópico sugerido para selecioná-lo automaticamente

### 2. Gerar TTS
- Gera conversas em áudio a partir de um tópico selecionado
- Suporta múltiplos idiomas simultaneamente (inglês e espanhol)
- **Player de Áudio Integrado**: reproduz arquivos FLAC diretamente no navegador usando Howler.js
- Exibe a transcrição da conversa gerada
- Controles: Play ▶️, Pause ⏸️, Stop ⏹️

### 3. Consultar Qdrant
- Busca conversas similares armazenadas no banco vetorial Qdrant
- Útil para encontrar conversas anteriores sobre temas relacionados

## Reprodução de Áudio FLAC

A interface utiliza **Howler.js**, uma biblioteca JavaScript poderosa que suporta nativamente arquivos FLAC sem necessidade de conversão. Howler.js oferece:

- ✅ Suporte nativo a FLAC via HTML5 Audio API
- ✅ Controle completo de reprodução (play, pause, stop)
- ✅ Callbacks para eventos de carregamento e reprodução
- ✅ Melhor compatibilidade cross-browser
- ✅ Streaming eficiente de arquivos grandes

### Por que Howler.js?

Arquivos FLAC não são nativamente suportados pelo elemento `<audio>` HTML5 em todos os navegadores. Howler.js resolve esse problema usando a Web Audio API e fallbacks inteligentes para garantir compatibilidade máxima.

## Como Usar

1. **Inicie o servidor FastAPI**:
   ```bash
   source venv/bin/activate
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **Acesse a interface**:
   - Via FastAPI: http://localhost:8000/web/index.html
   - Ou use um servidor local (Live Server, etc): http://127.0.0.1:5500/web/index.html

3. **Fluxo de uso**:
   1. Digite um assunto e clique em "Sugerir" para obter tópicos
   2. Clique em um tópico sugerido ou digite um personalizado
   3. Selecione os idiomas desejados
   4. Clique em "Gerar" e aguarde
   5. Use os controles de áudio para ouvir a conversa gerada
   6. Leia a transcrição abaixo do player

## Tecnologias

- **HTML5**: Estrutura semântica
- **CSS3**: Design responsivo e moderno
- **JavaScript (Vanilla)**: Sem frameworks, performance otimizada
- **Howler.js 2.2.4**: Reprodução de áudio FLAC
- **FastAPI**: Backend para servir arquivos e API

## Observações

- Os arquivos de áudio são salvos em `/outputs/` e servidos estaticamente
- As conversas são armazenadas no Qdrant para consultas futuras
- O player exibe status visual durante carregamento, reprodução e pausa
- Console do navegador mostra logs detalhados para debug
