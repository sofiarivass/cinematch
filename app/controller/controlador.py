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
                    plataforma_id=p_id, idiomas=preferencias.get("idiomas", [])
                )

                if movies_plataforma:
                    secciones_por_plataforma.append(
                        {
                            "nombre_plataforma": nombre_stream,
                            "peliculas": movies_plataforma[
                                :6
                            ],  # Mandamos las 6 primeras para el feed
                        }
                    )

            # Renderizamos usando tu vista adaptada
            return vista.render_index(
                peliculas=peliculas_mix,
                secciones=secciones_por_plataforma,
                usuario=usuario,
            )

    # ── CASO ANÓNIMO O DEFAULT ─────────────────────────────────────────────
    # Si no inició sesión, corre tu lógica base original limpia
    data_populares = modelo_peliculas.obtener_populares(1)
    peliculas_anonimas = data_populares.get("peliculas", [])[:18]

    return vista.render_index(peliculas=peliculas_anonimas, secciones=[], usuario=None)


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

    generos = modelo.obtener_generos()
    anios = modelo.obtener_anios()
    plataformas = modelo_peliculas.obtener_providers_ar()

    # Construir URLs de paginación en el controlador (Jinja2 no soporta dict.update)
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
        peliculas=datos["resultados"],
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


# SESIÓN DE USUARIO Y RUTA DE ENCUESTA
@cinematch_bp.route("/encuesta-perfil", methods=["GET", "POST"])
def encuesta_perfil():
    if request.method == "POST":
        paso = int(request.form.get("paso", 0))
        error = False  # 🟢 NUEVO: Bandera para controlar si hay error

        # Validación y guardado según el paso
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
            # Podrías tener idiomas en inputs ocultos si usan la opción "Otro"
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

                # 🟢 ENCUESTA FINALIZADA
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

                return redirect(url_for("cinematch.index"))

        # 🟢 NUEVO: Decidimos qué paso sigue
        if error:
            flash("Por favor, seleccioná al menos una opción para continuar.", "danger")
            siguiente_paso = paso  # Se queda en el mismo paso
        else:
            siguiente_paso = paso + 1

    else:
        siguiente_paso = request.args.get("paso", 0, type=int)

    # Solo hace la llamada a la API cuando es necesario
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
