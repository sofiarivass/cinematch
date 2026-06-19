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

from flask import Blueprint, flash, request, redirect, url_for, session
from app.model.modelo import Model
from app.views.vista import View
from app.model.modelo_usuarios import UsuarioModel
from app.model.modelo_peliculas import PeliculaModel
from app.model.modelo_series import SerieModel


# Blueprint principal — todas las rutas quedan agrupadas aquí
cinematch_bp = Blueprint("cinematch", __name__)

# Instancias del modelo y la vista
modelo = Model()
vista = View()
modelo_usuario = UsuarioModel()
modelo_peliculas = PeliculaModel()
modelo_series = SerieModel()


# RUTA INICIO
@cinematch_bp.route("/")
def index():
    # 1. Verificar si hay una sesión activa de usuario
    nombre_usuario = session.get("nombre_usuario")

    if nombre_usuario:
        # Buscamos los datos del usuario en MongoDB
        usuario = modelo_usuario.obtener_por_nombre(nombre_usuario)

        if usuario:
            # 🟢 CONTROL DE SEGURIDAD: Si está logueado pero no completó la encuesta,
            # lo redirigimos obligatoriamente para que configure su perfil.
            if not usuario.get("preferencias") or not usuario["preferencias"].get("plataformas"):
                return redirect(url_for("cinematch.encuesta_perfil", paso=1))

            preferencias = usuario["preferencias"]

            # Traemos el mix de películas que cumplen con sus gustos combinados
            peliculas_mix = modelo_peliculas.obtener_por_preferencias(preferencias)
            series_mix = modelo_series.obtener_por_preferencias(preferencias)

            # Armamos las filas independientes por cada plataforma que el usuario posee
            secciones_por_plataforma = []

            # Obtenemos los nombres reales mapeando los providers disponibles en tu modelo
            principales = modelo_peliculas.obtener_providers_ar()
            otras = modelo_peliculas.obtener_todos_providers_ar()
            catálogo_completo = principales + otras

            mapa_nombres = {p["id"]: p["nombre"] for p in catálogo_completo}

           
            # Iteramos solo por las plataformas que el usuario seleccionó en su encuesta (peliculas y series)
            for p_id in preferencias.get("plataformas", []):
                nombre_stream = mapa_nombres.get(p_id, f"Servicio {p_id}")
                movies = []
                series_data = []

                # 1. Intentar buscar películas
                try:
                    movies = modelo_peliculas.obtener_por_plataforma_individual(
                        plataforma_id=p_id, 
                        idiomas=preferencias.get("idiomas", [])
                    ) or []
                except Exception as e:
                    print(f"DEBUG: Error al llamar películas para {p_id}: {e}")

                # 2. Intentar buscar series
                try:
                    series_data = modelo_series.obtener_por_plataforma_individual(
                        plataforma_id=p_id, 
                        idiomas=preferencias.get("idiomas", [])
                    ) or []
                except Exception as e:
                    print(f"DEBUG: Error al llamar series para {p_id}: {e}")

                # 3. Solo agregamos la sección si la plataforma devolvió AL MENOS películas o series
                if movies or series_data:
                    secciones_por_plataforma.append({
                        "nombre_plataforma": nombre_stream,
                        "peliculas": movies[:6],      # Limitamos a 6 o la cantidad que uses
                        "series": series_data[:6]      # Limitamos a 6
                    })


            # Renderizamos usando tu vista adaptada
            return vista.render_index(
                peliculas=peliculas_mix,
                series=series_mix,
                secciones=secciones_por_plataforma,
                usuario=usuario,
            )

    # ── CASO ANÓNIMO O DEFAULT ─────────────────────────────────────────────
    # Si no inició sesión, corre tu lógica base original limpia
    data_populares = modelo_peliculas.obtener_populares(1)
    peliculas_anonimas = data_populares.get("peliculas", [])[:18]
    series_anonimas = modelo_series.obtener_series_populares(1).get("series", [])[:18]
    peliculas_tendencia = modelo_peliculas.obtener_tendencias(1).get("peliculas", [])[:8]

    return vista.render_index(peliculas=peliculas_anonimas, series=series_anonimas, secciones=[{"nombre": "Tendencias", "peliculas": peliculas_tendencia}], usuario=None)


# ── BUSCAR (redirige a explorar con q=) ───────────────────────────────────────
@cinematch_bp.route("/buscar")
def buscar():
    query = request.args.get("q", "").strip()
    if not query:
        return redirect(url_for("cinematch.explorar"))
    return redirect(url_for("cinematch.explorar", q=query))


# ── EXPLORAR ───────────────────────────────────────
@cinematch_bp.route("/explorar")
def explorar():

    def _int_or_none(key):
        try:
            v = request.args.get(key)
            return int(v) if v else None
        except (ValueError, TypeError):
            return None

    def _float_or_none(key):
        try:
            v = request.args.get(key)
            return float(v) if v else None
        except (ValueError, TypeError):
            return None

    filtros = {
        "q": (request.args.get("q") or "").strip(),
        "tipo": request.args.get("tipo", "todo"),
        "genero": _int_or_none("genero"),
        "anio": _int_or_none("anio"),
        "plataforma": _int_or_none("plataforma"),
        "puntaje": _float_or_none("puntaje"),
        "duracion": request.args.get("duracion"),
        "orden": request.args.get("orden", "popularidad"),
        "pagina": max(1, _int_or_none("pagina") or 1),
    }

    try:
        datos = modelo.explorar(filtros)
        error = None
    except Exception as e:
        datos = {"resultados": [], "total_paginas": 1, "pagina_actual": 1, "total": 0}
        error = str(e)

    # ── NORMALIZAR EL TIPO ESPECÍFICO DE CADA ELEMENTO ──
    for item in datos.get("resultados", []):
        # 1. Si el modelo ya trae el media_type explícito (desde la API de TMDB ej: 'movie' o 'tv')
        if "media_type" in item and item["media_type"]:
            item["tipo_render"] = "movie" if item["media_type"] == "movie" else "tv"
        
        # 2. Si el usuario filtró específicamente en la barra lateral por película o serie
        elif filtros["tipo"] == "pelicula":
            item["tipo_render"] = "movie"
        elif filtros["tipo"] == "serie":
            item["tipo_render"] = "tv"
        
        # 3. Caso "Todo" (mismatch preventivo): Deducción por propiedades nativas de TMDB
        else:
            # Las series usan 'name' o 'first_air_date'. Las películas usan 'title' o 'release_date'
            if "name" in item or "first_air_date" in item:
                item["tipo_render"] = "tv"
            else:
                item["tipo_render"] = "movie"

    generos = modelo.obtener_generos()
    anios = modelo.obtener_anios()
    plataformas = modelo_peliculas.obtener_providers_ar()

    # Construir URLs de paginación en el controlador
    total_paginas = datos["total_paginas"]
    pagina_actual = datos["pagina_actual"]

    def _url_pagina(p):
        args = {k: v for k, v in request.args.items() if k != "pagina" and v}
        args["pagina"] = p
        return url_for("cinematch.explorar", **args)

    def _url_tipo(t):
        args = {
            k: v for k, v in request.args.items() if k not in ("tipo", "pagina") and v
        }
        if t != "todo":
            args["tipo"] = t
        return url_for("cinematch.explorar", **args)

    url_tipo_todo = _url_tipo("todo")
    url_tipo_pelicula = _url_tipo("pelicula")
    url_tipo_serie = _url_tipo("serie")

    paginas_info = []
    for p in range(1, total_paginas + 1):
        if p == 1 or p == total_paginas or abs(p - pagina_actual) <= 2:
            paginas_info.append({"num": p, "url": _url_pagina(p), "tipo": "pagina"})
        elif abs(p - pagina_actual) == 3:
            paginas_info.append({"num": "…", "url": None, "tipo": "ellipsis"})

    return vista.render_explorar(
        peliculas=datos["resultados"],  # Van con el atributo 'tipo_render' inyectado
        pagina_actual=pagina_actual,
        total_paginas=total_paginas,
        total=datos["total"],
        filtros=filtros,
        generos=generos,
        anios=anios,
        plataformas=plataformas,
        paginas_info=paginas_info,
        url_anterior=_url_pagina(pagina_actual - 1) if pagina_actual > 1 else None,
        url_siguiente=(
            _url_pagina(pagina_actual + 1) if pagina_actual < total_paginas else None
        ),
        url_tipo_todo=url_tipo_todo,
        url_tipo_pelicula=url_tipo_pelicula,
        url_tipo_serie=url_tipo_serie,
        error=error,
    )


# RUTA MODAL DETALLE (Controlador General)
@cinematch_bp.route("/explorar/modal/<int:id_contenido>")
def enrutador_modal(id_contenido):
    """
    Enrutador intermedio calibrado para el esquema unificado.
    Recibe los tipos normalizados: 'pelicula' o 'serie'.
    """
    tipo = request.args.get("tipo", "pelicula")

    try:
        # Evaluamos con los strings en español del modelo
        if tipo == "pelicula":
            try:
                from app.controller.controlador_peliculas import modal_pelicula
            except ImportError:
                from controller.controlador_peliculas import modal_pelicula
            return modal_pelicula(pelicula_id=id_contenido)
            
        else: # Si es 'serie'
            try:
                from app.controller.controlador_series import modal_serie
            except ImportError:
                from controller.controlador_series import modal_serie
            return modal_serie(serie_id=id_contenido)
            
    except Exception as e:
        print("\n====== ERROR EN EL ENRUTADOR INTERMEDIO ======")
        import traceback
        traceback.print_exc()
        print("==============================================\n")
        return f"Error interno en el servidor: {str(e)}", 500


# SESIÓN DE USUARIO Y RUTA DE ENCUESTA
@cinematch_bp.route("/encuesta-perfil", methods=["GET", "POST"])
def encuesta_perfil():
    # 🟢 CONTROL DE ACCESO: Si no hay usuario en sesión, no puede hacer la encuesta
    if not session.get("usuario_id"):
        flash("Debes iniciar sesión para personalizar tu perfil.", "warning")
        return redirect(url_for("usuarios.login"))

    if request.method == "POST":
        paso = int(request.form.get("paso", 0))
        error = False 

        if paso == 1:
            plataformas = request.form.getlist("plataformas")
            otras = request.form.get("plataformas_otras", "")

            # Validamos que haya seleccionado al menos una o escrito otra
            if not plataformas and not otras:
                error = True
            else:
                plataformas_otras = [
                    int(x) for x in otras.split(",") if x.strip().isdigit()
                ]
                session["plataformas"] = list(
                    set([int(p) for p in plataformas] + plataformas_otras)
                )
                session["plataformas_otras_ids"] = plataformas_otras

        elif paso == 2:
            disponibilidad = request.form.get("disponibilidad")
            if not disponibilidad:
                error = True
            else:
                session["disponibilidad"] = disponibilidad

        elif paso == 3:
            idiomas = request.form.getlist("idiomas")
            if not idiomas:
                error = True
            else:
                session["idiomas"] = idiomas

        elif paso == 4:
            formato = request.form.get("formato")
            if not formato:
                error = True
            else:
                session["formato"] = formato

                # ENCUESTA FINALIZADA - Recopilación
                preferencias_finales = {
                    "plataformas": session.get("plataformas", []),
                    "disponibilidad": session.get("disponibilidad", "any"),
                    "idiomas": session.get("idiomas", []),
                    "formato": session.get("formato", "any"),
                }

                usuario_actual = session.get("nombre_usuario")
                if usuario_actual:
                    modelo_usuario.guardar_preferencias(
                        usuario_actual, preferencias_finales
                    )

                flash("¡Tu experiencia ha sido personalizada con éxito!", "success")
                return redirect(url_for("cinematch.index"))

        if error:
            flash("Por favor, seleccioná al menos una opción para continuar.", "danger")
            siguiente_paso = paso  # Se queda en el mismo paso
        else:
            siguiente_paso = paso + 1

    else:
        siguiente_paso = request.args.get("paso", 0, type=int)

    providers = modelo_peliculas.obtener_providers_ar() if siguiente_paso == 1 else []
    todos_providers = (
        modelo_peliculas.obtener_todos_providers_ar() if siguiente_paso == 1 else []
    )
    todos_idiomas = (
        modelo_peliculas.obtener_todos_idiomas() if siguiente_paso == 3 else []
    )

    return vista.render_encuesta_perfil(
        paso=siguiente_paso,
        providers=providers,
        todos_providers=todos_providers,
        todos_idiomas=todos_idiomas,
    )
