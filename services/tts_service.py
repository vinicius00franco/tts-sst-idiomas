import subprocess
import sys
from typing import Optional

class TTSService:
    def run_tts(self, model: str, specialist: Optional[str], langs: list[str], topic_subject: Optional[str], selected_topic: Optional[str]) -> str:
        cmd = [sys.executable, "scripts/run_tts.py", "--model", model]
        if specialist:
            cmd.extend(["--specialist", specialist])
        if langs:
            cmd.extend(["--langs", *langs])
        if topic_subject:
            cmd.extend(["--topic-subject", topic_subject])
        if selected_topic:
            cmd.extend(["--selected-topic", selected_topic])

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        if result.returncode != 0:
            raise Exception(f"Erro ao executar run_tts: {result.stderr}")
        return result.stdout

    def query_qdrant(self, query_text: str) -> str:
        cmd = [sys.executable, "scripts/query_qdrant.py", query_text]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        if result.returncode != 0:
            raise Exception(f"Erro ao executar query_qdrant: {result.stderr}")
        return result.stdout

    def get_conversation(self, conversation_uuid: str) -> str:
        cmd = [sys.executable, "scripts/get_conversation.py", conversation_uuid]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        if result.returncode != 0:
            raise Exception(f"Erro ao executar get_conversation: {result.stderr}")
        return result.stdout

    def suggest_topics(self, model: str, specialist: Optional[str], lang: str, subject: str) -> list[str]:
        # Importa diretamente para evitar criar novo script
        import sys
        sys.path.append('scripts')
        from interview_generator import InterviewGeneratorBuilder
        builder = InterviewGeneratorBuilder().set_model_type(model)
        if specialist:
            builder.set_specialist(specialist)
        gen = builder.build()
        return gen.suggest_topics(subject, target_lang=lang)