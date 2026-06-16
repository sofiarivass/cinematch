"""
app/views/vista_peliculas.py
───────────────────
Capa de Vista (V en MVC).

Responsabilidades:
  - Renderizar los templates Jinja2.
  - Recibir datos del controlador y pasarlos al template.
  - Nunca contiene lógica de negocio.
"""

from flask import render_template


class PeliculaView:
    """Encapsula el renderizado de todas las vistas de películas."""

    def render_modal_pelicula(self, pelicula, credits, keywords, providers, clasificacion, trailer=None) -> str:
        return render_template(
            "modal_pelicula.html",
            pelicula=pelicula,
            credits=credits,
            keywords=keywords,
            providers=providers,
            clasificacion=clasificacion,
            trailer=trailer,
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
