"""
app/controller/controlador_usuarios.py
─────────────────────────────────────
Controlador para gestionar rutas de usuarios (registro, login, etc.)
"""

from flask import Blueprint, request, redirect, url_for, flash, jsonify, session
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
            if not all([nombre_usuario, email, contraseña, repetir_contraseña, fecha_nacimiento]):
                return jsonify({
                    "exito": False,
                    "mensaje": "Todos los campos son requeridos"
                }), 400

            if len(nombre_usuario) < 3:
                return jsonify({
                    "exito": False,
                    "mensaje": "El nombre de usuario debe tener al menos 3 caracteres"
                }), 400

            if len(contraseña) < 6:
                return jsonify({
                    "exito": False,
                    "mensaje": "La contraseña debe tener al menos 6 caracteres"
                }), 400

            if contraseña != repetir_contraseña:
                return jsonify({
                    "exito": False,
                    "mensaje": "Las contraseñas no coinciden"
                }), 400

            if not terminos:
                return jsonify({
                    "exito": False,
                    "mensaje": "Debes aceptar los términos y condiciones"
                }), 400

            # Crear usuario
            resultado = usuario_modelo.crear(
                nombre_usuario, email, contraseña, fecha_nacimiento, preferencias={}
            )

            
            # Si el registro fue exitoso, iniciar sesión automáticamente
            if resultado["exito"]:
                session['usuario_id'] = resultado['usuario_id'] 
                session['nombre_usuario'] = nombre_usuario 
                return jsonify({
                    "exito": True,
                    "mensaje": resultado["mensaje"],
                    "redirigir": url_for("peliculas.encuesta_perfil")
                }), 201

    except Exception as e:
        print(f"Error en registro: {e}")
        return jsonify({
            "exito": False,
            "mensaje": "Ocurrió un error al procesar tu solicitud"
        }), 500

# login, logout y otras rutas de usuario se implementarían aquí siguiendo un patrón similar
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
                return jsonify({
                    "exito": False,
                    "mensaje": "Todos los campos son requeridos"
                }), 400

            if len(contraseña) < 6:
                return jsonify({
                    "exito": False,
                    "mensaje": "La contraseña debe tener al menos 6 caracteres"
                }), 400

            # Autenticar usuario
            resultado = usuario_modelo.autenticar(email, contraseña)

            if resultado["exito"]:
                return jsonify({
                    "exito": True,
                    "mensaje": resultado["mensaje"],
                    "redirigir": url_for("peliculas.index")
                }), 200
            else:
                return jsonify({
                    "exito": False,
                    "mensaje": resultado["mensaje"]
                }), 401

    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({
            "exito": False,
            "mensaje": "Ocurrió un error al procesar tu solicitud"
        }), 500

# logout para cerrar sesión del usuario
@usuarios_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('peliculas.index'))

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
                google_auth=True
            )

            if not resultado["exito"]:
                return jsonify({
                    "exito": False,
                    "mensaje": "Error creando usuario con Google"
                }), 500

            # sesión
            session["usuario_id"] = resultado["usuario_id"]
            session["nombre_usuario"] = nombre_usuario

            return redirect(url_for("peliculas.encuesta_perfil"))

        # Si ya existe
        session["usuario_id"] = str(usuario["_id"])
        session["nombre_usuario"] = usuario["nombre_usuario"]

        return redirect(url_for("peliculas.index"))

    except Exception as e:
        import traceback
        print("\n🔥 ERROR COMPLETO GOOGLE OAUTH 🔥")
        print(traceback.format_exc())

        return jsonify({
            "exito": False,
            "mensaje": str(e)
        }), 500