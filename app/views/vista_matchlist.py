"""
app/views/vista_matchlist.py
────────────────────────────
Capa de Vista (V en MVC) para la Matchlist.
"""

from flask import render_template

class MatchlistView:
    """Encapsula el renderizado de la vista de la Matchlist completa."""

    def render_matchlist_completa(self, usuario, matchlist, peliculas_match, series_match) -> str:
        """
        Recibe los datos procesados del controlador y los pasa al template.
        No contiene lógica de negocio.
        """
        return render_template(
            "matchlist.html",
            usuario=usuario,
            matchlist=matchlist,
            peliculas_match=peliculas_match,
            series_match=series_match
        )