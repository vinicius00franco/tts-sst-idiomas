import subprocess
import sys
from typing import Optional

class TTSService:
    def run_tts(self, model: str, specialist: Optional[str]) -> str:
        cmd = [sys.executable, "scripts/run_tts.py"]
        if model != "fast":
            cmd.extend(["--model", model])
        if specialist:
            cmd.extend(["--specialist", specialist])
        
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