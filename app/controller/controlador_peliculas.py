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


# RUTA INICIO
@peliculas_bp.route("/")
def index():
    # 1. Verificar si hay una sesión activa de usuario
    nombre_usuario = session.get("nombre_usuario")
    
    if nombre_usuario:
        # Buscamos los datos del usuario en MongoDB
        usuario = modelo_usuario.obtener_por_nombre(nombre_usuario)
        
        if usuario and "preferencias" in usuario:
            preferencias = usuario["preferencias"]
            
            # Traemos el mix de películas que cumplen con sus gustos combinados
            peliculas_mix = modelo.obtener_por_preferencias(preferencias)
            
            # Armamos las filas independientes por cada plataforma que el usuario posee
            secciones_por_plataforma = []
            
            # Obtenemos los nombres reales mapeando los providers disponibles en tu modelo
            todos_los_providers = modelo.obtener_providers_ar()
            mapa_nombres = {p["id"]: p["nombre"] for p in todos_los_providers}

            for p_id in preferencias.get("plataformas", []):
                nombre_stream = mapa_nombres.get(p_id, f"Servicio {p_id}")
                movies_plataforma = modelo.obtener_por_plataforma_individual(
                    plataforma_id=p_id, 
                    idiomas=preferencias.get("idiomas", [])
                )
                
                if movies_plataforma:
                    secciones_por_plataforma.append({
                        "nombre_plataforma": nombre_stream,
                        "peliculas": movies_plataforma[:6] # Mandamos las 6 primeras para el feed
                    })

            # Renderizamos usando tu vista adaptada
            return vista.render_index(
                peliculas=peliculas_mix,
                secciones=secciones_por_plataforma,
                usuario=usuario
            )

    # ── CASO ANÓNIMO O DEFAULT ─────────────────────────────────────────────
    # Si no inició sesión, corre tu lógica base original limpia
    data_populares = modelo.obtener_populares(1)
    peliculas_anonimas = data_populares.get("peliculas", [])[:18]
    
    return vista.render_index(
        peliculas=peliculas_anonimas, 
        secciones=[], 
        usuario=None
    )


# SESIÓN DE USUARIO Y RUTA DE ENCUESTA
@peliculas_bp.route("/encuesta-perfil", methods=["GET", "POST"])
def encuesta_perfil():
    if request.method == "POST":
        paso = int(request.form.get("paso", 0))

        # Guardar respuesta del paso actual en session
        if paso == 1:
            otras = request.form.get("plataformas_otras", "")
            plataformas_otras = [int(x) for x in otras.split(",") if x.strip().isdigit()]
            session["plataformas"] = list(set([int(p) for p in request.form.getlist("plataformas")] + plataformas_otras))
            session["plataformas_otras_ids"] = plataformas_otras 
        elif paso == 2:
            session["disponibilidad"] = request.form.get("disponibilidad")
        elif paso == 3:
            session["idiomas"] = request.form.getlist("idiomas")
        elif paso == 4:
            session["formato"] = request.form.get("formato")

            # 🟢 ENCUESTA FINALIZADA: Armamos el objeto JSON estructurado
            preferencias_finales = {
                "plataformas": session.get("plataformas", []),
                "disponibilidad": session.get("disponibilidad", "any"),
                "idiomas": session.get("idiomas", []),
                "formato": session.get("formato", "any"),
            }

            # Recuperamos el usuario actual de la sesión (ej: session.get("usuario"))
            # Si no manejás sesión con ese nombre, cambialo por la variable correspondiente
            usuario_actual = session.get("nombre_usuario")

            if usuario_actual:
                # Guardamos en MongoDB vía Pymongo
                modelo_usuario.guardar_preferencias(
                    usuario_actual, preferencias_finales
                )

            return redirect(url_for("peliculas.index"))

        siguiente_paso = paso + 1
    else:
        siguiente_paso = request.args.get("paso", 0, type=int)

    # Solo hace la llamada a la API cuando es necesario
    providers = modelo.obtener_providers_ar() if siguiente_paso == 1 else []
    todos_providers = modelo.obtener_todos_providers_ar() if siguiente_paso == 1 else []

    # 🟢 NUEVO: Si estamos en el paso 3, obtenemos todos los idiomas de TMDB
    todos_idiomas = modelo.obtener_todos_idiomas() if siguiente_paso == 3 else []

    return vista.render_encuesta_perfil(
        paso=siguiente_paso,
        providers=providers,
        todos_providers=todos_providers,
        todos_idiomas=todos_idiomas,
    )


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
    try:
        pelicula = modelo.obtener_detalle(pelicula_id)
        credits = modelo.obtener_credits(pelicula_id)
        keywords = modelo.obtener_keywords(pelicula_id)

        # 🟢 CAMBIADO: usar obtener_providers para la película individual
        providers = modelo.obtener_providers(pelicula_id)

        clasificacion = modelo.obtener_clasificacion(pelicula_id)
        return vista.render_recomendaciones(
            pelicula, credits, keywords, providers, clasificacion
        )
    except Exception as e:
        return vista.render_error(str(e))


# RUTA DETALLE DE PELÍCULA
@peliculas_bp.route("/pelicula/<int:pelicula_id>")
def detalle(pelicula_id: int):
    try:
        pelicula = modelo.obtener_detalle(pelicula_id)
        credits = modelo.obtener_credits(pelicula_id)
        keywords = modelo.obtener_keywords(pelicula_id)
        trailer = modelo.obtener_trailer(pelicula_id)

        # 🟢 CAMBIADO: usar obtener_providers para la película individual
        providers = modelo.obtener_providers(pelicula_id)

        clasificacion = modelo.obtener_clasificacion(pelicula_id)
        return vista.render_detalle(
            pelicula, credits, keywords, providers, clasificacion, trailer
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

