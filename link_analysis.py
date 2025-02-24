import pandas as pd
from typing import Dict, List, Set
import streamlit as st


def process_inlinks(inlinks_df: pd.DataFrame) -> Dict[str, Set[str]]:
    """
    Traite le fichier d'inlinks pour créer un dictionnaire des liens existants.
    Ne garde que les hyperlinks et exclut les self-referencing.
    """
    # Filtrer les hyperlinks uniquement
    hyperlinks = inlinks_df[inlinks_df['Type'] == 'Hyperlink']

    # Créer un dictionnaire des liens existants
    existing_links = {}

    for _, row in hyperlinks.iterrows():
        from_url = row['From']
        to_url = row['To']

        # Exclure les self-referencing
        if from_url != to_url:
            if from_url not in existing_links:
                existing_links[from_url] = set()
            existing_links[from_url].add(to_url)

    return existing_links


def find_linking_opportunities(semantic_relations: Dict[str, List[Dict]],
                               existing_links: Dict[str, Set[str]],
                               min_score: float = 0.7,
                               filtered_urls: List[str] = None) -> pd.DataFrame:
    """
    Identifie les opportunités de maillage interne en comparant
    les relations sémantiques avec les liens existants.

    filtered_urls: Liste des URLs sources à analyser (si None, analyse toutes les URLs)
    """
    opportunities = []

    # Déterminer les URLs sources à analyser
    source_urls = filtered_urls if filtered_urls else semantic_relations.keys()

    for source_url in source_urls:
        if source_url not in semantic_relations:
            continue

        source_links = existing_links.get(source_url, set())
        similar_pages = semantic_relations[source_url]

        for page in similar_pages:
            target_url = page['url']
            score = page['score']

            # Ne considérer que les pages avec un score supérieur au minimum
            if score >= min_score and target_url != source_url:
                # Vérifier si le lien n'existe pas déjà
                if target_url not in source_links:
                    # Vérifier la réciprocité du lien
                    target_links = existing_links.get(target_url, set())
                    is_bidirectional = source_url not in target_links

                    opportunities.append({
                        'Source URL': source_url,
                        'Target URL': target_url,
                        'Score de similarité': score,
                        'Type': 'Lien manquant bidirectionnel' if is_bidirectional
                        else 'Lien manquant unidirectionnel'
                    })

    # Créer et trier le DataFrame des opportunités
    if opportunities:
        opportunities_df = pd.DataFrame(opportunities)
        return opportunities_df.sort_values('Score de similarité', ascending=False)
    else:
        return pd.DataFrame(columns=['Source URL', 'Target URL', 'Score de similarité', 'Type'])


def analyze_incoming_links(existing_links: Dict[str, Set[str]],
                           semantic_relations: Dict[str, List[Dict]],
                           all_urls: List[str],
                           min_score: float = 0.7) -> pd.DataFrame:
    """
    Analyse les liens entrants et le potentiel de maillage pour chaque page.

    Returns:
        DataFrame avec URL, nombre de liens reçus et nombre de liens recommandés
    """
    # Calculer les liens entrants pour chaque URL
    incoming_links = {}
    for url in all_urls:
        incoming_links[url] = 0

    # Compter les liens entrants existants
    for source, targets in existing_links.items():
        for target in targets:
            if target in incoming_links:
                incoming_links[target] += 1

    # Calculer les opportunités de liens pour chaque URL
    recommended_links = {}
    for url in all_urls:
        recommended_links[url] = 0

    # Parcourir toutes les relations sémantiques
    for source_url, similar_pages in semantic_relations.items():
        for page in similar_pages:
            target_url = page['url']
            score = page['score']

            if score >= min_score:
                # Vérifier si le lien n'existe pas déjà dans les deux directions
                if target_url not in existing_links.get(source_url, set()):
                    recommended_links[target_url] += 1  # Lien entrant recommandé
                if source_url not in existing_links.get(target_url, set()):
                    recommended_links[source_url] += 1  # Lien sortant recommandé

    # Créer le DataFrame
    analysis_data = []
    for url in all_urls:
        analysis_data.append({
            'URL': url,
            'Nombre de liens internes reçus': incoming_links[url],
            'Nombre de liens internes recommandés': recommended_links[url]
        })

    # Créer et trier le DataFrame
    df = pd.DataFrame(analysis_data)
    # Trier d'abord par nombre de liens reçus (croissant)
    # puis par nombre de liens recommandés (décroissant)
    return df.sort_values(['Nombre de liens internes reçus', 'Nombre de liens internes recommandés'],
                          ascending=[True, False])


def analyze_linking_structure(df: pd.DataFrame, existing_links: Dict[str, Set[str]]) -> Dict:
    """
    Analyse la structure actuelle des liens et fournit des statistiques.
    """
    total_pages = len(df) if df is not None else 0
    pages_with_links = len(existing_links) if existing_links else 0
    total_links = sum(len(links) for links in existing_links.values()) if existing_links else 0

    # Éviter la division par zéro
    avg_links_per_page = (total_links / total_pages) if total_pages > 0 else 0

    # Calculer les pages orphelines
    if df is not None and existing_links:
        orphan_pages = len(df[~df['URL'].isin(existing_links.keys())])
    else:
        orphan_pages = 0

    stats = {
        'total_pages': total_pages,
        'pages_with_links': pages_with_links,
        'total_links': total_links,
        'avg_links_per_page': avg_links_per_page,
        'orphan_pages': orphan_pages
    }

    return stats


def analyze_link_distribution(existing_links: Dict[str, Set[str]]) -> pd.DataFrame:
    """
    Analyse la distribution des liens par page.
    """
    if not existing_links:
        return pd.DataFrame(columns=['URL', 'Nombre de liens sortants'])

    link_counts = {url: len(links) for url, links in existing_links.items()}
    return pd.DataFrame(list(link_counts.items()),
                        columns=['URL', 'Nombre de liens sortants']) \
        .sort_values('Nombre de liens sortants', ascending=False)