
### Alterações
- Configuração inicial do ambiente virtual (venv).
- Compilação de sintaxe do script `tts_test.py` validada.
- Renomeação do arquivo `scripts/tts_test.py` para `scripts/audio_generation.py` para melhor refletir sua função de geração de áudios TTS.
- Atualização das importações em `scripts/run_tts.py` para referenciar o novo nome do arquivo.
- Adição de geração dinâmica de texto de entrevista em inglês usando LangChain com OpenAI GPT-3.5-turbo, seguindo boas práticas de código e princípios SOLID (Single Responsibility, Open-Closed, etc.). Inclui limpeza de prompt antes de envio ao LLM.
- Separação da classe InterviewGenerator em arquivo dedicado `scripts/interview_generator.py` e migração para uso de modelo LLM local otimizado para CPU (Hugging Face Transformers com distilgpt2), removendo dependência de APIs externas para melhor performance e privacidade.
- Refatoração da classe InterviewGenerator para usar llama-cpp-python com modelos GGUF (Llama/Qwen) otimizados em C++ para CPU, melhorando performance e reduzindo latência. Suporte a modelos como Llama 3.2 ou Qwen 2.5, com chat templates adequados.
- Ajuste de `n_threads=3` na classe InterviewGenerator para otimizar uso de CPU com 4 núcleos físicos.
- Download dos modelos GGUF otimizados: Llama-3.2-3B-Instruct-Q4_K_M.gguf e Qwen2.5-1.5B-Instruct-Q4_K_M.gguf do Hugging Face (bartowski), para uso local em CPU.
- Implementação do Builder Pattern para configuração opcional da classe InterviewGenerator (model_type e specialist).
- Adição de processamento sequencial para especialista "grammar": gera diálogo base e depois corrige gramaticalmente em segunda chamada ao LLM.
- Integração com Qdrant para salvar textos gerados ("generated") e corrigidos ("corrected") em disco, usando embeddings SentenceTransformer para busca por similaridade.
- Criação de script `scripts/query_qdrant.py` para consultar coleções Qdrant e comparar diferenças entre textos gerados e corrigidos usando difflib.
- Lazy-initialization de Qdrant e modelo de embeddings para evitar downloads desnecessários quando especialista não é usado.
- Correções para evitar erros de shutdown do Qdrant (graceful close via atexit) e uso de UUIDs para IDs únicos.
- Ajuste no parsing para remover artefatos indesejados como "Corrected dialogue:" antes de salvar no Qdrant.
- Correção de erro na API FastAPI: import de `Optional` e ajuste de campos Pydantic para evitar passagem de valores inválidos aos argumentos de linha de comando.