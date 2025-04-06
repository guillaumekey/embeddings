import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Set, Tuple
import streamlit as st
import re


def analyze_broken_links(inlinks_df: pd.DataFrame) -> Tuple[int, pd.DataFrame]:
    """
    Analyse les liens cassés (404 et autres erreurs) dans le fichier d'inlinks.

    Returns:
        Tuple contenant le nombre total de liens cassés et un DataFrame avec les détails
    """
    # Filtrer les liens avec des codes d'erreur (4xx et 5xx)
    error_links = inlinks_df[inlinks_df['Status Code'] >= 400].copy()

    # Regrouper par URL cible et code d'erreur
    error_summary = error_links.groupby(['To', 'Status Code']).size().reset_index(name='Nombre de liens')

    # Ajouter le statut HTTP en texte
    error_summary['Statut'] = error_summary['Status Code'].apply(get_status_text)

    # Ordonner par nombre de liens décroissant
    error_summary = error_summary.sort_values('Nombre de liens', ascending=False)

    return len(error_links), error_summary


def get_status_text(status_code: int) -> str:
    """Retourne la description d'un code HTTP."""
    status_texts = {
        400: "Mauvaise requête",
        401: "Non autorisé",
        403: "Accès interdit",
        404: "Page non trouvée",
        500: "Erreur interne du serveur",
        503: "Service indisponible"
    }
    return status_texts.get(status_code, f"Erreur {status_code}")


def analyze_incoming_links_stats(inlinks_df: pd.DataFrame) -> Dict:
    """
    Calcule les statistiques sur les liens entrants.

    Returns:
        Un dictionnaire avec diverses statistiques
    """
    # Nombre de liens reçus par URL cible
    incoming_links = inlinks_df.groupby('To').size().reset_index(name='Liens reçus')

    # Nombre moyen de liens reçus par page
    avg_links_per_page = incoming_links['Liens reçus'].mean()

    # Nombre médian de liens reçus par page (nouvelle statistique)
    median_links_per_page = incoming_links['Liens reçus'].median()

    # Pages avec peu de liens entrants
    threshold = 7  # Par défaut, modifiable par l'utilisateur
    low_link_pages = incoming_links[incoming_links['Liens reçus'] < threshold]

    return {
        'incoming_links': incoming_links,
        'avg_links_per_page': avg_links_per_page,
        'median_links_per_page': median_links_per_page,  # Ajout de la médiane
        'low_link_pages': low_link_pages,
        'threshold': threshold
    }


def analyze_anchor_distribution(inlinks_df: pd.DataFrame) -> Dict:
    """
    Analyse la distribution des textes d'ancre dans les liens.

    Returns:
        Un dictionnaire avec les statistiques et visualisations sur les ancres
    """
    # Identifier les liens uniques (From-To) et leurs ancres
    unique_links = inlinks_df[['From', 'To', 'Anchor Text']].drop_duplicates()

    # Compter le nombre d'ancres différentes pour chaque cible
    anchor_counts = unique_links.groupby(['To', 'Anchor Text']).size().reset_index(name='count')
    distinct_anchors = anchor_counts.groupby('To').size().reset_index(name='Ancres distinctes')

    # Calculer la moyenne d'ancres distinctes par page
    avg_anchors = distinct_anchors['Ancres distinctes'].mean()

    # Calculer la médiane d'ancres distinctes par page (nouvelle statistique)
    median_anchors = distinct_anchors['Ancres distinctes'].median()

    # Créer un histogramme de la distribution
    anchor_dist = distinct_anchors['Ancres distinctes'].value_counts().sort_index().reset_index()
    anchor_dist.columns = ['Nombre d\'ancres distinctes', 'Nombre d\'URLs']

    return {
        'distinct_anchors': distinct_anchors,
        'avg_anchors': avg_anchors,
        'median_anchors': median_anchors,  # Ajout de la médiane
        'anchor_dist': anchor_dist,
        'anchor_counts': anchor_counts,  # Ajout pour l'accès aux ancres spécifiques par page
        'unique_links': unique_links  # Ajout pour l'accès aux liens pointant vers cette page
    }


def create_anchor_distribution_chart(anchor_dist: pd.DataFrame) -> go.Figure:
    """
    Crée un graphique de la distribution des ancres.
    """

    # Catégoriser les ancres
    def categorize_anchors(n):
        if n <= 6:
            return '1-6'
        elif n <= 10:
            return '7-10'
        else:
            return '11+'

    # Ajout de la catégorie
    anchor_dist['Catégorie'] = anchor_dist['Nombre d\'ancres distinctes'].apply(categorize_anchors)

    # Graphique en barres
    fig_bar = px.bar(
        anchor_dist,
        x='Nombre d\'ancres distinctes',
        y='Nombre d\'URLs',
        labels={'x': 'Nombre d\'ancres distinctes', 'y': 'Nombre d\'URLs'},
        title='Distribution du nombre d\'ancres distinctes par URL',
        color='Catégorie',
        color_discrete_map={'1-6': '#E9B4B4', '7-10': '#f0d1a0', '11+': '#B4D9C4'}
    )

    # Camembert pour les catégories
    category_counts = anchor_dist.groupby('Catégorie')['Nombre d\'URLs'].sum().reset_index()

    fig_pie = px.pie(
        category_counts,
        values='Nombre d\'URLs',
        names='Catégorie',
        title='Répartition du nombre d\'ancres différentes par lien',
        color='Catégorie',
        color_discrete_map={'1-6': '#E9B4B4', '7-10': '#f0d1a0', '11+': '#B4D9C4'}
    )

    # Combiner les graphiques dans une figure composée
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "xy"}]])

    # Ajouter le camembert
    for trace in fig_pie.data:
        fig.add_trace(trace, row=1, col=1)

    # Ajouter le graphique en barres
    for trace in fig_bar.data:
        fig.add_trace(trace, row=1, col=2)

    # Mise en page
    fig.update_layout(
        title_text="Répartition du nombre d'ancres différentes par lien",
        height=600,
        width=1200
    )

    return fig


def get_url_detail_info(url: str, inlinks_df: pd.DataFrame,
                        anchor_stats: Dict, related_pages: Dict, existing_links: Dict[str, Set[str]] = None) -> Dict:
    """
    Récupère les informations détaillées pour une URL spécifique.

    Args:
        url: L'URL à analyser
        inlinks_df: DataFrame des liens entrants
        anchor_stats: Statistiques d'ancres
        related_pages: Dictionnaire des pages similaires
        existing_links: Dictionnaire des liens existants

    Returns:
        Un dictionnaire avec les informations détaillées
    """
    # Tous les liens pointant vers cette URL
    incoming_links = inlinks_df[inlinks_df['To'] == url]

    # Nombre total de liens
    total_links = len(incoming_links)

    # Nombre de liens uniques (sources distinctes)
    unique_sources = incoming_links['From'].nunique()

    # Récupérer les ancres distinctes
    unique_anchors = anchor_stats['unique_links'][anchor_stats['unique_links']['To'] == url]

    # Liste des ancres distinctes
    anchor_list = unique_anchors['Anchor Text'].unique().tolist() if not unique_anchors.empty else []

    # Créer un dictionnaire de référence rapide pour les scores de similarité
    similarity_lookup = {}

    # Pré-calculer tous les scores de similarité possibles pour cette URL
    if related_pages:
        # Cas 1: Chercher dans related_pages les pages qui ont notre URL comme cible similaire
        for source_url, pages in related_pages.items():
            for page in pages:
                if page['url'] == url:
                    similarity_lookup[source_url] = page['score']

        # Cas 2: Chercher dans nos pages similaires celles qui sont sources de liens
        if url in related_pages:
            for page in related_pages[url]:
                target_url = page['url']
                if target_url not in similarity_lookup:  # Ne pas écraser les valeurs existantes
                    similarity_lookup[target_url] = page['score']

    # Liste des pages sources avec leurs ancres
    source_pages = []
    sources_with_anchor = incoming_links[['From', 'Anchor Text']].drop_duplicates()

    for _, row in sources_with_anchor.iterrows():
        source_url = row['From']
        anchor_text = row['Anchor Text']

        # Récupérer le score du dictionnaire pré-calculé
        similarity_score = similarity_lookup.get(source_url)

        source_pages.append({
            'url': source_url,
            'anchor': anchor_text,
            'similarity': similarity_score
        })

    # Vérifier si des ancres peuvent être considérées comme cannibales (même texte pour différentes pages)
    anchor_counts = inlinks_df.groupby('Anchor Text')['To'].nunique().reset_index()
    cannibal_anchors = anchor_counts[anchor_counts['To'] > 1]['Anchor Text'].tolist()

    # Filtrer pour ne garder que les ancres cannibales utilisées pour cette page
    page_cannibal_anchors = [a for a in anchor_list if a in cannibal_anchors]

    # Trouver des opportunités de maillage interne
    opportunities = []
    processed_urls = set()  # Pour suivre les URLs déjà traitées

    # Vérifier que les données nécessaires sont disponibles
    if related_pages and existing_links is not None:
        # Rechercher toutes les pages qui pourraient pointer vers notre URL
        for source_url, similar_pages in related_pages.items():
            # Ne pas considérer l'URL cible elle-même comme source
            if source_url == url:
                continue

            # Vérifier si l'URL cible est dans les pages similaires à la source
            for page in similar_pages:
                if page['url'] == url:
                    # Éviter les doublons
                    if source_url in processed_urls:
                        continue
                    processed_urls.add(source_url)

                    # Vérifier si le lien n'existe pas déjà
                    link_exists = False
                    if source_url in existing_links:
                        link_exists = url in existing_links[source_url]

                    # Ajouter à la liste des opportunités
                    if not link_exists:
                        opportunities.append({
                            'source_url': source_url,
                            'similarity_score': page['score'],
                            'link_exists': False
                        })
                    else:
                        # Optionnel: Ajouter quand même mais marquer comme existant
                        opportunities.append({
                            'source_url': source_url,
                            'similarity_score': page['score'],
                            'link_exists': True
                        })

        # Vérifier aussi si notre URL cible peut pointer vers d'autres pages similaires
        if url in related_pages:
            for target in related_pages[url]:
                target_url = target['url']
                # Ne pas considérer l'URL cible elle-même ou les URLs déjà traitées
                if target_url == url or target_url in processed_urls:
                    continue
                processed_urls.add(target_url)

                # Vérifier si le lien inverse existe déjà
                link_exists = False
                if url in existing_links:
                    link_exists = target_url in existing_links[url]

                if not link_exists:
                    # Ajouter à la liste des opportunités mais marquer comme lien inverse
                    opportunities.append({
                        'source_url': target_url,
                        'similarity_score': target['score'],
                        'link_exists': False,
                        'is_reverse': True
                    })

    # Trier les opportunités par score de similarité décroissant
    opportunities = sorted(opportunities, key=lambda x: x['similarity_score'], reverse=True)

    # Éliminer les éventuels doublons restants en utilisant un dictionnaire temporaire
    unique_opportunities = {}
    for opp in opportunities:
        source_url = opp['source_url']
        # Utiliser l'URL source comme clé pour éliminer les doublons
        # Si un doublon existe avec un score plus élevé, le conserver
        if source_url not in unique_opportunities or opp['similarity_score'] > unique_opportunities[source_url][
            'similarity_score']:
            unique_opportunities[source_url] = opp

    # Convertir le dictionnaire en liste et remplacer la liste originale
    opportunities = list(unique_opportunities.values())
    # Re-trier après l'élimination des doublons
    opportunities = sorted(opportunities, key=lambda x: x['similarity_score'], reverse=True)

    return {
        'url': url,
        'total_links': total_links,
        'unique_links': unique_sources,
        'distinct_anchors_count': len(anchor_list),
        'anchor_list': anchor_list,
        'cannibal_anchors': page_cannibal_anchors,
        'source_pages': source_pages,
        'linking_opportunities': opportunities
    }
def filter_urls_by_regex(urls: List[str], regex_pattern: str) -> List[str]:
    """
    Filtre une liste d'URLs en utilisant une expression régulière.

    Args:
        urls: Liste des URLs à filtrer
        regex_pattern: Pattern regex à utiliser pour le filtrage

    Returns:
        Liste des URLs filtrées
    """
    if not regex_pattern:
        return urls

    try:
        # Utilisation de flags=re.IGNORECASE pour une recherche insensible à la casse
        pattern = re.compile(regex_pattern, flags=re.IGNORECASE)
        return [url for url in urls if pattern.search(url)]
    except re.error:
        # En cas d'erreur dans l'expression régulière
        st.error(f"Expression régulière invalide: {regex_pattern}")
        return urls


def apply_simple_filters(urls: List[str], include_terms: List[str], exclude_terms: List[str]) -> List[str]:
    """
    Applique des filtres simples d'inclusion et d'exclusion.

    Args:
        urls: Liste des URLs à filtrer
        include_terms: Termes à inclure (si au moins un est présent)
        exclude_terms: Termes à exclure (si au moins un est présent)

    Returns:
        Liste des URLs filtrées
    """
    filtered_urls = urls

    # Filtrer par termes d'inclusion (OR logic)
    if include_terms:
        filtered_urls = [url for url in filtered_urls
                         if any(term.lower() in url.lower() for term in include_terms)]

    # Filtrer par termes d'exclusion
    if exclude_terms:
        filtered_urls = [url for url in filtered_urls
                         if not any(term.lower() in url.lower() for term in exclude_terms)]

    return filtered_urls