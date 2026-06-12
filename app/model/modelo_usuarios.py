"""
app/model/modelo_usuarios.py
────────────────────────────
Modelo CRUD para usuarios con MongoDB.
Gestiona registro, búsqueda y validación de usuarios.
"""

from pymongo import MongoClient
from config.config import Config
from datetime import datetime
import hashlib
import re
from bson.objectid import ObjectId
from flask import session


class UsuarioModel:
    """
    Modelo para gestionar usuarios en MongoDB.
    Realiza operaciones CRUD.
    """

    def __init__(self):
        """Inicializa conexión a MongoDB."""
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client["cinematch"]
        self.usuarios = self.db["usuarios"]

    def _conectar(self):
        """Verifica la conexión a MongoDB."""
        try:
            self.client.admin.command("ping")
            return True
        except Exception as e:
            print(f"Error conectando a MongoDB: {e}")
            return False

    def _hash_password(self, contraseña):
        """
        Hashea una contraseña usando SHA256.

        Args:
            contraseña (str): Contraseña a hashear.

        Returns:
            str: Contraseña hasheada.
        """
        return hashlib.sha256(contraseña.encode()).hexdigest()

    def _validar_email(self, email):
        """
        Valida formato de email.

        Args:
            email (str): Email a validar.

        Returns:
            bool: True si es válido, False si no.
        """
        patron = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(patron, email) is not None

    def crear(self, nombre_usuario, email, contraseña, fecha_nacimiento, preferencias, google_auth=False):
        """
        Crea un nuevo usuario.

        Args:
            nombre_usuario (str): Nombre de usuario.
            email (str): Correo electrónico.
            contraseña (str): Contraseña.
            fecha_nacimiento (str): Fecha de nacimiento (YYYY-MM-DD).

        Returns:
            dict: Resultado con 'exito' (bool) y 'mensaje' (str).
        """
        try:
            # Validar email
            if not self._validar_email(email):
                return {"exito": False, "mensaje": "El email no es válido"}

            # Validar que no exista usuario con el mismo nombre o email
            if self.usuarios.find_one({"nombre_usuario": nombre_usuario}):
                return {"exito": False, "mensaje": "El nombre de usuario ya existe"}

            if self.usuarios.find_one({"email": email}):
                return {"exito": False, "mensaje": "El email ya está registrado"}

            # Crear documento
            usuario = {
                "nombre_usuario": nombre_usuario,
                "email": email,
                "contraseña": self._hash_password(contraseña) if contraseña else None,
                "fecha_nacimiento": fecha_nacimiento,
                "preferencias": preferencias,
                "google_auth": google_auth,
                "fecha_registro": datetime.now(),
            }

            # Insertar en BD
            resultado = self.usuarios.insert_one(usuario)

            return {
                "exito": True,
                "mensaje": "Usuario registrado correctamente",
                "usuario_id": str(resultado.inserted_id),
            }

        except Exception as e:
            return {"exito": False, "mensaje": f"Error al registrar: {str(e)}"}

    def obtener_por_nombre(self, nombre_usuario):
        """
        Obtiene un usuario por nombre de usuario.

        Args:
            nombre_usuario (str): Nombre de usuario.

        Returns:
            dict: Documento del usuario o None si no existe.
        """
        try:
            return self.usuarios.find_one({"nombre_usuario": nombre_usuario})
        except Exception as e:
            print(f"Error buscando usuario: {e}")
            return None

    def obtener_por_email(self, email):
        """
        Obtiene un usuario por email.

        Args:
            email (str): Correo electrónico.

        Returns:
            dict: Documento del usuario o None si no existe.
        """
        try:
            return self.usuarios.find_one({"email": email})
        except Exception as e:
            print(f"Error buscando usuario: {e}")
            return None

    def obtener_por_id(self, usuario_id):
        """
        Obtiene un usuario por ID.

        Args:
            usuario_id (str): ID de MongoDB.

        Returns:
            dict: Documento del usuario o None si no existe.
        """
        try:
            from bson.objectid import ObjectId

            return self.usuarios.find_one({"_id": ObjectId(usuario_id)})
        except Exception as e:
            print(f"Error buscando usuario: {e}")
            return None

    def verificar_contraseña(self, nombre_usuario, contraseña):
        """
        Verifica si la contraseña es correcta para un usuario.

        Args:
            nombre_usuario (str): Nombre de usuario.
            contraseña (str): Contraseña a verificar.

        Returns:
            bool: True si es correcta, False si no.
        """
        usuario = self.obtener_por_nombre(nombre_usuario)
        if not usuario:
            return False
        return usuario["contraseña"] == self._hash_password(contraseña)

    def actualizar(self, nombre_usuario, datos):
        """
        Actualiza datos de un usuario.

        Args:
            nombre_usuario (str): Nombre de usuario.
            datos (dict): Campos a actualizar.

        Returns:
            dict: Resultado de la operación.
        """
        try:
            resultado = self.usuarios.update_one(
                {"nombre_usuario": nombre_usuario}, {"$set": datos}
            )
            if resultado.modified_count > 0:
                return {"exito": True, "mensaje": "Usuario actualizado"}
            return {"exito": False, "mensaje": "No se realizaron cambios"}
        except Exception as e:
            return {"exito": False, "mensaje": f"Error al actualizar: {str(e)}"}

    def eliminar(self, nombre_usuario):
        """
        Elimina un usuario.

        Args:
            nombre_usuario (str): Nombre de usuario.

        Returns:
            dict: Resultado de la operación.
        """
        try:
            resultado = self.usuarios.delete_one({"nombre_usuario": nombre_usuario})
            if resultado.deleted_count > 0:
                return {"exito": True, "mensaje": "Usuario eliminado"}
            return {"exito": False, "mensaje": "Usuario no encontrado"}
        except Exception as e:
            return {"exito": False, "mensaje": f"Error al eliminar: {str(e)}"}

    def obtener_todos(self):
        """
        Obtiene todos los usuarios (sin mostrar contraseñas).

        Returns:
            list: Lista de usuarios.
        """
        try:
            usuarios = list(self.usuarios.find({}, {"contraseña": 0}))
            return usuarios
        except Exception as e:
            print(f"Error obteniendo usuarios: {e}")
            return []

    # Método adicional para autenticar usuarios normales y guardar sesión
    def autenticar(self, email, contraseña):
        """Autentica un usuario por email y contraseña.

        Args:
            email (str): Correo electrónico.
            contraseña (str): Contraseña sin hashear.

        Returns:
            dict: Resultado con 'exito' (bool) y 'mensaje' (str).
        """
        try:
            # Buscar usuario por email
            usuario = self.obtener_por_email(email)

            if not usuario:
                return {"exito": False, "mensaje": "El correo no está registrado"}

            # Verificar contraseña
            if usuario["contraseña"] != self._hash_password(contraseña):
                return {"exito": False, "mensaje": "Contraseña incorrecta"}

            # Guardar sesión
            session["usuario_id"] = str(usuario["_id"])
            session["nombre_usuario"] = usuario["nombre_usuario"]
            session["email"] = usuario["email"]

            return {
                "exito": True,
                "mensaje": f"Bienvenido, {usuario['nombre_usuario']}",
            }
        except Exception as e:
            return {"exito": False, "mensaje": f"Error al autenticar: {str(e)}"}

    def guardar_preferencias(self, nombre_usuario, preferencias_dict):
        """
        Guarda el objeto/diccionario de preferencias consolidado dentro del usuario.
        """
        # Usamos el método actualizar que ya tenías programado
        return self.actualizar(nombre_usuario, {"preferencias": preferencias_dict})
    
    # Método adicional para generar un nombre de usuario único a partir del email
    def generar_nombre_usuario_unico(self, email):
        """
        Genera un nombre de usuario único a partir del email.
        """

        base = email.split("@")[0]
        nombre_usuario = base

        contador = 1

        while self.obtener_por_nombre(nombre_usuario):
            nombre_usuario = f"{base}{contador}"
            contador += 1

        return nombre_usuario
