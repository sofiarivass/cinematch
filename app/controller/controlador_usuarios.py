"""
app/controller/controlador_usuarios.py
─────────────────────────────────────
Controlador para gestionar rutas de usuarios (registro, login, etc.)
"""

from flask import Blueprint, request, redirect, url_for, flash, jsonify, session
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