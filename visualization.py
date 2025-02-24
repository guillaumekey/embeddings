import pandas as pd
import numpy as np
from typing import Dict, List, Set
from pyvis.network import Network
import json
import tempfile
import plotly.graph_objects as go
from utils import get_theme_color, get_readable_label, extract_theme_from_url


def create_theme_heatmap(df: pd.DataFrame, existing_links: Dict[str, Set[str]],
                         semantic_relations: Dict[str, List[Dict]],
                         min_score: float = 0.7) -> None:
    """
    Crée une heatmap des relations entre thématiques, montrant :
    - Le nombre de liens existants entre thématiques
    - Le nombre de liens potentiels basé sur la similarité
    - Le ratio de couverture (liens existants / liens potentiels)
    """
    # Extraire les thématiques de toutes les URLs
    url_themes = {url: extract_theme_from_url(url) for url in df['URL']}
    all_themes = sorted(list(set(url_themes.values())))

    # Initialiser les matrices pour les liens existants et potentiels
    n_themes = len(all_themes)
    existing_matrix = np.zeros((n_themes, n_themes))
    potential_matrix = np.zeros((n_themes, n_themes))

    # Compter les liens existants entre thématiques
    for source, targets in existing_links.items():
        if source in url_themes:
            source_theme = url_themes[source]
            source_idx = all_themes.index(source_theme)
            for target in targets:
                if target in url_themes:
                    target_theme = url_themes[target]
                    target_idx = all_themes.index(target_theme)
                    existing_matrix[source_idx][target_idx] += 1

    # Compter les liens potentiels basés sur la similarité
    for source, similar_pages in semantic_relations.items():
        if source in url_themes:
            source_theme = url_themes[source]
            source_idx = all_themes.index(source_theme)
            for page in similar_pages:
                if page['score'] >= min_score and page['url'] in url_themes:
                    target_theme = url_themes[page['url']]
                    target_idx = all_themes.index(target_theme)
                    potential_matrix[source_idx][target_idx] += 1

    # Calculer le ratio de couverture
    coverage_matrix = np.zeros((n_themes, n_themes))
    for i in range(n_themes):
        for j in range(n_themes):
            if potential_matrix[i][j] > 0:
                coverage_matrix[i][j] = existing_matrix[i][j] / potential_matrix[i][j]

    # Créer la heatmap avec Plotly
    fig = go.Figure()

    # Ajouter la heatmap du ratio de couverture
    fig.add_trace(go.Heatmap(
        z=coverage_matrix,
        x=all_themes,
        y=all_themes,
        colorscale='RdYlGn',  # Rouge (sous-maillé) à Vert (bien maillé)
        zmin=0,
        zmax=1,
        name='Ratio de couverture',
        hoverongaps=False,
        hovertemplate=(
                'De %{y} vers %{x}<br>' +
                'Liens existants: %{customdata[0]:.0f}<br>' +
                'Liens potentiels: %{customdata[1]:.0f}<br>' +
                'Couverture: %{z:.1%}<br>' +
                '<extra></extra>'
        ),
        customdata=np.dstack((existing_matrix, potential_matrix))
    ))

    # Mise en forme
    fig.update_layout(
        title='Heatmap du maillage entre thématiques',
        xaxis_title='Thématique cible',
        yaxis_title='Thématique source',
        height=800,
        width=1000,
        showlegend=True
    )

    return fig


def create_similarity_network(related_pages: Dict[str, List[Dict]], min_score: float = 0.5) -> str:
    """Crée une visualisation interactive du réseau de similarité entre les pages."""
    net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="black")

    # Configuration de la physique pour une meilleure visualisation des clusters
    physics_options = {
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -2000,  # Force de répulsion fortement augmentée
                "centralGravity": 0.005,  # Gravité centrale réduite
                "springLength": 400,  # Distance entre les nœuds augmentée
                "springConstant": 0.04,  # Élasticité des liens réduite
                "damping": 0.85  # Amortissement pour stabilisation
            },
            "maxVelocity": 50,  # Vitesse max de déplacement
            "solver": "forceAtlas2Based",
            "timestep": 0.3,
            "stabilization": {
                "iterations": 300,  # Plus d'itérations pour une meilleure stabilisation
                "updateInterval": 25
            },
            "minVelocity": 0.75  # Seuil minimal de mouvement
        },
        "interaction": {
            "hover": True,
            "navigationButtons": True,
            "keyboard": {
                "enabled": True
            },
            "zoomView": True  # Permet le zoom
        }
    }
    net.set_options(json.dumps(physics_options))

    # Calcul du degré de connectivité de chaque nœud
    connectivity = {}
    for source_url, similar_pages in related_pages.items():
        if source_url not in connectivity:
            connectivity[source_url] = 0
        for page in similar_pages:
            if page['score'] >= min_score:
                connectivity[source_url] += 1
                if page['url'] not in connectivity:
                    connectivity[page['url']] = 0
                connectivity[page['url']] += 1

    # Définir la palette de couleurs pour les clusters
    themes_colors = {
        'primary': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#F7D794'],  # Rouge, Turquoise, Bleu, Vert, Jaune
        'secondary': ['#EE5253', '#2D98DA', '#20BF6B', '#FA8231', '#8854D0']  # Nuances plus foncées
    }

    added_urls = set()
    theme_index = 0

    # Fonction pour obtenir une couleur basée sur la connectivité
    def get_node_color(url: str, theme_idx: int) -> str:
        base_color = themes_colors['primary'][theme_idx % len(themes_colors['primary'])]
        sec_color = themes_colors['secondary'][theme_idx % len(themes_colors['secondary'])]

        # Normaliser la connectivité entre 0 et 1
        max_conn = max(connectivity.values())
        norm_conn = connectivity[url] / max_conn if max_conn > 0 else 0

        # Mélanger les couleurs en fonction de la connectivité
        from colour import Color
        c1 = Color(base_color)
        c2 = Color(sec_color)
        gradient = list(c1.range_to(c2, 10))
        color_idx = int(norm_conn * 9)
        return gradient[color_idx].hex_l

    for source_url, similar_pages in related_pages.items():
        # Déterminer la thématique et la couleur du nœud source
        source_theme = extract_theme_from_url(source_url)

        if source_url not in added_urls:
            source_color = get_node_color(source_url, theme_index)
            net.add_node(
                source_url,
                label=get_readable_label(source_url),
                title=f"{source_url}\nConnectivité: {connectivity[source_url]}",
                color=source_color,
                size=20 + (connectivity[source_url] * 2),  # Taille basée sur la connectivité
                font={'size': 12, 'face': 'Arial'},
                shape='dot'
            )
            added_urls.add(source_url)
            theme_index = (theme_index + 1) % len(themes_colors['primary'])

        for page in similar_pages:
            if page['score'] >= min_score:
                target_url = page['url']
                target_theme = extract_theme_from_url(target_url)

                if target_url not in added_urls:
                    target_color = get_node_color(target_url, theme_index)
                    net.add_node(
                        target_url,
                        label=get_readable_label(target_url),
                        title=f"{target_url}\nConnectivité: {connectivity[target_url]}",
                        color=target_color,
                        size=20 + (connectivity[target_url] * 2),
                        font={'size': 12, 'face': 'Arial'},
                        shape='dot'
                    )
                    added_urls.add(target_url)

                # Lien avec épaisseur et couleur proportionnelles au score
                edge_width = page['score'] * 3
                # Utiliser une couleur semi-transparente pour les liens
                edge_alpha = page['score']  # Score comme niveau de transparence
                edge_color = f"rgba(128, 128, 128, {edge_alpha})"

                net.add_edge(
                    source_url,
                    target_url,
                    value=edge_width,
                    title=f"Score: {page['score']:.3f}",
                    color=edge_color,
                    smooth={'type': 'continuous'}
                )

    # Sauvegarder le graphe dans un fichier temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
        net.save_graph(tmp_file.name)
        return tmp_file.name