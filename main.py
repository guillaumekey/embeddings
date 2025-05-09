import streamlit as st
import pandas as pd
import os

from data_processing import read_csv, convert_embeddings, find_related_pages, analyze_themes
from visualization import create_similarity_network, create_theme_heatmap
from link_analysis import process_inlinks, find_linking_opportunities, analyze_linking_structure, analyze_incoming_links
from advanced_link_analysis import (
    analyze_broken_links,
    analyze_incoming_links_stats,
    analyze_anchor_distribution,
    create_anchor_distribution_chart
)
from utils import get_download_link
from config import setup_page, setup_sidebar
from ui_components import display_theme_analysis, display_link_analysis, display_link_recommendations, \
    display_similarity_details
from ui_link_analysis import display_advanced_link_analysis
from filters import apply_url_filters


def main():
    setup_page()

    st.title("Analyse de similarité sémantique des pages web")

    # Upload des fichiers
    col1, col2 = st.columns(2)
    with col1:
        uploaded_embeddings = st.file_uploader("Choisissez le fichier CSV des embeddings", type="csv", key="embeddings")
    with col2:
        uploaded_inlinks = st.file_uploader("Choisissez le fichier CSV des inlinks (optionnel)", type="csv",
                                            key="inlinks")

    if uploaded_embeddings is not None:
        df = read_csv(uploaded_embeddings)
        inlinks_df = read_csv(uploaded_inlinks) if uploaded_inlinks is not None else None

        if df is not None:
            try:
                # Vérification des colonnes
                required_columns = ['URL', 'Embeddings']
                if not all(col in df.columns for col in required_columns):
                    st.error(f"Le fichier d'embeddings doit contenir les colonnes : URL, Embeddings")
                    return

                # Configuration des paramètres
                top_n, include_exact, include_partial, exclude_exact, exclude_partial, theme_level = setup_sidebar()

                # Application des filtres
                filtered_df, filtered_urls = apply_url_filters(
                    df, include_exact, include_partial, exclude_exact, exclude_partial
                )

                if filtered_urls:
                    st.sidebar.info(f"Pages après filtrage : {len(filtered_urls)} / {len(df)}")

                # Conversion des embeddings
                df['Embeddings'] = df['Embeddings'].apply(convert_embeddings)

                if df['Embeddings'].isna().any():
                    st.error("Certains embeddings n'ont pas pu être convertis.")
                    return

                # Calcul des pages similaires
                related_pages = find_related_pages(df, filtered_urls, top_n=top_n)

                # Traitement des inlinks si disponibles
                existing_links = {}
                if inlinks_df is not None:
                    # Vérifier les colonnes nécessaires pour le fichier d'inlinks
                    required_inlink_columns = ['Type', 'From', 'To', 'Status Code', 'Anchor Text']
                    if not all(col in inlinks_df.columns for col in required_inlink_columns):
                        st.error(
                            f"Le fichier d'inlinks doit contenir les colonnes : {', '.join(required_inlink_columns)}")
                        return

                    # Traitement des liens existants
                    existing_links = process_inlinks(inlinks_df)

                # Table détaillée des similarités
                st.header("Table détaillée des similarités")
                similarity_min_score = st.slider(
                    "Score minimum de similarité",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.05,
                    help="Filtrer les similarités selon leur score minimum"
                )

                # Afficher les similarités avec les liens existants si disponibles
                similarity_df = display_similarity_details(related_pages, similarity_min_score, existing_links)

                # Bouton d'export pour la table de similarité
                if not similarity_df.empty:
                    st.download_button(
                        label="Télécharger la table des similarités (CSV)",
                        data=similarity_df.to_csv(index=False).encode('utf-8'),
                        file_name="similarites_detaillees.csv",
                        mime="text/csv",
                        key="download_similarities"
                    )

                # Analyse thématique
                st.header("Analyse par thématiques")

                col1, col2 = st.columns(2)
                with col1:
                    theme_min_score = st.slider(
                        "Score minimum pour l'analyse thématique",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.5,
                        step=0.05
                    )
                with col2:
                    min_cluster_size = st.slider(
                        "Taille minimale des clusters",
                        min_value=1,
                        max_value=10,
                        value=2
                    )

                # Analyse des thèmes avec le niveau choisi
                theme_df = analyze_themes(filtered_df, related_pages, theme_min_score, theme_level)
                display_theme_analysis(theme_df, min_cluster_size)

                # Export des résultats thématiques avec une clé unique
                st.markdown(get_download_link(theme_df, "theme_results"), unsafe_allow_html=True)

                if inlinks_df is not None:
                    st.header("Analyse du maillage interne")

                    # Analyse standard du maillage
                    link_stats = analyze_linking_structure(filtered_df, existing_links)
                    display_link_analysis(link_stats)

                    # Analyse des liens entrants et recommandés
                    st.subheader("État du maillage interne")
                    link_analysis_df = analyze_incoming_links(
                        existing_links,
                        related_pages,
                        df['URL'].tolist(),
                        min_score=similarity_min_score
                    )

                    display_link_recommendations(link_analysis_df)

                    # Trouver les opportunités de maillage
                    st.subheader("Opportunités de maillage interne")
                    opportunities = find_linking_opportunities(
                        related_pages,
                        existing_links,
                        min_score=similarity_min_score,
                        filtered_urls=filtered_urls
                    )

                    if not opportunities.empty:
                        st.dataframe(
                            opportunities,
                            column_config={
                                "Source URL": "URL Source",
                                "Target URL": "URL Cible",
                                "Score de similarité": st.column_config.NumberColumn(
                                    "Score",
                                    format="%.3f"
                                )
                            },
                            use_container_width=True,
                            hide_index=True
                        )

                        # Export des opportunités avec une clé unique
                        st.markdown(get_download_link(opportunities, "opportunities"), unsafe_allow_html=True)

                    # Analyse avancée du maillage interne
                    broken_links_count, broken_links_df = analyze_broken_links(inlinks_df)
                    incoming_links_stats = analyze_incoming_links_stats(inlinks_df)
                    anchor_stats = analyze_anchor_distribution(inlinks_df)
                    anchor_chart = create_anchor_distribution_chart(anchor_stats['anchor_dist'])

                    # Passer les related_pages, inlinks_df et existing_links pour la vue détaillée
                    display_advanced_link_analysis(
                        broken_links_count,
                        broken_links_df,
                        incoming_links_stats,
                        anchor_stats,
                        anchor_chart,
                        related_pages,    # Ajout du paramètre related_pages
                        inlinks_df,       # Ajout du paramètre inlinks_df
                        existing_links    # Ajout du paramètre existing_links
                    )

            except Exception as e:
                st.error(f"Une erreur s'est produite lors du traitement : {str(e)}")
                st.exception(e)  # Afficher la trace complète pour le débogage


if __name__ == "__main__":
    main()