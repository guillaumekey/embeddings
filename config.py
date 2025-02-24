import streamlit as st


def setup_page():
    """Configure la page Streamlit."""
    st.set_page_config(
        page_title="Analyse de similarité sémantique des pages web",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def setup_sidebar():
    """Configure la barre latérale avec les paramètres."""
    st.sidebar.header("Paramètres")
    top_n = st.sidebar.slider("Nombre de pages similaires à afficher", 1, 20, 5)

    # Configuration des paramètres de filtrage avancé
    st.sidebar.header("Filtres d'URL")

    # Filtres d'inclusion
    st.sidebar.subheader("Inclusion (ET)")
    include_exact = st.sidebar.text_input(
        "URLs qui contiennent exactement",
        help="Mots exacts séparés par des virgules"
    )
    include_partial = st.sidebar.text_input(
        "URLs qui contiennent partiellement",
        help="Parties de mots séparés par des virgules"
    )

    # Filtres d'exclusion
    st.sidebar.subheader("Exclusion (ET)")
    exclude_exact = st.sidebar.text_input(
        "URLs qui ne contiennent pas exactement",
        help="Mots exacts séparés par des virgules"
    )
    exclude_partial = st.sidebar.text_input(
        "URLs qui ne contiennent pas partiellement",
        help="Parties de mots séparés par des virgules"
    )

    # Sélecteur de niveau pour l'analyse thématique
    st.sidebar.header("Analyse thématique")
    theme_level = st.sidebar.selectbox(
        "Niveau de profondeur pour l'analyse thématique",
        options=[1, 2, 3],
        format_func=lambda x: f"Niveau {x}",
        help="Niveau 1: premier dossier, Niveau 2: second dossier, etc."
    )

    return top_n, include_exact, include_partial, exclude_exact, exclude_partial, theme_level