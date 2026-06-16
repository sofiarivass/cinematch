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
from app.model.modelo import Model
from app.views.vista import View
from app.model.modelo_usuarios import UsuarioModel
from app.model.modelo_peliculas import PeliculaModel

# Blueprint principal — todas las rutas quedan agrupadas aquí
cinematch_bp = Blueprint("cinematch", __name__)

# Instancias del modelo y la vista
modelo = Model()
vista = View()
modelo_usuario = UsuarioModel()
modelo_peliculas = PeliculaModel()

# RUTA INICIO
@cinematch_bp.route("/")
def index():
    # 1. Verificar si hay una sesión activa de usuario
    nombre_usuario = session.get("nombre_usuario")
    
    if nombre_usuario:
        # Buscamos los datos del usuario en MongoDB
        usuario = modelo_usuario.obtener_por_nombre(nombre_usuario)
        
        if usuario and "preferencias" in usuario:
            preferencias = usuario["preferencias"]
            
            # Traemos el mix de películas que cumplen con sus gustos combinados
            peliculas_mix = modelo_peliculas.obtener_por_preferencias(preferencias)
            
            # Armamos las filas independientes por cada plataforma que el usuario posee
            secciones_por_plataforma = []
            
            # Obtenemos los nombres reales mapeando los providers disponibles en tu modelo
            todos_los_providers = modelo_peliculas.obtener_providers_ar()
            mapa_nombres = {p["id"]: p["nombre"] for p in todos_los_providers}

            for p_id in preferencias.get("plataformas", []):
                nombre_stream = mapa_nombres.get(p_id, f"Servicio {p_id}")
                movies_plataforma = modelo_peliculas.obtener_por_plataforma_individual(
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
    data_populares = modelo_peliculas.obtener_populares(1)
    peliculas_anonimas = data_populares.get("peliculas", [])[:18]
    
    return vista.render_index(
        peliculas=peliculas_anonimas, 
        secciones=[], 
        usuario=None
    )



# RUTA COMO FUNCIONA
# @cinematch_bp.route("/como-funciona")
# def como_funciona():
#     """Muestra la página de información."""
#     return vista.render_como_funciona()

# SESIÓN DE USUARIO Y RUTA DE ENCUESTA
@cinematch_bp.route("/encuesta-perfil", methods=["GET", "POST"])
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

            return redirect(url_for("cinematch.index"))

        siguiente_paso = paso + 1
    else:
        siguiente_paso = request.args.get("paso", 0, type=int)

    # Solo hace la llamada a la API cuando es necesario
    providers = modelo_peliculas.obtener_providers_ar() if siguiente_paso == 1 else []
    todos_providers = modelo_peliculas.obtener_todos_providers_ar() if siguiente_paso == 1 else []

    # 🟢 NUEVO: Si estamos en el paso 3, obtenemos todos los idiomas de TMDB
    todos_idiomas = modelo_peliculas.obtener_todos_idiomas() if siguiente_paso == 3 else []

    return vista.render_encuesta_perfil(
        paso=siguiente_paso,
        providers=providers,
        todos_providers=todos_providers,
        todos_idiomas=todos_idiomas,
    )