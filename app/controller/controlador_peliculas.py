"""
app/controller/controlador_peliculas.py
──────────────────────────────
Capa de Controlador (C en MVC).

Responsabilidades:
  - Definir las rutas (URLs) de la aplicación.
  - Recibir los requests del usuario.
  - Llamar al Modelo para obtener los datos.
  - Pasar los datos a la Vista para renderizar.
"""

from flask import Blueprint, request, redirect, url_for, session
from app.model.modelo_peliculas import PeliculaModel
from app.views.vista_peliculas import PeliculaView
from app.model.modelo_usuarios import UsuarioModel

# Blueprint principal — todas las rutas quedan agrupadas aquí
peliculas_bp = Blueprint("peliculas", __name__)

# Instancias del modelo y la vista
modelo = PeliculaModel()
modelo_usuario = UsuarioModel()
vista = PeliculaView()



# RUTA EXPLORAR
@peliculas_bp.route("/explorar")
def explorar():
    """Muestra el listado de películas con búsqueda."""
    query = request.args.get("q", "").strip()
    pagina = request.args.get("page", 1, type=int)

    try:
        if query:
            datos = modelo.buscar(query=query, pagina=pagina)
            titulo_seccion = f'Resultados para "{query}"'
        else:
            datos = modelo.obtener_populares(pagina=pagina)
            titulo_seccion = "Explorar películas"

        return vista.render_explorar(
            peliculas=datos["peliculas"],
            pagina_actual=datos["pagina_actual"],
            total_paginas=datos["total_paginas"],
            titulo_seccion=titulo_seccion,
            query=query,
        )
    except Exception as e:
        return vista.render_error(str(e))


# RUTA BUSCAR
@peliculas_bp.route("/buscar")
def buscar():
    """Busca películas por título y muestra los resultados."""
    query = request.args.get("q", "").strip()
    pagina = request.args.get("page", 1, type=int)

    if not query:
        return redirect(url_for("peliculas.explorar"))

    try:
        datos = modelo.buscar(query=query, pagina=pagina)
        return vista.render_explorar(
            peliculas=datos["peliculas"],
            pagina_actual=datos["pagina_actual"],
            total_paginas=datos["total_paginas"],
            titulo_seccion=f'Resultados para "{query}"',
            query=query,
        )
    except Exception as e:
        return vista.render_error(str(e))
    

# RUTA CONTENIDO MODAL DETALLE PELIS
@peliculas_bp.route("/pelicula/<int:pelicula_id>/modal")
def modal_pelicula(pelicula_id: int):
    try:
        pelicula = modelo.obtener_detalle(pelicula_id)
        credits = modelo.obtener_credits(pelicula_id)
        keywords = modelo.obtener_keywords(pelicula_id)
        providers = modelo.obtener_providers(pelicula_id)
        clasificacion = modelo.obtener_clasificacion(pelicula_id)
        trailer = modelo.obtener_trailer(pelicula_id)
        return vista.render_modal_pelicula(pelicula, credits, keywords, providers, clasificacion, trailer)
    except Exception as e:
        return str(e), 500