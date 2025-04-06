import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict


def display_advanced_link_analysis(
        broken_links_count: int,
        broken_links_df: pd.DataFrame,
        link_stats: Dict,
        anchor_stats: Dict,
        anchor_chart: go.Figure
):
    """
    Affiche l'analyse avancée du maillage interne.
    """
    st.header("Analyse avancée du maillage interne")

    # Répartition en onglets
    tabs = st.tabs(["Vue d'ensemble", "Liens cassés", "Distribution des liens", "Analyse des ancres"])

    # Onglet 1: Vue d'ensemble
    with tabs[0]:
        st.subheader("Statistiques globales")

        # Métriques clés
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Liens cassés",
                broken_links_count,
                delta=None,
                delta_color="inverse"
            )

        with col2:
            st.metric(
                "Moyenne de liens entrants par page",
                f"{link_stats['avg_links_per_page']:.2f}"
            )

        with col3:
            st.metric(
                "Moyenne d'ancres distinctes par page",
                f"{anchor_stats['avg_anchors']:.2f}"
            )

        # Pages avec peu de liens
        st.subheader(f"Pages avec moins de {link_stats['threshold']} liens entrants")
        threshold = st.slider(
            "Seuil minimum de liens entrants",
            min_value=1,
            max_value=20,
            value=link_stats['threshold']
        )

        # Filtrer selon le nouveau seuil
        low_links = link_stats['incoming_links'][link_stats['incoming_links']['Liens reçus'] < threshold]
        st.write(f"{len(low_links)} pages ont moins de {threshold} liens entrants")

        st.dataframe(
            low_links,
            column_config={
                "To": "URL",
                "Liens reçus": st.column_config.NumberColumn("Liens reçus")
            },
            use_container_width=True,
            hide_index=True
        )

    # Onglet 2: Liens cassés
    with tabs[1]:
        st.subheader("Détails des liens cassés")

        if broken_links_count > 0:
            st.info(f"Il y a {broken_links_count} liens cassés sur le site.")

            st.dataframe(
                broken_links_df,
                column_config={
                    "To": "URL cible",
                    "Status Code": st.column_config.NumberColumn("Code HTTP"),
                    "Statut": "Description",
                    "Nombre de liens": st.column_config.NumberColumn("Nombre de liens")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("Aucun lien cassé détecté!")

    # Onglet 3: Distribution des liens
    with tabs[2]:
        st.subheader("Distribution des liens entrants")

        # Histogramme de distribution
        link_dist = link_stats['incoming_links']['Liens reçus'].value_counts().sort_index().reset_index()
        link_dist.columns = ['Nombre de liens', 'Nombre de pages']

        st.bar_chart(link_dist.set_index('Nombre de liens'))

        # Tableau détaillé
        st.dataframe(
            link_dist,
            use_container_width=True,
            hide_index=True
        )

    # Onglet 4: Analyse des ancres
    with tabs[3]:
        st.subheader("Analyse des textes d'ancre")

        # Graphique de distribution
        st.plotly_chart(anchor_chart)

        # Tableau détaillé
        st.dataframe(
            anchor_stats['anchor_dist'],
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Pages avec le plus d'ancres distinctes")
        top_anchors = anchor_stats['distinct_anchors'].sort_values('Ancres distinctes', ascending=False).head(20)

        st.dataframe(
            top_anchors,
            column_config={
                "To": "URL",
                "Ancres distinctes": st.column_config.NumberColumn("Nombre d'ancres distinctes")
            },
            use_container_width=True,
            hide_index=True
        )