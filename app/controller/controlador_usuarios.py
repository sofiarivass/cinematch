"""
app/controller/controlador_usuarios.py
─────────────────────────────────────
Controlador para gestionar rutas de usuarios (registro, login, etc.)
"""

import io
import base64
import matplotlib.pyplot as plt
from flask import Blueprint, request, redirect, url_for, flash, jsonify, session, make_response
from app.services.google_oauth import oauth
from app.model.modelo_usuarios import UsuarioModel
from app.views.vista_usuarios import UsuarioView

# Crear blueprint
usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

# Instanciar modelo y vista
usuario_modelo = UsuarioModel()
usuario_vista = UsuarioView()


@usuarios_bp.route("/registro", methods=["GET", "POST"])
def registro():
    """
    Ruta para mostrar y procesar el formulario de registro.

    GET: Muestra el formulario de registro.
    POST: Procesa el formulario y registra al usuario.
    """
    try:
        if request.method == "GET":
            return usuario_vista.render_registro()

        # POST: Procesar registro
        if request.method == "POST":
            nombre_usuario = request.form.get("nombre_usuario", "").strip()
            email = request.form.get("email", "").strip()
            contraseña = request.form.get("contraseña", "")
            repetir_contraseña = request.form.get("repetir_contraseña", "")
            fecha_nacimiento = request.form.get("fecha_nacimiento", "")
            terminos = request.form.get("terminos")

            # Validaciones básicas
            if not all(
                [
                    nombre_usuario,
                    email,
                    contraseña,
                    repetir_contraseña,
                    fecha_nacimiento,
                ]
            ):
                return (
                    jsonify(
                        {"exito": False, "mensaje": "Todos los campos son requeridos"}
                    ),
                    400,
                )

            if len(nombre_usuario) < 3:
                return (
                    jsonify(
                        {
                            "exito": False,
                            "mensaje": "El nombre de usuario debe tener al menos 3 caracteres",
                        }
                    ),
                    400,
                )

            if len(contraseña) < 6:
                return (
                    jsonify(
                        {
                            "exito": False,
                            "mensaje": "La contraseña debe tener al menos 6 caracteres",
                        }
                    ),
                    400,
                )

            if contraseña != repetir_contraseña:
                return (
                    jsonify(
                        {"exito": False, "mensaje": "Las contraseñas no coinciden"}
                    ),
                    400,
                )

            if not terminos:
                return (
                    jsonify(
                        {
                            "exito": False,
                            "mensaje": "Debes aceptar los términos y condiciones",
                        }
                    ),
                    400,
                )

            # Crear usuario
            resultado = usuario_modelo.crear(
                nombre_usuario, email, contraseña, fecha_nacimiento, preferencias={}
            )

            # Si el registro fue exitoso, iniciar sesión automáticamente
            if resultado["exito"]:
                session["usuario_id"] = resultado["usuario_id"]
                session["nombre_usuario"] = nombre_usuario
                return (
                    jsonify(
                        {
                            "exito": True,
                            "mensaje": resultado["mensaje"],
                            "redirigir": url_for("cinematch.encuesta_perfil"),
                        }
                    ),
                    201,
                )

    except Exception as e:
        print(f"Error en registro: {e}")
        return (
            jsonify(
                {"exito": False, "mensaje": "Ocurrió un error al procesar tu solicitud"}
            ),
            500,
        )



@usuarios_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Ruta para mostrar y procesar el formulario de inicio de sesión.

    GET: Muestra el formulario de login.
    POST: Procesa el formulario y autentica al usuario.
    """
    try:
        if request.method == "GET":
            return usuario_vista.render_login()

        if request.method == "POST":
            email = request.form.get("email", "").strip()
            contraseña = request.form.get("contraseña", "")

            # Validaciones básicas
            if not all([email, contraseña]):
                return (
                    jsonify(
                        {"exito": False, "mensaje": "Todos los campos son requeridos"}
                    ),
                    400,
                )

            if len(contraseña) < 6:
                return (
                    jsonify(
                        {
                            "exito": False,
                            "mensaje": "La contraseña debe tener al menos 6 caracteres",
                        }
                    ),
                    400,
                )

            # Autenticar usuario (El modelo guarda los datos en session internamente)
            resultado = usuario_modelo.autenticar(email, contraseña)

            if resultado["exito"]:
                return (
                    jsonify(
                        {
                            "exito": True,
                            "mensaje": resultado["mensaje"],
                            "redirigir": url_for("cinematch.index"),
                        }
                    ),
                    200,
                )
            else:
                return jsonify({"exito": False, "mensaje": resultado["mensaje"]}), 401

    except Exception as e:
        print(f"Error en login: {e}")
        return (
            jsonify(
                {"exito": False, "mensaje": "Ocurrió un error al procesar tu solicitud"}
            ),
            500,
        )



@usuarios_bp.route("/logout")
def logout():
    """
    Limpia las variables de sesión del servidor y destruye las cookies
    del navegador para evitar estados 'bugeados' o heredados.
    """
    # 1. Limpiar por completo el diccionario de sesión del lado del servidor
    session.clear()
    
    # 2. Crear respuesta para redireccionar al index/inicio
    response = make_response(redirect(url_for('cinematch.index')))
    
    # 3. Forzar al navegador a destruir la cookie de sesión de Flask
    response.set_cookie('session', '', expires=0)
    
    return response


# Ruta para login con Google
@usuarios_bp.route("/login/google")
def login_google():
    redirect_uri = url_for(
        "usuarios.google_callback",
        _external=True
    )
    return oauth.google.authorize_redirect(redirect_uri)


@usuarios_bp.route("/google/callback")
def google_callback():
    try:
        # Obtener token y datos de Google
        token = oauth.google.authorize_access_token()

        user_info = token.get("userinfo")

        if not user_info:
            user_info = oauth.google.parse_id_token(token, nonce=None)

        email = user_info["email"]

        # Buscar usuario en BD
        usuario = usuario_modelo.obtener_por_email(email)

        if not usuario:
            nombre_usuario = usuario_modelo.generar_nombre_usuario_unico(email)
            # Crear usuario si no existe
            resultado = usuario_modelo.crear(
                nombre_usuario=nombre_usuario,
                email=email,
                contraseña=None,
                fecha_nacimiento=None,
                preferencias={},
                google_auth=True,
            )

            if not resultado["exito"]:
                return (
                    jsonify(
                        {"exito": False, "mensaje": "Error creando usuario con Google"}
                    ),
                    500,
                )

            # sesión
            session["usuario_id"] = resultado["usuario_id"]
            session["nombre_usuario"] = nombre_usuario

            return redirect(url_for("cinematch.encuesta_perfil"))

        # Si ya existe
        session["usuario_id"] = str(usuario["_id"])
        session["nombre_usuario"] = usuario["nombre_usuario"]

        return redirect(url_for("cinematch.index"))

    except Exception as e:
        import traceback

        print("\n🔥 ERROR COMPLETO GOOGLE OAUTH 🔥")
        print(traceback.format_exc())

        return jsonify({"exito": False, "mensaje": str(e)}), 500


import io
import base64
import matplotlib

matplotlib.use("Agg")  # backend sin GUI, obligatorio en servidor
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from flask import Blueprint, request, redirect, url_for, session, jsonify
from app.model.modelo_usuarios import PerfilModel
from app.model.modelo import Model
from app.views.vista_usuarios import VistaPerfil

perfil_bp = Blueprint("perfil", __name__)
modelo_perfil = PerfilModel()
modelo_explorar = Model()
vista = VistaPerfil()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _usuario_requerido():
    """Devuelve el nombre de usuario o None si no hay sesión."""
    return session.get("nombre_usuario")


def _generar_grafico_actividad(actividad_mensual: dict) -> str:
    """
    Genera el gráfico de barras de actividad mensual con matplotlib.
    Devuelve la imagen como string base64 para incrustar en el HTML.
    """
    meses = list(actividad_mensual.keys())
    valores = list(actividad_mensual.values())

    fig, ax = plt.subplots(figsize=(7, 3))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    bars = ax.bar(meses, valores, color="#3b82f6", width=0.6, zorder=3)

    # Estilo oscuro coherente con la UI
    ax.tick_params(colors="#7a8db3", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#1d2d4a")
    ax.spines["bottom"].set_color("#1d2d4a")
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.grid(axis="y", color="#1d2d4a", linewidth=0.8, zorder=0)

    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + 0.1,
                str(int(h)),
                ha="center",
                va="bottom",
                fontsize=7,
                color="#7a8db3",
            )

    plt.tight_layout(pad=0.5)

    img = io.BytesIO()
    plt.savefig(img, format="png", transparent=True, dpi=120)
    img.seek(0)
    plt.close(fig)

    return base64.b64encode(img.getvalue()).decode()


# ── Ruta principal del perfil ─────────────────────────────────────────────────


@perfil_bp.route("/perfil")
def perfil():
    nombre_usuario = _usuario_requerido()
    if not nombre_usuario:
        return redirect(url_for("usuarios.login"))

    # Datos del usuario
    usuario = modelo_perfil.usuario_model.obtener_por_nombre(nombre_usuario)
    if not usuario:
        return redirect(url_for("usuarios.login"))

    # Listas
    listas = modelo_perfil.obtener_listas(nombre_usuario)
    conteos = modelo_perfil.calcular_conteos(listas)

    # Estadísticas — necesitamos el mapa id→nombre de géneros
    generos_tmdb = modelo_explorar.obtener_generos()
    mapa_generos = {g["id"]: g["nombre"] for g in generos_tmdb}
    stats = modelo_perfil.calcular_estadisticas(nombre_usuario, mapa_generos)

    # Gráfico matplotlib
    plot_url = _generar_grafico_actividad(stats["actividad_mensual"])

    # Pasamos solo las primeras 5 de cada lista para el preview
    return vista.render_perfil(
        usuario=usuario,
        conteos=conteos,
        matchlist=listas["matchlist"][:5],
        favoritos=listas["favoritos"][:5],
        peliculas_vistas=listas["peliculas_vistas"][:5],
        series_vistas=listas["series_vistas"][:5],
        generos=stats["generos"],
        plot_url=plot_url,
    )


# ── API: toggle de listas (llamadas AJAX desde el modal de película) ──────────


@perfil_bp.route("/perfil/lista/<lista>")
def lista_completa(lista):
    nombre_usuario = _usuario_requerido()
    if not nombre_usuario:
        return redirect(url_for("usuarios.login"))
    items = modelo_perfil.obtener_lista(nombre_usuario, lista)


@perfil_bp.route("/perfil/lista/toggle", methods=["POST"])
def toggle_lista():
    """
    Agrega o quita un item de una lista del usuario.
    Recibe JSON: { lista, id, tipo, titulo, poster, puntuacion, fecha, genero_ids }
    Devuelve JSON: { accion: "agregado" | "quitado", lista }
    """
    nombre_usuario = _usuario_requerido()
    if not nombre_usuario:
        return jsonify({"error": "No autenticado"}), 401

    data = request.get_json()
    print("DATA RECIBIDA:", data)  # ← agregá esto
    lista = data.get("lista")
    item_id = data.get("id")
    tipo = data.get("tipo")

    if not all([lista, item_id, tipo]):
        print("FALLÓ VALIDACIÓN:", lista, item_id, tipo)  # ← agregá esto
        return jsonify({"error": "Faltan campos"}), 400

    ya_estaba = modelo_perfil.esta_en_lista(nombre_usuario, lista, item_id, tipo)

    if ya_estaba:
        modelo_perfil.quitar_de_lista(nombre_usuario, lista, item_id, tipo)
        accion = "quitado"
    else:
        item = {
            "id": item_id,
            "tipo": tipo,
            "titulo": data.get("titulo", ""),
            "poster": data.get("poster", ""),
            "puntuacion": data.get("puntuacion", 0),
            "fecha": data.get("fecha", ""),
            "genero_ids": data.get("genero_ids", []),
        }
        modelo_perfil.agregar_a_lista(nombre_usuario, lista, item)
        accion = "agregado"

    return jsonify({"accion": accion, "lista": lista})


@perfil_bp.route("/perfil/lista/estado", methods=["GET"])
def estado_listas():
    """
    Dado un item (id + tipo), devuelve en qué listas está el usuario.
    Query params: id, tipo
    Devuelve JSON: { favoritos: bool, matchlist: bool, peliculas_vistas: bool, series_vistas: bool }
    """
    nombre_usuario = _usuario_requerido()
    if not nombre_usuario:
        return jsonify(
            {
                lista: False
                for lista in (
                    "favoritos",
                    "matchlist",
                    "peliculas_vistas",
                    "series_vistas",
                )
            }
        )

    item_id = request.args.get("id", type=int)
    tipo = request.args.get("tipo", "")

    return jsonify(
        {
            lista: modelo_perfil.esta_en_lista(nombre_usuario, lista, item_id, tipo)
            for lista in ("favoritos", "matchlist", "peliculas_vistas", "series_vistas")
        }
    )