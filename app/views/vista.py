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

    def render_index(
        self, peliculas: list = [], series: list = [], secciones: list = [], usuario: dict = None
    ) -> str:
        return render_template(
            "index.html", peliculas=peliculas, series=series, secciones=secciones, usuario=usuario
        )

    def render_explorar(
        self,
        peliculas: list,
        pagina_actual: int,
        total_paginas: int,
        total: int,
        filtros: dict,
        generos: list,
        anios: list,
        plataformas: list,
        paginas_info: list,
        url_anterior: str = None,
        url_siguiente: str = None,
        url_tipo_todo: str = None,
        url_tipo_pelicula: str = None,
        url_tipo_serie: str = None,
        error: str = None,
    ) -> str:
        return render_template(
            "explorar.html",
            peliculas=peliculas,
            pagina_actual=pagina_actual,
            paginas=total_paginas,
            total=total,
            filtros=filtros,
            generos=generos,
            anios=anios,
            plataformas=plataformas,
            paginas_info=paginas_info,
            url_anterior=url_anterior,
            url_siguiente=url_siguiente,
            url_tipo_todo=url_tipo_todo,
            url_tipo_pelicula=url_tipo_pelicula,
            url_tipo_serie=url_tipo_serie,
            error=error,
        )

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
