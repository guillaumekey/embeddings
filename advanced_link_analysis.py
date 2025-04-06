import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Set, Tuple
import streamlit as st


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

    # Pages avec peu de liens entrants
    threshold = 7  # Par défaut, modifiable par l'utilisateur
    low_link_pages = incoming_links[incoming_links['Liens reçus'] < threshold]

    return {
        'incoming_links': incoming_links,
        'avg_links_per_page': avg_links_per_page,
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

    # Créer un histogramme de la distribution
    anchor_dist = distinct_anchors['Ancres distinctes'].value_counts().sort_index().reset_index()
    anchor_dist.columns = ['Nombre d\'ancres distinctes', 'Nombre d\'URLs']

    return {
        'distinct_anchors': distinct_anchors,
        'avg_anchors': avg_anchors,
        'anchor_dist': anchor_dist
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