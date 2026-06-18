"""
app/views/vista_series.py
───────────────────
Capa de Vista (V en MVC).

Responsabilidades:
  - Renderizar los templates Jinja2.
  - Recibir datos del controlador y pasarlos al template.
  - Nunca contiene lógica de negocio.
"""

from flask import render_template


class SerieView:
    """Encapsula el renderizado de todas las vistas de series."""

    def render_modal_serie(self, serie, credits, keywords, providers, clasificacion, trailer=None, estados=None) -> str:
        """
        Renderiza el modal con el detalle de una serie específica.
        """
        return render_template(
            "modal_serie.html",
            serie=serie,
            credits=credits,
            keywords=keywords,
            providers=providers,
            clasificacion=clasificacion,
            trailer=trailer,
            estados=estados or {"matchlist": False, "favoritos": False, "series_vistas": False},
        )

    def render_error(self, mensaje: str) -> tuple[str, int]:
        """
        Renderiza la vista de error.

        Args:
            mensaje: Descripción del error ocurrido

        Returns:
            Tupla (HTML, código HTTP 500)
        """
        return render_template("error.html", mensaje=mensaje), 500