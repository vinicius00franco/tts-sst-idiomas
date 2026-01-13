# Diretrizes para Análise do Contexto do Código

## Objetivo do Projeto
Este projeto visa desenvolver um sistema de Text-to-Speech (TTS) e Speech-to-Text (SST) utilizando modelos ONNX, com foco em vozes em português brasileiro e outros idiomas. O objetivo principal é fornecer ferramentas para conversão de texto em áudio e vice-versa, utilizando bibliotecas como Piper e eSpeak-ng para síntese de voz.

### Regras Gerais do Código
- **Estrutura Modular**: O código deve ser organizado em módulos separados para TTS, SST, download de vozes e testes.
- **Compatibilidade**: Usar Python 3.x, com dependências gerenciadas via virtualenv.
- **Documentação**: Todos os scripts devem ter comentários explicativos e docstrings.
- **Testes**: Implementar testes automatizados para validar funcionalidades.
- **Licenciamento**: Código deve seguir licenças open-source compatíveis.

### Análise de Contexto
- **Dependências**: Verificar se todas as bibliotecas necessárias estão instaladas (ex: onnxruntime, numpy).
- **Modelos**: Os modelos ONNX devem ser baixados e organizados na pasta `models/`.
- **Dados**: Arquivos de dados como listas de conversas e histórias estão em `data/`.
- **Scripts**: Scripts em `scripts/` para execução de tarefas específicas.
- **Saídas**: Resultados de TTS em `outputs/`.

### Diretrizes para Desenvolvimento
- Sempre validar sintaxe antes de executar.
- Usar versionamento Git para rastrear mudanças.
- Manter compatibilidade com diferentes sistemas operacionais (Linux, Windows).
- Priorizar performance e eficiência nos modelos de IA.
- **Registro de Mudanças**: Todas as mudanças no projeto devem ser registradas no arquivo `CHANGES.md`, organizadas em tópicos e subtópicos para facilitar o acompanhamento e a documentação das evoluções.