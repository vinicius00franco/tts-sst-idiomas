# ==========================
# Múltiplas vozes por idioma
# ==========================
VOICE_CATALOG = {
    'pt': {
        'male': [
            ('pt_BR-faber-medium', 'models/pt_BR-faber-medium.onnx'),
            ('pt_BR-cadu-medium', 'models/pt_BR-cadu-medium.onnx'),
            ('pt_BR-jeff-medium', 'models/pt_BR-jeff-medium.onnx'),
        ],
        'female': [
            # Não há vozes femininas pt_BR publicadas no catálogo oficial
            # Deixe vazio ou use alternativas de pt_PT se desejar
        ],
    },
    'en': {
        'male': [
            ('en_US-ryan-medium', 'models/en_US-ryan-medium.onnx'),
            ('en_US-joe-medium', 'models/en_US-joe-medium.onnx'),
            ('en_GB-alan-medium', 'models/en_GB-alan-medium.onnx'),
        ],
        'female': [
            ('en_US-lessac-medium', 'models/en_US-lessac-medium.onnx'),
            ('en_US-amy-medium', 'models/en_US-amy-medium.onnx'),
            ('en_GB-jenny_dioco-medium', 'models/en_GB-jenny_dioco-medium.onnx'),
        ],
    },
    'es': {
        'male': [
            ('es_ES-davefx-medium', 'models/es_ES-davefx-medium.onnx'),
            ('es_ES-sharvard-medium', 'models/es_ES-sharvard-medium.onnx'),
            ('es_MX-ald-medium', 'models/es_MX-ald-medium.onnx'),
        ],
        'female': [
            ('es_AR-daniela-high', 'models/es_AR-daniela-high.onnx'),
        ],
    },
}