"""
app/controller/controlador.py
──────────────────────────────
Capa de Controlador (C en MVC).

Responsabilidades:
  - Definir las rutas (URLs) de la aplicación.
  - Recibir los requests del usuario.
  - Llamar al Modelo para obtener los datos.
  - Pasar los datos a la Vista para renderizar.
"""

from flask import Blueprint, request, redirect, url_for
from app.model.modelo_peliculas import PeliculaModel
from app.views.vista_peliculas import PeliculaView

# Blueprint principal — todas las rutas quedan agrupadas aquí
peliculas_bp = Blueprint("peliculas", __name__)

# Instancias del modelo y la vista
modelo = PeliculaModel()
vista  = PeliculaView()


# ── Ruta: Inicio — películas populares ────────────────────────────────────

@peliculas_bp.route("/")
def index():
    """Muestra la página principal con las películas populares."""
    pagina = request.args.get("page", 1, type=int)

    try:
        datos = modelo.obtener_populares(pagina=pagina)
        return vista.render_lista(
            peliculas    = datos["peliculas"],
            pagina_actual= datos["pagina_actual"],
            total_paginas= datos["total_paginas"],
            titulo_seccion= "Películas Populares",
        )
    except Exception as e:
        return vista.render_error(str(e))


# ── Ruta: Detalle de una película ─────────────────────────────────────────

@peliculas_bp.route("/pelicula/<int:pelicula_id>")
def detalle(pelicula_id: int):
    """Muestra el detalle completo de una película."""
    try:
        pelicula = modelo.obtener_detalle(pelicula_id)
        credits  = modelo.obtener_credits(pelicula_id)   # ← agregás esta línea
        keywords = modelo.obtener_keywords(pelicula_id)
        providers = modelo.obtener_providers(pelicula_id)
        clasificacion = modelo.obtener_clasificacion(pelicula_id)
        return vista.render_detalle(pelicula, credits, keywords, providers, clasificacion)
    except Exception as e:
        return vista.render_error(str(e))


# ── Ruta: Búsqueda ────────────────────────────────────────────────────────

@peliculas_bp.route("/buscar")
def buscar():
    """Busca películas por título y muestra los resultados."""
    query = request.args.get("q", "").strip()
    pagina = request.args.get("page", 1, type=int)

    if not query:
        return redirect(url_for("peliculas.index"))

    try:
        datos = modelo.buscar(query=query, pagina=pagina)
        return vista.render_lista(
            peliculas     = datos["peliculas"],
            pagina_actual = datos["pagina_actual"],
            total_paginas = datos["total_paginas"],
            titulo_seccion= f'Resultados para "{query}"',
            query         = query,
        )
    except Exception as e:
        return vista.render_error(str(e))
