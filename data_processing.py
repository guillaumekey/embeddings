import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Optional
import streamlit as st


def read_csv(uploaded_file) -> Optional[pd.DataFrame]:
    """Lit le CSV uploadé."""
    try:
        return pd.read_csv(uploaded_file)
    except Exception as e:
        st.error("Erreur lors de la lecture du CSV")
        return None


def convert_embeddings(embedding_str: str) -> Optional[np.ndarray]:
    """Convertit une chaîne d'embeddings en tableau numpy."""
    try:
        if isinstance(embedding_str, str):
            # Nettoyer la chaîne
            cleaned_str = embedding_str.strip()
            if cleaned_str.startswith('[') and cleaned_str.endswith(']'):
                cleaned_str = cleaned_str[1:-1]

            # Diviser et convertir en nombres
            values = [float(x.strip()) for x in cleaned_str.split(',') if x.strip()]
            if values:
                return np.array(values)

        return None

    except Exception as e:
        return None


def find_related_pages(df: pd.DataFrame, filtered_urls: list = None, top_n: int = 5) -> Dict[str, List[Dict]]:
    """
    Trouve les pages les plus similaires pour chaque URL.
    filtered_urls: liste des URLs sources à analyser (si None, analyse toutes les URLs)
    """
    related_pages = {}
    try:
        # Calculer la matrice de similarité sur toutes les données
        embeddings = np.stack(df['Embeddings'].values)
        cosine_similarities = cosine_similarity(embeddings)

        # Créer un dictionnaire d'index pour les URLs
        url_to_idx = {url: idx for idx, url in enumerate(df['URL'])}

        # Utiliser toutes les URLs si aucun filtre n'est spécifié
        urls_to_process = filtered_urls if filtered_urls else df['URL'].tolist()

        for url in urls_to_process:
            idx = url_to_idx[url]
            # Récupérer les indices des pages les plus similaires (exclure l'URL elle-même)
            similarities = cosine_similarities[idx]
            similar_indices = np.argsort(similarities)[::-1][1:top_n + 1]  # +1 car on exclut l'URL elle-même

            similar_pages = []
            for similar_idx in similar_indices:
                similar_pages.append({
                    'url': df.iloc[similar_idx]['URL'],
                    'score': similarities[similar_idx]
                })

            related_pages[url] = similar_pages

    except Exception as e:
        st.error(f"Erreur lors du calcul des similarités : {str(e)}")
        return {}

    return related_pages


def analyze_themes(df: pd.DataFrame, related_pages: Dict[str, List[Dict]],
                   min_score: float = 0.5, theme_level: int = 1) -> pd.DataFrame:
    """Analyse et regroupe les pages par thématique avec analyse inter-thématiques."""
    from utils import extract_theme_from_url

    theme_data = []

    # Créer un dictionnaire des thèmes pour toutes les URLs disponibles
    all_urls = set(df['URL'])  # URLs source
    for pages in related_pages.values():
        for page in pages:
            all_urls.add(page['url'])  # Ajouter les URLs cibles

    all_urls_themes = {url: extract_theme_from_url(url, theme_level) for url in all_urls}

    # Analyser seulement les URLs dans related_pages
    for url in related_pages.keys():
        if url not in all_urls_themes:
            continue

        current_theme = all_urls_themes[url]
        similar_pages = [page for page in related_pages[url] if page['score'] >= min_score]

        # Compter les relations inter-thématiques
        cross_theme_count = 0
        cross_theme_details = []

        for page in similar_pages:
            target_url = page['url']
            target_theme = all_urls_themes.get(target_url, 'Inconnu')

            if target_theme != current_theme:
                cross_theme_count += 1
                cross_theme_details.append(f"{target_theme} ({page['score']:.3f})")

        theme_data.append({
            'Theme': current_theme,
            'URL': url,
            'Nombre de pages similaires': len(similar_pages),
            'Nombre de relations inter-thématiques': cross_theme_count,
            'Relations inter-thématiques': ', '.join(cross_theme_details),
            'Score moyen': round(sum(p['score'] for p in similar_pages) / len(similar_pages) if similar_pages else 0,
                                 3),
            'Pages similaires': ', '.join([f"{p['url']} ({p['score']:.3f})" for p in similar_pages])
        })

    if not theme_data:  # Si aucune donnée n'est trouvée
        return pd.DataFrame(columns=['Theme', 'URL', 'Nombre de pages similaires',
                                     'Nombre de relations inter-thématiques', 'Relations inter-thématiques',
                                     'Score moyen', 'Pages similaires'])

    theme_df = pd.DataFrame(theme_data)
    return theme_df.sort_values(['Theme', 'Nombre de relations inter-thématiques', 'Score moyen'],
                                ascending=[True, False, False])