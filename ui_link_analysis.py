import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Set
import re


def display_advanced_link_analysis(
        broken_links_count: int,
        broken_links_df: pd.DataFrame,
        link_stats: Dict,
        anchor_stats: Dict,
        anchor_chart: go.Figure,
        related_pages: Dict = None,
        inlinks_df: pd.DataFrame = None,
        existing_links: Dict[str, Set[str]] = None
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
            # Ajout de la médiane de liens entrants
            st.metric(
                "Médiane de liens entrants par page",
                f"{link_stats['median_links_per_page']:.0f}"
            )

        with col3:
            st.metric(
                "Moyenne d'ancres distinctes par page",
                f"{anchor_stats['avg_anchors']:.2f}"
            )
            # Ajout de la médiane d'ancres distinctes
            st.metric(
                "Médiane d'ancres distinctes par page",
                f"{anchor_stats['median_anchors']:.0f}"
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

        # Pages avec le plus d'ancres distinctes
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

        # Ajout: Pages avec le moins d'ancres distinctes
        st.subheader("Pages avec le moins d'ancres distinctes")

        # Options de filtrage pour le tableau
        col1, col2 = st.columns([1, 1])

        with col1:
            # Champ pour spécifier le nombre de lignes à afficher
            display_rows = st.number_input("Nombre de lignes à afficher",
                                           min_value=1,
                                           max_value=100,
                                           value=20,
                                           step=5)

        with col2:
            # Filtre par nombre d'ancres
            min_anchors = 1  # Valeur par défaut
            max_anchors = st.slider("Filtrer par nombre d'ancres (max)",
                                    min_value=1,
                                    max_value=10,
                                    value=6)

        # Filtrage simple par inclusion/exclusion d'URL
        col1, col2 = st.columns([1, 1])

        with col1:
            include_pattern = st.text_input("URLs qui contiennent (séparées par des virgules):", "")
            include_terms = [term.strip() for term in include_pattern.split(',') if term.strip()]

        with col2:
            exclude_pattern = st.text_input("URLs qui ne contiennent pas (séparées par des virgules):", "")
            exclude_terms = [term.strip() for term in exclude_pattern.split(',') if term.strip()]

        # Appliquer les filtres
        # Ne prendre que les pages qui ont au moins 1 ancre
        bottom_anchors = anchor_stats['distinct_anchors'][anchor_stats['distinct_anchors']['Ancres distinctes'] > 0]

        # Filtre par nombre d'ancres
        bottom_anchors = bottom_anchors[bottom_anchors['Ancres distinctes'] <= max_anchors]

        # Filtre par termes d'inclusion
        if include_terms:
            mask = bottom_anchors['To'].str.contains('|'.join(include_terms), case=False)
            bottom_anchors = bottom_anchors[mask]

        # Filtre par termes d'exclusion
        if exclude_terms:
            mask = ~bottom_anchors['To'].str.contains('|'.join(exclude_terms), case=False)
            bottom_anchors = bottom_anchors[mask]

        # Trier et limiter
        bottom_anchors = bottom_anchors.sort_values('Ancres distinctes', ascending=True).head(display_rows)

        # Afficher le nombre total d'URLs après filtrage
        st.write(f"{len(bottom_anchors)} pages affichées correspondant aux critères de filtrage")

        st.dataframe(
            bottom_anchors,
            column_config={
                "To": "URL",
                "Ancres distinctes": st.column_config.NumberColumn("Nombre d'ancres distinctes")
            },
            use_container_width=True,
            hide_index=True
        )

        # Analyse détaillée par URL avec filtrage amélioré
        if inlinks_df is not None:
            st.subheader("Analyse détaillée par URL")

            # Récupérer toutes les URLs cibles
            all_urls = anchor_stats['distinct_anchors']['To'].tolist()

            # Interface de filtrage simplifiée
            with st.expander("Options de filtrage avancées", expanded=True):
                # Option 1: Filtrage simple par inclusion/exclusion
                st.subheader("Filtrage simple")
                col1, col2 = st.columns([1, 1])

                with col1:
                    include_pattern = st.text_input("URLs qui contiennent:", "", key="detail_include")

                with col2:
                    exclude_pattern = st.text_input("URLs qui ne contiennent pas:", "", key="detail_exclude")

                # Option 2: Filtrage par Regex pour utilisateurs avancés
                st.subheader("Filtrage avancé (Regex)")
                col1, col2 = st.columns([3, 1])

                with col1:
                    regex_filter = st.text_input("Expression régulière:", "")

                with col2:
                    regex_help = st.button("Aide Regex", help="Affiche des exemples d'expressions régulières courantes")

            # Afficher l'aide si demandé
            if regex_help:
                st.info("""
                **Exemples d'expressions régulières utiles:**
                - `blog` : URLs contenant "blog"
                - `^https://www\\.example\\.com/blog/` : URLs commençant par "https://www.example.com/blog/"
                - `(blog|article)` : URLs contenant "blog" OU "article"
                - `\\.html$` : URLs se terminant par ".html"
                - `product/[0-9]+` : URLs contenant "product/" suivi de chiffres
                """)

            # Appliquer les filtres
            filtered_urls = all_urls

            # Appliquer le filtre d'inclusion simple
            if include_pattern:
                filtered_urls = [url for url in filtered_urls if include_pattern.lower() in url.lower()]

            # Appliquer le filtre d'exclusion simple
            if exclude_pattern:
                filtered_urls = [url for url in filtered_urls if exclude_pattern.lower() not in url.lower()]

            # Appliquer le filtre regex (avancé) si fourni
            if regex_filter:
                try:
                    pattern = re.compile(regex_filter, flags=re.IGNORECASE)
                    filtered_urls = [url for url in filtered_urls if pattern.search(url)]
                except re.error:
                    st.error(f"Expression régulière invalide: {regex_filter}")

            # Trier les URLs pour une meilleure lisibilité
            filtered_urls.sort()

            # Afficher le nombre d'URLs après filtrage
            st.write(f"{len(filtered_urls)} URLs correspondent aux critères de filtrage")

            # Sélecteur d'URL
            if filtered_urls:
                selected_url = st.selectbox("Sélectionner une URL pour l'analyse détaillée:", filtered_urls)

                if selected_url:
                    st.subheader(f"Analyse détaillée de: {selected_url}")

                    # Récupérer les informations détaillées pour cette URL
                    from advanced_link_analysis import get_url_detail_info
                    url_info = get_url_detail_info(selected_url, inlinks_df, anchor_stats, related_pages,
                                                   existing_links)

                    # Afficher les métriques
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Liens internes", url_info['total_links'])

                    with col2:
                        st.metric("Liens uniques", url_info['unique_links'])

                    with col3:
                        st.metric("Ancres différentes", url_info['distinct_anchors_count'])

                    with col4:
                        st.metric("Ancres cannibales", len(url_info['cannibal_anchors']))

                    # Liste des ancres cannibales
                    if url_info['cannibal_anchors']:
                        st.subheader("✏️ Liste des ancres cannibales :")
                        for anchor in url_info['cannibal_anchors']:
                            st.write(f"- {anchor}")

                    # Liste de toutes les ancres
                    st.subheader("⚓ Liste des ancres :")
                    for anchor in url_info['anchor_list']:
                        # Mettre en surbrillance les ancres cannibales
                        if anchor in url_info['cannibal_anchors']:
                            st.markdown(f"- **{anchor}** _(cannibale)_")
                        else:
                            st.write(f"- {anchor}")

                    # Tableau des pages sources
                    st.subheader("📄 Pages pointant vers cette URL:")

                    # Créer un DataFrame pour l'affichage
                    source_df = pd.DataFrame(url_info['source_pages'])

                    if not source_df.empty:
                        # Ajouter une colonne pour le score formaté
                        source_df['Score'] = source_df['similarity'].apply(
                            lambda x: f"{x:.3f}" if x is not None else "N/A"
                        )

                        st.dataframe(
                            source_df[['url', 'anchor', 'Score']],
                            column_config={
                                "url": "URL source",
                                "anchor": "Texte d'ancre",
                                "Score": "Score de similarité"
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("Aucune page ne pointe vers cette URL.")

                    # Nouvelle section: Opportunités de maillage interne
                    st.subheader("📊 Opportunités de maillage interne:")

                    # Slider pour le seuil de similarité
                    similarity_threshold = st.slider(
                        "Seuil de similarité minimum",
                        min_value=0.50,
                        max_value=1.0,
                        value=0.85,  # Valeur par défaut à 85% (plus réaliste)
                        step=0.05,
                        format="%.2f",
                        help="Pages avec un score de similarité supérieur ou égal à ce seuil"
                    )

                    # Afficher les liens existants ou non
                    show_existing_links = st.checkbox("Afficher aussi les liens déjà existants", value=False)

                    # Filtrer les opportunités selon le seuil de similarité et les préférences d'affichage
                    filtered_opportunities = []
                    for opp in url_info['linking_opportunities']:
                        if opp['similarity_score'] >= similarity_threshold:
                            if not opp.get('link_exists', False) or show_existing_links:
                                filtered_opportunities.append(opp)

                    if filtered_opportunities:
                        # Convertir en DataFrame pour l'affichage
                        opps_df = pd.DataFrame(filtered_opportunities)

                        # Ajouter une colonne pour le type de lien
                        opps_df['type_lien'] = opps_df.apply(
                            lambda x: "Lien déjà existant" if x.get('link_exists', False) else
                            ("Lien inverse suggéré" if x.get('is_reverse', False) else "Lien suggéré"),
                            axis=1
                        )

                        # Formater le score pour l'affichage
                        opps_df['score_formatted'] = opps_df['similarity_score'].apply(lambda x: f"{x:.3f}")

                        # Afficher le DataFrame avec des styles personnalisés
                        st.dataframe(
                            opps_df[['source_url', 'score_formatted', 'type_lien']],
                            column_config={
                                "source_url": st.column_config.TextColumn("URL source", width="large"),
                                "score_formatted": st.column_config.TextColumn("Score de similarité", width="medium"),
                                "type_lien": st.column_config.TextColumn("Type", width="medium")
                            },
                            use_container_width=True,
                            hide_index=True
                        )

                        # Information sur le nombre d'opportunités
                        total_new = len([o for o in filtered_opportunities if not o.get('link_exists', False)])
                        total_existing = len([o for o in filtered_opportunities if o.get('link_exists', False)])

                        if show_existing_links and total_existing > 0:
                            st.info(
                                f"{total_new} nouvelles opportunités et {total_existing} liens existants trouvés avec un score ≥ {similarity_threshold:.2f}")
                        else:
                            st.info(
                                f"{total_new} opportunités de maillage interne trouvées avec un score ≥ {similarity_threshold:.2f}")

                        # Option pour télécharger les opportunités
                        if len(filtered_opportunities) > 0:
                            # Filtrer seulement les opportunités sans liens existants pour l'export
                            export_opps = [o for o in filtered_opportunities if not o.get('link_exists', False)]
                            if export_opps:
                                export_df = pd.DataFrame(export_opps)[['source_url', 'similarity_score']]
                                csv_data = export_df.to_csv(index=False)
                                st.download_button(
                                    label="Télécharger les opportunités (CSV)",
                                    data=csv_data,
                                    file_name=f"opportunites_{selected_url.split('/')[-1]}.csv",
                                    mime="text/csv"
                                )
                    else:
                        st.info(f"Aucune opportunité de maillage trouvée avec un score ≥ {similarity_threshold:.2f}")
                else:
                    st.info("Aucune URL ne correspond aux critères de filtrage.")