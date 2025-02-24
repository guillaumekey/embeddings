import streamlit as st
import pandas as pd
from typing import Dict, List


def display_theme_analysis(theme_df: pd.DataFrame, min_cluster_size: int):
    """Affiche l'analyse thématique."""
    themes = theme_df['Theme'].value_counts()
    valid_themes = themes[themes >= min_cluster_size].index

    total_themes = len(themes)
    valid_clusters = len(valid_themes)

    st.info(f"Sur {total_themes} thèmes détectés, {valid_clusters} ont au moins {min_cluster_size} pages.")

    for theme in valid_themes:
        theme_subset = theme_df[theme_df['Theme'] == theme]
        with st.expander(
                f"📚 {theme} ({len(theme_subset)} pages, dont {theme_subset['Nombre de relations inter-thématiques'].sum()} relations inter-thématiques)"):
            display_cols = [
                'URL',
                'Nombre de pages similaires',
                'Nombre de relations inter-thématiques',
                'Score moyen',
                'Relations inter-thématiques',
                'Pages similaires'
            ]

            st.dataframe(
                theme_subset[display_cols],
                column_config={
                    'URL': 'URL',
                    'Nombre de pages similaires': st.column_config.NumberColumn('Pages similaires'),
                    'Nombre de relations inter-thématiques': st.column_config.NumberColumn(
                        'Relations inter-thématiques'),
                    'Score moyen': st.column_config.NumberColumn('Score moyen', format="%.3f"),
                    'Relations inter-thématiques': 'Détails des relations inter-thématiques',
                    'Pages similaires': 'Pages similaires'
                },
                use_container_width=True,
                hide_index=True
            )


def display_link_analysis(link_stats: dict):
    """Affiche les statistiques de liens."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pages totales", link_stats['total_pages'])
        st.metric("Pages avec liens sortants", link_stats['pages_with_links'])
    with col2:
        st.metric("Nombre total de liens", link_stats['total_links'])
        st.metric("Moyenne de liens par page", f"{link_stats['avg_links_per_page']:.2f}")
    with col3:
        st.metric("Pages orphelines", link_stats['orphan_pages'])
        st.metric("% pages orphelines", f"{(link_stats['orphan_pages'] / link_stats['total_pages'] * 100):.1f}%")


def display_link_recommendations(link_analysis_df: pd.DataFrame):
    """Affiche les recommandations de liens."""
    st.dataframe(
        link_analysis_df,
        column_config={
            "URL": "URL",
            "Nombre de liens internes reçus": st.column_config.NumberColumn(
                "Liens reçus",
                help="Nombre de liens internes pointant vers cette page"
            ),
            "Nombre de liens internes recommandés": st.column_config.NumberColumn(
                "Liens manquants recommandés",
                help="Nombre de liens potentiels basé sur la similarité sémantique"
            )
        },
        use_container_width=True,
        hide_index=True
    )


def display_similarity_details(related_pages: Dict[str, List[Dict]], min_score: float) -> pd.DataFrame:
    """
    Crée et affiche une table détaillée des similarités avec une URL par ligne,
    en évitant les doublons de relations.

    Args:
        related_pages: Dictionnaire des pages similaires
        min_score: Score minimum de similarité à afficher

    Returns:
        DataFrame contenant les détails des similarités
    """
    # Création de la liste des similarités
    similarity_data = []
    processed_pairs = set()  # Pour suivre les paires déjà traitées

    for source_url, similar_pages in related_pages.items():
        for page in similar_pages:
            if page['score'] >= min_score:
                target_url = page['url']

                # Créer une paire triée pour éviter les doublons
                pair = tuple(sorted([source_url, target_url]))

                # Ne traiter la paire que si elle n'a pas déjà été vue
                if pair not in processed_pairs:
                    similarity_data.append({
                        'URL principale': pair[0],
                        'URL similaire': pair[1],
                        'Score de similarité': page['score']
                    })
                    processed_pairs.add(pair)

    # Création du DataFrame
    similarity_df = pd.DataFrame(similarity_data)

    if not similarity_df.empty:
        # Tri par score de similarité décroissant
        similarity_df = similarity_df.sort_values('Score de similarité', ascending=False)

        # Affichage du tableau
        st.dataframe(
            similarity_df,
            column_config={
                'URL principale': st.column_config.TextColumn(
                    'URL principale',
                    width='large'
                ),
                'URL similaire': st.column_config.TextColumn(
                    'URL similaire',
                    width='large'
                ),
                'Score de similarité': st.column_config.NumberColumn(
                    'Score de similarité',
                    format="%.3f"
                )
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Aucune similarité trouvée avec le score minimum sélectionné.")

    return similarity_df