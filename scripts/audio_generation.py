import os
import json
import wave
import numpy as np
import pandas as pd
import soundfile as sf
import tempfile
from scipy.signal import resample_poly
from typing import Optional, List, Tuple
from piper.voice import PiperVoice
from voice_catalog import VOICE_CATALOG
from interview_generator import InterviewGenerator, InterviewGeneratorBuilder


def convert_numpy(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(item) for item in obj]
    else:
        return obj


# Lista de modelos (Piper usa modelos próprios .onnx)
# Você pode baixar mais em: https://github.com/rhasspy/piper/
MODELS_PIPER = {
    "pt": "models/pt_BR-faber-medium.onnx",  # Voz masculina PT-BR
    "en": "models/en_US-lessac-medium.onnx",  # Voz feminina EN-US
}


def carregar_voz(lang: str) -> PiperVoice:
    model_path = MODELS_PIPER[lang]
    config_path = model_path + ".parquet"
    # Load config from Parquet
    cfg = convert_numpy(pd.read_parquet(config_path).iloc[0].to_dict())
    # Create temp JSON file
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cfg, f)
        temp_config_path = f.name
    voice = PiperVoice.load(model_path, temp_config_path)
    # Note: temp file will be deleted when program exits
    return voice


def falar_piper_api(
    texto: str, lang: str = "pt", output_file: Optional[str] = None
) -> str:
    """Gera áudio via API Python do Piper usando synthesize_wav e retorna o caminho do WAV."""
    if output_file is None:
        output_file = f"output_piper_{lang}.wav"

    voice = carregar_voz(lang)

    # Escrever WAV corretamente via wave.Wave_write
    with wave.open(output_file, "wb") as wav_file:
        voice.synthesize_wav(texto, wav_file)

    print(f"Piper API finalizado ({lang}) - Audio salvo em {output_file}")
    return output_file


def synthesize_to_flac(
    texto: str, model_path: str, config_parquet: str, output_flac: str
) -> Tuple[str, int]:
    """Gera áudio com Piper (API) e salva diretamente em FLAC.
    Retorna (arquivo_saida, sample_rate).
    """
    cfg = convert_numpy(pd.read_parquet(config_parquet).iloc[0].to_dict())
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cfg, f)
        temp_config_path = f.name
    voice = PiperVoice.load(model_path, temp_config_path)
    chunks = list(voice.synthesize(texto))
    if not chunks:
        raise RuntimeError("Nenhum chunk de áudio retornado pelo Piper")
    # Piper retorna um único chunk com propriedades úteis
    sr = int(chunks[0].sample_rate)
    # Usa int16 nativo do Piper para escrita FLAC
    audio_i16 = chunks[0].audio_int16_array
    if audio_i16 is None:
        raise RuntimeError("Chunk sem audio_int16_array")
    # Salvar FLAC (mono int16)
    sf.write(output_flac, audio_i16, sr, format="FLAC", subtype="PCM_16")
    return output_flac, sr


def _resample_int16(audio_i16: np.ndarray, sr_from: int, sr_to: int) -> np.ndarray:
    """Resample int16 mono audio from sr_from to sr_to using polyphase filtering."""
    if sr_from == sr_to:
        return audio_i16
    # Convert to float32 for processing
    x = audio_i16.astype(np.float32)
    # Compute up/down factors via greatest common divisor
    import math
    g = math.gcd(sr_from, sr_to)
    up = sr_to // g
    down = sr_from // g
    y = resample_poly(x, up, down)
    # Back to int16 with clipping
    y = np.clip(y, -32768, 32767).astype(np.int16)
    return y


# =====================
# Testes de integridade
# =====================
def assert_wav_integrity(
    path: str,
    expected_rate: Optional[int] = None,
    min_duration: float = 0.05,
    min_rms: float = 50.0,
) -> None:
    """Valida se um WAV é audível e bem formado.
    - Arquivo existe e tamanho > 44 bytes (cabeçalho)
    - Header RIFF/WAVE
    - Canais 1 ou 2, sample width 2 bytes (int16)
    - Taxa de amostragem condizente (se informada)
    - Duração mínima
    - RMS mínimo (não silêncio absoluto)
    """
    assert os.path.exists(path), f"Arquivo inexistente: {path}"
    size = os.path.getsize(path)
    assert size > 44, f"WAV sem dados (tamanho={size}): {path}"

    # Verificar RIFF/WAVE
    with open(path, "rb") as f:
        header = f.read(12)
        assert (
            header[0:4] == b"RIFF" and header[8:12] == b"WAVE"
        ), "Cabeçalho WAV inválido"

    # Verificar parâmetros e obter frames
    with wave.open(path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()

        assert n_channels in (1, 2), f"Canais inválidos: {n_channels}"
        assert sampwidth == 2, f"Sample width inválido: {sampwidth} (esperado=2 bytes)"
        if expected_rate is not None:
            assert (
                framerate == expected_rate
            ), f"Sample rate {framerate} != {expected_rate}"

        duration = nframes / float(framerate) if framerate > 0 else 0.0
        assert (
            duration >= min_duration
        ), f"Duração muito curta: {duration:.3f}s (< {min_duration}s)"

        # RMS dos samples (int16)
        raw = wf.readframes(nframes)
        if len(raw) == 0:
            raise AssertionError("Sem frames lidos do WAV")
        samples = np.frombuffer(raw, dtype=np.int16)
        # Se estéreo, reduzir para mono
        if n_channels == 2:
            samples = samples.reshape(-1, 2).mean(axis=1)
        rms = float(np.sqrt(np.mean(np.square(samples.astype(np.float32)))))
        assert (
            rms >= min_rms
        ), f"RMS muito baixo (provável silêncio): {rms:.2f} (< {min_rms})"


def assert_flac_integrity(
    path: str,
    expected_rate: Optional[int] = None,
    min_duration: float = 0.05,
    min_rms: float = 50.0,
) -> None:
    """Valida se um FLAC é audível e bem formado usando soundfile."""
    assert os.path.exists(path), f"Arquivo inexistente: {path}"
    size = os.path.getsize(path)
    assert size > 100, f"FLAC muito pequeno (tamanho={size}): {path}"
    # Ler pelo soundfile
    data, sr = sf.read(path, always_2d=False)
    # Garantir mono
    if data.ndim == 2:
        data = data.mean(axis=1)
    duration = len(data) / float(sr) if sr > 0 else 0.0
    assert (
        duration >= min_duration
    ), f"Duração muito curta: {duration:.3f}s (< {min_duration}s)"
    # RMS
    rms = float(np.sqrt(np.mean(np.square(data.astype(np.float32)))))
    assert rms >= min_rms / 32767.0, f"RMS muito baixo (provável silêncio): {rms:.4f}"
    if expected_rate is not None:
        assert sr == expected_rate, f"Sample rate {sr} != {expected_rate}"


def run_tests_pt_en():
    # Descobrir sample_rate da config do PT para validar
    cfg = convert_numpy(
        pd.read_parquet(MODELS_PIPER["pt"] + ".parquet").iloc[0].to_dict()
    )
    expected_rate_pt = int(cfg.get("audio", {}).get("sample_rate", 22050))

    # PT-BR
    pt_out = falar_piper_api(
        "Otimização concluída com Piper TTS via API.", "pt", "output_piper_api.wav"
    )
    assert_wav_integrity(pt_out, expected_rate=expected_rate_pt)
    # Versão FLAC
    pt_flac, sr_pt = synthesize_to_flac(
        "Otimização concluída com Piper TTS via API.",
        MODELS_PIPER["pt"],
        MODELS_PIPER["pt"] + ".parquet",
        "output_piper_api.flac",
    )
    assert_flac_integrity(pt_flac, expected_rate=sr_pt)

    # EN-US (se modelo existir)
    if os.path.exists(MODELS_PIPER["en"]) and os.path.exists(
        MODELS_PIPER["en"] + ".parquet"
    ):
        cfg_en = convert_numpy(
            pd.read_parquet(MODELS_PIPER["en"] + ".parquet").iloc[0].to_dict()
        )
        expected_rate_en = int(cfg_en.get("audio", {}).get("sample_rate", 22050))
        en_out = falar_piper_api(
            "Optimization completed with Piper TTS via API.",
            "en",
            "output_piper_api_en.wav",
        )
        assert_wav_integrity(en_out, expected_rate=expected_rate_en)
        en_flac, sr_en = synthesize_to_flac(
            "Optimization completed with Piper TTS via API.",
            MODELS_PIPER["en"],
            MODELS_PIPER["en"] + ".parquet",
            "output_piper_api_en.flac",
        )
        assert_flac_integrity(en_flac, expected_rate=sr_en)
    else:
        print("Modelo EN não encontrado; testes EN pulados.")

    # Apagar arquivos de teste após validação
    if os.path.exists("output_piper_api.wav"):
        os.remove("output_piper_api.wav")
    if os.path.exists("output_piper_api.flac"):
        os.remove("output_piper_api.flac")
    if os.path.exists("output_piper_api_en.wav"):
        os.remove("output_piper_api_en.wav")
    if os.path.exists("output_piper_api_en.flac"):
        os.remove("output_piper_api_en.flac")


def generate_language_audios(texts: dict, out_dir: str = "."):
    os.makedirs(out_dir, exist_ok=True)
    for lang, lang_text in texts.items():
        for gender in ("male", "female"):
            options = VOICE_CATALOG.get(lang, {}).get(gender, [])
            used = 0
            for display, model in options:
                model_path = model
                cfg_path = model_path + ".parquet"
                if os.path.exists(model_path) and os.path.exists(cfg_path):
                    out_flac = os.path.join(out_dir, f"{lang}_{gender}_{display}.flac")
                    try:
                        flac_path, sr = synthesize_to_flac(
                            lang_text, model_path, cfg_path, out_flac
                        )
                        assert_flac_integrity(flac_path, expected_rate=sr)
                        print(f"OK: {flac_path}")
                        used += 1
                        if used >= 3:
                            break
                    except Exception as e:
                        print(f"Falha com {display}: {e}")
                else:
                    print(
                        f"Modelo ausente: {model_path} (+ .json). Baixe em: https://huggingface.co/rhasspy/piper-voices/resolve/main/<lang>/<variant>/<voice>/<quality>/{model}"
                    )
            if used == 0:
                print(
                    f"Nenhum modelo {lang}/{gender} disponível localmente. (Baixe até 3)"
                )


def generate_interview_english(model_type: str = "fast", specialist: Optional[str] = None, selected_topic: Optional[str] = None):
    """Gera uma entrevista em inglês usando duas vozes, concatena em memória e salva apenas o arquivo final."""
    # Definir as vozes para a entrevista
    sarah_model = "models/en_US-lessac-medium.onnx"
    sarah_config = sarah_model + ".parquet"
    leo_model = "models/en_US-ryan-medium.onnx"
    leo_config = leo_model + ".parquet"

    # Verificar se os modelos existem
    if not (
        os.path.exists(sarah_model)
        and os.path.exists(sarah_config)
        and os.path.exists(leo_model)
        and os.path.exists(leo_config)
    ):
        print("Modelos para entrevista em inglês não encontrados.")
        return

    # Load configs
    sarah_cfg = convert_numpy(pd.read_parquet(sarah_config).iloc[0].to_dict())
    leo_cfg = convert_numpy(pd.read_parquet(leo_config).iloc[0].to_dict())

    # Create temp JSON files
    sarah_temp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(sarah_cfg, sarah_temp)
    sarah_temp_path = sarah_temp.name
    sarah_temp.close()

    leo_temp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(leo_cfg, leo_temp)
    leo_temp_path = leo_temp.name
    leo_temp.close()

    # Gerar textos usando LLM com Builder
    builder = InterviewGeneratorBuilder()
    builder.set_model_type(model_type)
    if specialist:
        builder.set_specialist(specialist)
    generator = builder.build()
    structured_texts = generator.generate_english_interview_texts(selected_topic)  # [(speaker, text), ...]

    # Construir conversation respeitando o speaker (ordem lógica)
    conversation = []
    for speaker, text in structured_texts:
        if speaker == 'Sarah':
            conversation.append((sarah_model, sarah_temp_path, text))
        else:
            conversation.append((leo_model, leo_temp_path, text))

    # Coletar todos os áudios em uma lista
    all_audio = []
    sample_rate = None
    male_count = 0
    female_count = 0
    sr_mismatch = False

    for model_path, config_path, text in conversation:
        voice = PiperVoice.load(model_path, config_path)
        chunks = list(voice.synthesize(text))
        if chunks:
            chunk = chunks[0]
            current_sr = int(chunk.sample_rate)
            if sample_rate is None:
                sample_rate = current_sr
            audio_i16 = chunk.audio_int16_array
            if audio_i16 is not None:
                if current_sr != sample_rate:
                    sr_mismatch = True
                    audio_i16 = _resample_int16(audio_i16, current_sr, sample_rate)
                all_audio.append(audio_i16)
                if model_path == leo_model:
                    male_count += 1
                else:
                    female_count += 1

    if not all_audio:
        print("Nenhum áudio gerado para a entrevista em inglês.")
        return

    # Adicionar silêncio entre os áudios e no final
    all_audio_with_silence = []
    silence = np.zeros(int(0.5 * sample_rate), dtype=np.int16)
    for audio in all_audio:
        all_audio_with_silence.append(audio)
        all_audio_with_silence.append(silence)
    concatenated_audio = np.concatenate(all_audio_with_silence)

    # Salvar o arquivo final FLAC
    base_name = "interview_english"
    extension = ".flac"
    output_dir = "outputs"
    version = 1
    while True:
        if version == 1:
            final_output = os.path.join(output_dir, f"{base_name}{extension}")
        else:
            final_output = os.path.join(output_dir, f"{base_name}_v{version}{extension}")
        if not os.path.exists(final_output):
            break
        version += 1
    sf.write(
        final_output, concatenated_audio, sample_rate, format="FLAC", subtype="PCM_16"
    )
    print(f"Entrevista em inglês salva em {final_output}")
    print(f"Segmentos: Sarah={female_count}, Leo={male_count}, SR mismatch={'sim' if sr_mismatch else 'não'}")

    # Clean up temp files
    os.unlink(sarah_temp_path)
    os.unlink(leo_temp_path)


def generate_interview_spanish(model_type: str = "fast", specialist: Optional[str] = None, selected_topic: Optional[str] = None):
    """Gera uma entrevista em espanhol (via LLM) usando duas vozes, concatena em memória e salva apenas o arquivo final."""
    # Definir as vozes para a entrevista
    sarah_model = "models/es_AR-daniela-high.onnx"
    sarah_config = sarah_model + ".parquet"
    leo_model = "models/es_ES-davefx-medium.onnx"
    leo_config = leo_model + ".parquet"

    # Verificar se os modelos existem
    if not (
        os.path.exists(sarah_model)
        and os.path.exists(sarah_config)
        and os.path.exists(leo_model)
        and os.path.exists(leo_config)
    ):
        print("Modelos para entrevista em espanhol não encontrados.")
        return

    # Load configs
    sarah_cfg = convert_numpy(pd.read_parquet(sarah_config).iloc[0].to_dict())
    leo_cfg = convert_numpy(pd.read_parquet(leo_config).iloc[0].to_dict())

    # Create temp JSON files
    sarah_temp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(sarah_cfg, sarah_temp)
    sarah_temp_path = sarah_temp.name
    sarah_temp.close()

    leo_temp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(leo_cfg, leo_temp)
    leo_temp_path = leo_temp.name
    leo_temp.close()

    # Gerar textos via LLM (estruturado)
    builder = InterviewGeneratorBuilder()
    builder.set_model_type(model_type)
    if specialist:
        builder.set_specialist(specialist)
    generator = builder.build()
    structured_texts = generator.generate_spanish_interview_texts(selected_topic)

    conversation = []
    for speaker, text in structured_texts:
        if speaker == 'Sarah':
            conversation.append((sarah_model, sarah_temp_path, text))
        else:
            conversation.append((leo_model, leo_temp_path, text))

    # Coletar todos os áudios em uma lista
    all_audio = []
    sample_rate = None
    male_count = 0
    female_count = 0
    sr_mismatch = False

    for model_path, config_path, text in conversation:
        voice = PiperVoice.load(model_path, config_path)
        chunks = list(voice.synthesize(text))
        if chunks:
            chunk = chunks[0]
            current_sr = int(chunk.sample_rate)
            if sample_rate is None:
                sample_rate = current_sr
            audio_i16 = chunk.audio_int16_array
            if audio_i16 is not None:
                if current_sr != sample_rate:
                    sr_mismatch = True
                    audio_i16 = _resample_int16(audio_i16, current_sr, sample_rate)
                all_audio.append(audio_i16)
                if model_path == leo_model:
                    male_count += 1
                else:
                    female_count += 1

    if not all_audio:
        print("Nenhum áudio gerado para a entrevista em espanhol.")
        return

    # Adicionar silêncio de 2 segundos entre os áudios e no final
    all_audio_with_silence = []
    silence = np.zeros(int(0.5 * sample_rate), dtype=np.int16)
    for audio in all_audio:
        all_audio_with_silence.append(audio)
        all_audio_with_silence.append(silence)
    concatenated_audio = np.concatenate(all_audio_with_silence)

    # Salvar o arquivo final FLAC
    base_name = "interview_spanish"
    extension = ".flac"
    output_dir = "outputs"
    version = 1
    while True:
        if version == 1:
            final_output = os.path.join(output_dir, f"{base_name}{extension}")
        else:
            final_output = os.path.join(output_dir, f"{base_name}_v{version}{extension}")
        if not os.path.exists(final_output):
            break
        version += 1
    sf.write(
        final_output, concatenated_audio, sample_rate, format="FLAC", subtype="PCM_16"
    )
    print(f"Entrevista em espanhol salva em {final_output}")
    print(f"Segmentos: Sarah={female_count}, Leo={male_count}, SR mismatch={'sim' if sr_mismatch else 'não'}")

    # Clean up temp files
    os.unlink(sarah_temp_path)
    os.unlink(leo_temp_path)
