import base64
import hashlib
import colorsys
from typing import Dict, List
import pandas as pd


def get_download_link(df: pd.DataFrame, key_suffix: str = "") -> str:
    """Génère un lien de téléchargement pour le DataFrame avec une clé unique."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()

    # Ajouter le suffixe à l'ID HTML pour le rendre unique
    download_id = f"download_link_{key_suffix}" if key_suffix else "download_link"

    return f'<a id="{download_id}" href="data:file/csv;base64,{b64}" download="resultats.csv">Télécharger les résultats (CSV)</a>'


def extract_theme_from_url(url: str, level: int = 1) -> str:
    """Extrait le thème à partir de l'URL en se basant sur le niveau spécifié."""
    try:
        path = url.split('://')[1].split('/')
        path = [p for p in path if p and p not in ['www', 'fr', 'com', 'net', 'org']]

        if len(path) >= level:
            theme = path[level - 1]
            return theme.replace('-', ' ').title()

        if path:
            theme = path[-1]
            return theme.replace('-', ' ').title()

        return 'Autres'
    except:
        return 'Autres'


def get_theme_color(theme: str) -> str:
    """Retourne une couleur aléatoire mais cohérente pour un thème donné."""
    hash_object = hashlib.md5(theme.encode())
    hash_hex = hash_object.hexdigest()

    hue = int(hash_hex[:2], 16) / 255 * 360
    saturation = 0.7
    lightness = 0.5

    rgb = colorsys.hls_to_rgb(hue / 360, lightness, saturation)
    return '#{:02x}{:02x}{:02x}'.format(
        int(rgb[0] * 255),
        int(rgb[1] * 255),
        int(rgb[2] * 255)
    )


def get_readable_label(url: str) -> str:
    """Crée une étiquette lisible à partir de l'URL."""
    label = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
    label = label.replace('-', ' ').title()
    words = label.split()
    if len(words) > 4:
        label = ' '.join(words[:4]) + '...'
    return label