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


class View:
    """Encapsula el renderizado de todas las vistas de películas."""

    def render_index(self) -> str:
        return render_template("index.html")

    def render_como_funciona(self) -> str:
        return render_template("como_funciona.html")
    
    def render_encuesta_perfil(
        self,
        paso: int,
        providers: list = [],
        todos_providers: list = [],
        todos_idiomas: list = [],
    ) -> str:
        return render_template(
            "encuesta_perfil.html",
            paso=paso,
            providers=providers,
            todos_providers=todos_providers,
            todos_idiomas=todos_idiomas,
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
