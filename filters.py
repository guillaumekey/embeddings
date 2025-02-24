import pandas as pd
from typing import List, Tuple


def clean_terms(terms_str: str) -> List[str]:
    """Nettoie et sépare les termes de filtrage."""
    if terms_str:
        return [term.strip() for term in terms_str.split(',') if term.strip()]
    return []


def apply_url_filters(df: pd.DataFrame,
                      include_exact: str,
                      include_partial: str,
                      exclude_exact: str,
                      exclude_partial: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Applique les filtres d'URL et retourne le DataFrame filtré et la liste des URLs filtrées.
    """
    filtered_df = df.copy()
    filtered_urls = None

    # Application des filtres d'inclusion exacts
    include_exact_terms = clean_terms(include_exact)
    if include_exact_terms:
        for term in include_exact_terms:
            filtered_df = filtered_df[filtered_df['URL'].str.contains(f"/{term}/", case=False)]
        filtered_urls = filtered_df['URL'].tolist()

    # Application des filtres d'inclusion partiels
    include_partial_terms = clean_terms(include_partial)
    if include_partial_terms:
        for term in include_partial_terms:
            filtered_df = filtered_df[filtered_df['URL'].str.contains(term, case=False)]
        filtered_urls = filtered_df['URL'].tolist()

    # Application des filtres d'exclusion exacts
    exclude_exact_terms = clean_terms(exclude_exact)
    if exclude_exact_terms:
        for term in exclude_exact_terms:
            filtered_df = filtered_df[~filtered_df['URL'].str.contains(f"/{term}/", case=False)]
        filtered_urls = filtered_df['URL'].tolist()

    # Application des filtres d'exclusion partiels
    exclude_partial_terms = clean_terms(exclude_partial)
    if exclude_partial_terms:
        for term in exclude_partial_terms:
            filtered_df = filtered_df[~filtered_df['URL'].str.contains(term, case=False)]
        filtered_urls = filtered_df['URL'].tolist()

    return filtered_df, filtered_urls