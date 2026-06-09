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

from flask import Blueprint, request, redirect, url_for, session
from app.model.modelo_peliculas import PeliculaModel
from app.views.vista_peliculas import PeliculaView

# Blueprint principal — todas las rutas quedan agrupadas aquí
peliculas_bp = Blueprint("peliculas", __name__)

# Instancias del modelo y la vista
modelo = PeliculaModel()
vista = PeliculaView()


# RUTA INICIO
@peliculas_bp.route("/")
def index():
    return vista.render_index()


# SESIÓN DE USUARIO Y RUTA DE ENCUESTA
@peliculas_bp.route("/encuesta-perfil", methods=["GET", "POST"])
def encuesta_perfil():
    if request.method == "POST":
        paso = int(request.form.get("paso", 0))

        # Guardar respuesta del paso actual en session
        if paso == 1:
            session["plataformas"] = request.form.getlist("plataformas")
        elif paso == 2:
            session["disponibilidad"] = request.form.get("disponibilidad")
        elif paso == 3:
            session["idiomas"] = request.form.getlist("idiomas")
        elif paso == 4:
            session["formato"] = request.form.get("formato")
            return redirect(url_for("peliculas.index"))  # Encuesta finalizada

        siguiente_paso = paso + 1
    else:
        siguiente_paso = 0
        session.clear()

    # Solo hace la llamada a la API cuando es necesario
    providers = modelo.obtener_providers_ar() if siguiente_paso == 1 else []
    todos_providers = modelo.obtener_todos_providers_ar() if siguiente_paso == 1 else []

    return vista.render_encuesta_perfil(paso=siguiente_paso, providers=providers, todos_providers=todos_providers)


# # RUTA ENCUESTA PERFIL
# @peliculas_bp.route("/encuesta-perfil")
# def encuesta_perfil():
#     return vista.render_encuesta_perfil(paso=0)


# @peliculas_bp.route("/")
# def index():
#     """Muestra la página principal."""
#     pagina = request.args.get("page", 1, type=int)

#     try:
#         datos = modelo.obtener_populares(pagina=pagina)
#         return vista.render_explorar(
#             peliculas=datos["peliculas"],
#             pagina_actual=datos["pagina_actual"],
#             total_paginas=datos["total_paginas"],
#             titulo_seccion="Películas Populares",
#         )
#     except Exception as e:
#         return vista.render_error(str(e))


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


# RUTA RECOMENDACIONES
@peliculas_bp.route("/recomendacion/<int:pelicula_id>")
def recomendacion(pelicula_id: int):
    """Recomendacion de una película."""
    try:
        pelicula = modelo.obtener_detalle(pelicula_id)
        credits = modelo.obtener_credits(pelicula_id)
        keywords = modelo.obtener_keywords(pelicula_id)
        providers = modelo.obtener_providers(pelicula_id)
        clasificacion = modelo.obtener_clasificacion(pelicula_id)
        return vista.render_recomendaciones(
            pelicula, credits, keywords, providers, clasificacion
        )
    except Exception as e:
        return vista.render_error(str(e))


# RUTA COMO FUNCIONA
@peliculas_bp.route("/como-funciona")
def como_funciona():
    """Muestra la página de información."""
    return vista.render_como_funciona()


# RUTA DETALLE DE PELÍCULA
@peliculas_bp.route("/pelicula/<int:pelicula_id>")
def detalle(pelicula_id: int):
    """Muestra el detalle completo de una película."""
    try:
        pelicula = modelo.obtener_detalle(pelicula_id)
        credits = modelo.obtener_credits(pelicula_id)
        keywords = modelo.obtener_keywords(pelicula_id)
        providers = modelo.obtener_providers(pelicula_id)
        clasificacion = modelo.obtener_clasificacion(pelicula_id)
        return vista.render_detalle(
            pelicula, credits, keywords, providers, clasificacion
        )
    except Exception as e:
        return vista.render_error(str(e))
