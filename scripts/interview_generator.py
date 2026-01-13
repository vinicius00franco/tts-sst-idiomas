from llama_cpp import Llama
import re
import sys
import os
import atexit
from uuid import uuid4
from typing import Optional
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


class InterviewGeneratorBuilder:
    """Builder para configurar InterviewGenerator de forma opcional."""
    
    def __init__(self):
        self.model_type = "fast"
        self.specialist = None
    
    def set_model_type(self, model_type: str):
        self.model_type = model_type
        return self
    
    def set_specialist(self, specialist: str):
        self.specialist = specialist
        return self
    
    def build(self):
        return InterviewGenerator(self.model_type, self.specialist)


class InterviewGenerator:
    """Gerador de entrevistas técnica utilizando modelos GGUF (Llama/Qwen)."""

    def __init__(self, model_type: str = "fast", specialist: Optional[str] = None):
        # Mapeamento de tipos para caminhos de modelos
        model_paths = {
            "fast": "models/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf",  # Modelo menor, mais rápido
            "reasoning": "models/Llama-3.2-3B-Instruct-Q4_K_M.gguf",  # Modelo maior, melhor raciocínio
        }
        
        model_path = model_paths.get(model_type, model_paths["fast"])
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo não encontrado: {model_path}")
        
        # Aumenta n_ctx para reduzir avisos e suportar prompts maiores
        n_ctx_map = {"fast": 16384, "reasoning": 32768}
        
        # Configuração para CPU: n_threads deve ser o número de núcleos físicos do seu PC
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx_map.get(model_type, 8192),  # Ajuste conforme modelo
            n_threads=3,      # Ajuste conforme seu processador
            verbose=False     # Desativa logs pesados do C++
        )
        
        self.specialist = specialist
        
        # Qdrant/Embedder serão inicializados sob demanda para evitar downloads desnecessários
        self.qdrant = None
        self.embedder = None
        
        # Registrar fechamento gracioso para evitar erro no shutdown
        atexit.register(self._close_qdrant)

    def suggest_topics(self, subject: str, target_lang: str = "en") -> list[str]:
        """Sugere 5 tópicos em Português (PT-BR) para uma conversa que será gerada em inglês ou espanhol."""
        lang_label = "Inglês" if target_lang == "en" else "Espanhol"
        sys_prompt = (
            "Você sugere temas de conversa para uma entrevista com base em um assunto. "
            f"A conversa será em {lang_label}. "
            "Responda em Português do Brasil e retorne apenas uma lista numerada com 5 opções de tema, curtas e objetivas, sem comentários extras."
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"Assunto: {subject}"},
        ]
        out = self.llm.create_chat_completion(messages=messages, max_tokens=256, temperature=0.4)
        txt = out["choices"][0]["message"]["content"].strip()
        lines = [ln.strip() for ln in txt.split('\n') if ln.strip()]
        # Remover numeração/traço e retornar lista simples
        topics = [re.sub(r'^\d+\.|^-\s*', '', ln).strip() for ln in lines]
        return topics[:5]

    def generate_english_interview_texts(self, selected_topic: str | None = None) -> list[tuple[str, str]]:
        # Primeiro, gerar diálogo base
        if self.specialist == "daily":
            sys_prompt = (
                "You are a casual interviewer in an everyday setting. Generate a relaxed, informal dialogue between Sarah (Interviewer) and Leo (Backend Candidate). "
                "Use everyday language, slang, common expressions, and informal terms. Make it sound like a natural conversation, not a formal interview. "
                "Topics: REST APIs, SQL, Docker, and Debugging, but discuss them in a laid-back way. "
                "Generate at least 12-16 dialogue exchanges (24-32 lines total) to create a substantial conversation. "
                "Format: Return ONLY the dialogue lines, one per line, prefixed with the speaker name: \"Sarah: [text]\" or \"Leo: [text]\". "
                "Start with Sarah, then alternate speakers logically."
            )
        else:
            sys_prompt = (
                "You are a technical recruiter. Generate a dialogue between Sarah (Interviewer) and Leo (Backend Candidate). "
                "Topics: REST APIs, SQL, Docker, and Debugging. "
                "Generate at least 12-16 dialogue exchanges (24-32 lines total) to create a complete interview. "
                "Format: Return ONLY the dialogue lines, one per line, prefixed with the speaker name: \"Sarah: [text]\" or \"Leo: [text]\". "
                "Start with Sarah, then alternate speakers logically."
            )
        messages = [
            {
                "role": "system",
                "content": sys_prompt
            },
            {"role": "user", "content": (
                f"Generate the interview now. Focus on the theme: {selected_topic}." if selected_topic else "Generate the interview now."
            )}
        ]

        output = self.llm.create_chat_completion(
            messages=messages,
            max_tokens=2500,
            temperature=0.7
        )

        raw_text = output["choices"][0]["message"]["content"]
        
        # Salvar generated no Qdrant quando especialista for selecionado
        if self.specialist:
            self._save_to_qdrant("generated", raw_text)
        
        # Se especialista em gramática, corrigir sequencialmente
        if self.specialist in ("grammar", "daily"):
            correction_messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert reviewer. Ensure the dialogue has a clear logical order: greeting, background, REST APIs, scalability/design, SQL optimization, Docker usage, debugging example, final wrap-up. "
                        "Ensure speakers alternate starting with Sarah, and every line is prefixed with 'Sarah:' or 'Leo:'. "
                        "If grammar specialist: correct grammar to standard formal English. If daily specialist: keep language natural and conversational. "
                        "IMPORTANT: Preserve the dialogue length. Do NOT shorten or summarize. Keep ALL exchanges from the original. "
                        "Keep the original meaning; do not add extra topics; maintain the number of lines."
                    )
                },
                {"role": "user", "content": f"Correct this dialogue:\n{raw_text}"}
            ]
            correction_output = self.llm.create_chat_completion(
                messages=correction_messages,
                max_tokens=2000,
                temperature=0.3  # Menos criatividade para correção/validação
            )
            corrected_text = correction_output["choices"][0]["message"]["content"]
            # Limpar artefatos indesejados
            corrected_text = re.sub(r'^Corrected dialogue:\s*\n?', '', corrected_text).strip()
            # Salvar corrected
            self._save_to_qdrant("corrected", corrected_text)
            raw_text = corrected_text
        
        print(f"Raw text (tokens aproximados): {len(raw_text.split())}")
        structured = self._parse_dialogue_structured(raw_text)
        joined = ' '.join([t for _, t in structured])
        print(f"Parsed texts (linhas): {len(structured)}, tokens aproximados: {len(joined.split())}")
        print(f"Tokens removidos: {len(raw_text.split()) - len(joined.split())}")
        return structured

    def _parse_dialogue_structured(self, text: str) -> list[tuple[str, str]]:
        """Retorna lista de tuplas (speaker, text), garantindo alternância lógica se ausente."""
        lines = [ln for ln in text.strip().split('\n') if ln.strip()]
        result: list[tuple[str, str]] = []
        for ln in lines:
            m = re.match(r'^(Sarah|Leo):\s*(.*)$', ln.strip())
            if m:
                speaker, content = m.group(1), m.group(2).strip()
                result.append((speaker, content))
            else:
                # Sem prefixo, aplicar alternância: começa com Sarah
                speaker = 'Sarah' if len(result) % 2 == 0 else 'Leo'
                result.append((speaker, ln.strip()))
        # Garantir alternância simples
        fixed: list[tuple[str, str]] = []
        for i, (spk, content) in enumerate(result):
            expected = 'Sarah' if i % 2 == 0 else 'Leo'
            fixed.append((expected, content))
        return fixed

    def generate_spanish_interview_texts(self, selected_topic: str | None = None) -> list[tuple[str, str]]:
        """Gera diálogo em espanhol, mantendo nomes 'Sarah' e 'Leo' para mapear vozes."""
        if self.specialist == "daily":
            sys_prompt = (
                "Eres un entrevistador casual en un entorno cotidiano. Genera un diálogo relajado e informal entre Sarah (Entrevistadora) y Leo (Candidato Backend). "
                "Usa lenguaje cotidiano, jerga, expresiones comunes y términos informales. Haz que suene como una conversación natural, no una entrevista formal. "
                "Temas: APIs REST, SQL, Docker y Depuración, pero discútelos de manera relajada. "
                "Genera al menos 12-16 intercambios de diálogo (24-32 líneas en total) para crear una conversación sustancial. "
                "Formato: Devuelve SOLO las líneas del diálogo, cada una con el nombre del hablante: 'Sarah: [texto]' o 'Leo: [texto]'. "
                "Empieza con Sarah y alterna de forma lógica."
            )
        else:
            sys_prompt = (
                "Eres un reclutador técnico. Genera un diálogo entre Sarah (Entrevistadora) y Leo (Candidato Backend). "
                "Temas: APIs REST, SQL, Docker y Depuración. "
                "Genera al menos 12-16 intercambios de diálogo (24-32 líneas en total) para crear una entrevista completa. "
                "Formato: Devuelve SOLO las líneas del diálogo, cada una con el nombre del hablante: 'Sarah: [texto]' o 'Leo: [texto]'. "
                "Empieza con Sarah y alterna de forma lógica."
            )
        messages = [
            {
                "role": "system",
                "content": sys_prompt
            },
            {"role": "user", "content": (
                f"Genera la entrevista ahora. Enfócate en el tema: {selected_topic}." if selected_topic else "Genera la entrevista ahora."
            )}
        ]
        out = self.llm.create_chat_completion(messages=messages, max_tokens=2500, temperature=0.7)
        raw_text = out["choices"][0]["message"]["content"]
        
        # Salvar generated no Qdrant quando especialista for selecionado
        if self.specialist:
            self._save_to_qdrant("generated", raw_text)
        
        # Se especialista em gramática, corrigir sequencialmente
        if self.specialist in ("grammar", "daily"):
            correction_messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un revisor experto. Asegúrate de que el diálogo tenga un orden lógico claro: saludo, antecedentes, APIs REST, escalabilidad/diseño, optimización SQL, uso de Docker, ejemplo de depuración, cierre final. "
                        "Asegúrate de que los hablantes alternen empezando con Sarah, y cada línea esté prefijada con 'Sarah:' o 'Leo:'. "
                        "Si especialista en gramática: corrige la gramática a español estándar formal. Si especialista diario: mantén el lenguaje natural y conversacional. "
                        "IMPORTANTE: Preserva la longitud del diálogo. NO acortes ni resumas. Mantén TODOS los intercambios del original. "
                        "Mantén el significado original; no agregues temas extra; mantén el número de líneas."
                    )
                },
                {"role": "user", "content": f"Corrige este diálogo:\n{raw_text}"}
            ]
            correction_output = self.llm.create_chat_completion(
                messages=correction_messages,
                max_tokens=2000,
                temperature=0.3  # Menos creatividad para correção/validação
            )
            corrected_text = correction_output["choices"][0]["message"]["content"]
            # Limpar artefatos indesejados
            corrected_text = re.sub(r'^Diálogo corregido:\s*\n?', '', corrected_text).strip()
            # Salvar corrected
            self._save_to_qdrant("corrected", corrected_text)
            raw_text = corrected_text
        
        print(f"Raw text (tokens aproximados): {len(raw_text.split())}")
        structured = self._parse_dialogue_structured(raw_text)
        joined = ' '.join([t for _, t in structured])
        print(f"Parsed texts (linhas): {len(structured)}, tokens aproximados: {len(joined.split())}")
        print(f"Tokens removidos: {len(raw_text.split()) - len(joined.split())}")
        return structured

    def _ensure_qdrant(self):
        """Inicializa Qdrant e o modelo de embeddings apenas quando necessário."""
        if self.qdrant is None:
            self.qdrant = QdrantClient(path="./qdrant_db")
        if self.embedder is None:
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

    def _save_to_qdrant(self, collection_name: str, text: str):
        """Salva texto no Qdrant com embedding."""
        from qdrant_client.http.models import VectorParams, Distance, PointStruct
        
        self._ensure_qdrant()
        
        # Criar coleção se não existir
        try:
            self.qdrant.get_collection(collection_name)
        except Exception:
            self.qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
        
        # Gerar embedding
        embedding = self.embedder.encode(text).tolist()
        
        # Salvar ponto com ID único
        point = PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={"text": text}
        )
        self.qdrant.upsert(collection_name=collection_name, points=[point])

    def _close_qdrant(self):
        """Fecha o cliente Qdrant de forma segura para evitar erros no shutdown do Python."""
        try:
            if self.qdrant is not None:
                self.qdrant.close()
        except Exception:
            # Ignora erros no shutdown
            pass


if __name__ == "__main__":
    # Teste isolado da classe usando Builder
    builder = InterviewGeneratorBuilder()
    
    if len(sys.argv) > 1:
        model_type = sys.argv[1].strip().lower()
        if model_type in ["fast", "reasoning"]:
            builder.set_model_type(model_type)
    
    if len(sys.argv) > 2:
        spec = sys.argv[2].strip().lower()
        if spec in ["grammar", "daily"]:
            builder.set_specialist(spec)
    
    try:
        generator = builder.build()
        texts = generator.generate_english_interview_texts()
        print("Textos gerados pelo modelo:")
        for i, text in enumerate(texts, 1):
            print(f"{i}. {text}")
    except Exception as e:
        print(f"Erro ao carregar ou usar o modelo: {e}")