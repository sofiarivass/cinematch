"""
app/views/vista_series.py
─────────────────────────
Capa de Vista (V en MVC) para Series.

Responsabilidades:
  - Renderizar los templates Jinja2.
  - Recibir datos del controlador y pasarlos al template.
  - Nunca contiene lógica de negocio.
"""

from flask import render_template


class SerieView:
    """Encapsula el renderizado de todas las vistas de series."""

    def render_explorar(
        self,
        series: list,
        pagina_actual: int,
        total_paginas: int,
        titulo_seccion: str,
        query: str = "",
    ) -> str:
        """
        Renderiza la vista de listado de series.

        Args:
            series         : Lista de dicts con datos de series
            pagina_actual  : Página actualmente mostrada
            total_paginas  : Total de páginas disponibles
            titulo_seccion : Título a mostrar en la sección
            query          : Texto de búsqueda (vacío si no es una búsqueda)

        Returns:
            HTML renderizado como string
        """
        return render_template(
            "series_explorar.html",
            series=series,
            pagina_actual=pagina_actual,
            total_paginas=total_paginas,
            titulo_seccion=titulo_seccion,
            query=query,
        )

    def render_detalle(
        self,
        serie: dict,
        credits: dict,
        keywords: list,
        providers: dict,
        clasificacion: str,
    ) -> str:
        """
        Renderiza la vista de detalle de una serie.

        Args:
            serie: Dict con todos los datos de la serie

        Returns:
            HTML renderizado como string
        """
        return render_template(
            "series_detalle.html",
            serie=serie,
            credits=credits,
            keywords=keywords,
            providers=providers,
            clasificacion=clasificacion,
        )

    def render_recomendaciones(
        self,
        serie: dict,
        credits: dict,
        providers: dict,
        clasificacion: str,
    ) -> str:
        """
        Renderiza la vista de recomendaciones de una serie.

        Args:
            serie: Dict con todos los datos de la serie
            credits: Dict con creadores y elenco
            providers: Dict con proveedores de streaming
            clasificacion: String con la clasificación

        Returns:
            HTML renderizado como string
        """
        return render_template(
            "series_detalle.html",
            serie=serie,
            credits=credits,
            keywords=[],
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
