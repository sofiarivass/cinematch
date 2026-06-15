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

    def render_explorar(
        self,
        peliculas: list,
        pagina_actual: int,
        total_paginas: int,
        titulo_seccion: str,
        query: str = "",
        ) -> str:
        """
        Renderiza la vista de listado de películas.

        Args:
            peliculas      : Lista de dicts con datos de películas
            pagina_actual  : Página actualmente mostrada
            total_paginas  : Total de páginas disponibles
            titulo_seccion : Título a mostrar en la sección
            query          : Texto de búsqueda (vacío si no es una búsqueda)

        Returns:
            HTML renderizado como string
        """
        return render_template(
            "explorar.html",
            peliculas=peliculas,
            pagina_actual=pagina_actual,
            total_paginas=total_paginas,
            titulo_seccion=titulo_seccion,
            query=query,
        )

    # def render_detalle(
    #     self,
    #     pelicula: dict,
    #     credits: dict,
    #     keywords: list,
    #     providers: dict,
    #     clasificacion: str,
    #     trailer: str | None = None,
    # ) -> str:
    #     """
    #     Renderiza la vista de detalle de una película.

    #     Args:
    #         pelicula: Dict con todos los datos de la película

    #     Returns:
    #         HTML renderizado como string
    #     """
    #     return render_template(
    #         "detalle.html",
    #         pelicula=pelicula,
    #         credits=credits,
    #         keywords=keywords,
    #         providers=providers,
    #         clasificacion=clasificacion,
    #         trailer=trailer,
    #     )

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
