"""
app/controller/controlador_series.py
────────────────────────────────────
Capa de Controlador (C en MVC) para Series.

Responsabilidades:
  - Definir las rutas (URLs) de la aplicación.
  - Recibir los requests del usuario.
  - Llamar al Modelo para obtener los datos.
  - Pasar los datos a la Vista para renderizar.
"""

from flask import Blueprint, request, redirect, url_for
from app.model.modelo_series import SerieModel
from app.views.vista_series import SerieView

# Blueprint para series — todas las rutas quedan agrupadas aquí
series_bp = Blueprint("series", __name__)

# Instancias del modelo y la vista
modelo = SerieModel()
vista = SerieView()


# RUTA EXPLORAR
@series_bp.route("/series")
def explorar():
    """Muestra el listado de series con búsqueda."""
    query = request.args.get("q", "").strip()
    pagina = request.args.get("page", 1, type=int)

    try:
        if query:
            datos = modelo.buscar(query=query, pagina=pagina)
            titulo_seccion = f'Resultados para "{query}"'
        else:
            datos = modelo.obtener_populares(pagina=pagina)
            titulo_seccion = "Explorar series"

        return vista.render_explorar(
            series=datos["series"],
            pagina_actual=datos["pagina_actual"],
            total_paginas=datos["total_paginas"],
            titulo_seccion=titulo_seccion,
            query=query,
        )
    except Exception as e:
        return vista.render_error(str(e))


# RUTA BUSCAR
@series_bp.route("/series/buscar")
def buscar():
    """Busca series por título y muestra los resultados."""
    query = request.args.get("q", "").strip()
    pagina = request.args.get("page", 1, type=int)

    if not query:
        return redirect(url_for("series.explorar"))

    try:
        datos = modelo.buscar(query=query, pagina=pagina)
        return vista.render_explorar(
            series=datos["series"],
            pagina_actual=datos["pagina_actual"],
            total_paginas=datos["total_paginas"],
            titulo_seccion=f'Resultados para "{query}"',
            query=query,
        )
    except Exception as e:
        return vista.render_error(str(e))


# RUTA RECOMENDACIONES
@series_bp.route("/recomendacion/<int:serie_id>")
def recomendacion(serie_id: int):
    """Recomendacion de una serie."""
    try:
        serie = modelo.obtener_detalle(serie_id)
        credits = modelo.obtener_credits(serie_id)
        providers = modelo.obtener_providers(serie_id)
        clasificacion = modelo.obtener_clasificacion(serie_id)
        return vista.render_recomendaciones(
            serie, credits, providers, clasificacion
        )
    except Exception as e:
        return vista.render_error(str(e))


# RUTA DETALLE DE SERIE
@series_bp.route("/serie/<int:serie_id>")
def detalle(serie_id: int):
    """Muestra el detalle completo de una serie."""
    try:
        serie = modelo.obtener_detalle(serie_id)
        credits = modelo.obtener_credits(serie_id)
        keywords = modelo.obtener_keywords(serie_id)
        providers = modelo.obtener_providers(serie_id)
        clasificacion = modelo.obtener_clasificacion(serie_id)
        return vista.render_detalle(
            serie, credits, keywords, providers, clasificacion
        )
    except Exception as e:
        return vista.render_error(str(e))
