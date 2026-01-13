#!/usr/bin/env python3
import os
import sys
import json
import glob
import shutil
import argparse
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from urllib.request import urlretrieve
import pandas as pd

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))

# Voices needed by the current scripts
DEFAULT_VOICES = [
    'pt_BR-faber-medium',
    'en_US-lessac-medium',
    'en_US-ryan-medium',
    'es_AR-daniela-high',
    'es_ES-davefx-medium',
]

HF_BASE = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/{family}/{family}_{region}/{voice}/{quality}/{file}'


def parse_voice_id(vid: str):
    # e.g., en_US-ryan-medium
    try:
        family, region_voice, quality = vid.split('-')
        family2, region = family.split('_')
        voice = region_voice
        return family2, region, voice, quality
    except Exception:
        raise ValueError(f"Formato inválido de voice id: {vid}")


def voice_urls(vid: str):
    family, region, voice, quality = parse_voice_id(vid)
    onnx_name = f"{vid}.onnx"
    json_name = f"{vid}.onnx.json"
    onnx_url = HF_BASE.format(family=family, region=region, voice=voice, quality=quality, file=onnx_name)
    json_url = HF_BASE.format(family=family, region=region, voice=voice, quality=quality, file=json_name)
    return onnx_url, json_url, onnx_name, json_name


def sizeof(path: str) -> int:
    try:
        return os.path.getsize(path)
    except FileNotFoundError:
        return 0


def dir_size(path: str) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total


def human(n: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if n < 1024.0:
            return f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}TB"


def replace_empty_dicts(obj):
    if isinstance(obj, dict):
        return {k: (replace_empty_dicts(v) if v != {} else None) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_empty_dicts(item) for item in obj]
    else:
        return obj


def convert_json_to_parquet(json_path: str) -> str:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data = replace_empty_dicts(data)
    df = pd.DataFrame([data])
    parquet_path = json_path.replace('.json', '.parquet')
    df.to_parquet(parquet_path, index=False)
    return parquet_path


def download_file(url: str, dest: str):
    try:
        urlretrieve(url, dest)
        return True
    except (HTTPError, URLError) as e:
        print(f"Falha ao baixar {url}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Baixa vozes Piper, converte JSON para Parquet e remove JSON, medindo espaço.')
    parser.add_argument('--voices', nargs='*', default=DEFAULT_VOICES, help='Lista de IDs de vozes (ex: en_US-ryan-medium)')
    args = parser.parse_args()

    os.makedirs(MODELS_DIR, exist_ok=True)

    before_total = dir_size(MODELS_DIR)

    downloaded_json = []
    downloaded_onnx = []

    print(f"Baixando vozes em {MODELS_DIR}...")
    for vid in args.voices:
        onnx_url, json_url, onnx_name, json_name = voice_urls(vid)
        onnx_dest = os.path.join(MODELS_DIR, onnx_name)
        json_dest = os.path.join(MODELS_DIR, json_name)
        if not os.path.exists(onnx_dest):
            ok = download_file(onnx_url, onnx_dest)
            if ok:
                downloaded_onnx.append(onnx_dest)
        else:
            downloaded_onnx.append(onnx_dest)
        if not os.path.exists(json_dest):
            ok = download_file(json_url, json_dest)
            if ok:
                downloaded_json.append(json_dest)
        else:
            downloaded_json.append(json_dest)

    json_total_before = sum(sizeof(p) for p in downloaded_json)

    print("Convertendo JSON -> Parquet...")
    parquet_paths = []
    for jp in downloaded_json:
        if os.path.exists(jp):
            pq = convert_json_to_parquet(jp)
            parquet_paths.append(pq)

    parquet_total_after = sum(sizeof(p) for p in parquet_paths)

    print("Removendo arquivos JSON...")
    for jp in downloaded_json:
        if os.path.exists(jp):
            os.remove(jp)

    after_total = dir_size(MODELS_DIR)

    print("\nResumo de espaço em disco:")
    print(f"- Tamanho total antes: {human(before_total)}")
    print(f"- Tamanho total depois: {human(after_total)}")
    diff = after_total - before_total
    sign = '+' if diff >= 0 else '-'
    print(f"- Diferença total: {sign}{human(abs(diff))}")

    print("\nConfig JSON vs Parquet (apenas configs):")
    print(f"- Soma JSON (antes): {human(json_total_before)}")
    print(f"- Soma Parquet (depois): {human(parquet_total_after)}")
    config_diff = parquet_total_after - json_total_before
    sign2 = '+' if config_diff >= 0 else '-'
    pct = (config_diff / json_total_before * 100.0) if json_total_before > 0 else 0.0
    print(f"- Diferença nas configs: {sign2}{human(abs(config_diff))} ({pct:.1f}%)")

    print("\nArquivos gerados:")
    for p in parquet_paths:
        print(f"- {os.path.basename(p)}")

    print("Concluído.")


if __name__ == '__main__':
    main()
