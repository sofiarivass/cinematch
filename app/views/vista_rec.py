"""
app/views/vista_rec.py
───────────────────
Capa de Vista (V en MVC).

Responsabilidades:
  - Renderizar los templates Jinja2.
  - Recibir datos del controlador y pasarlos al template.
  - Nunca contiene lógica de negocio.
"""

from flask import render_template


class RecomendacionesView:
    """Encapsula el renderizado de todas las vistas de recomendaciones."""

    def render_encuesta_rec(
        self,
        paso: int,
    ) -> str:
        return render_template(
            "encuesta_rec.html",
            paso=paso,
        )

    def render_recomendaciones(
        self,
        pelicula: dict,
        credits: dict,
        keywords: list,
        providers: dict,
        clasificacion: str,
    ) -> str:
        """
        Renderiza la vista de recomendaciones de películas.

        Args:
            pelicula: Dict con todos los datos de la película

        Returns:
            HTML renderizado como string
        """
        return render_template(
            "recomendaciones.html",
            pelicula=pelicula,
            credits=credits,
            keywords=keywords,
            providers=providers,
            clasificacion=clasificacion,
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
