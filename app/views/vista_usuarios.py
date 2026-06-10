"""
app/views/vista_usuarios.py
───────────────────────────
Vista para renderizar templates de usuarios.
"""

from flask import render_template


class UsuarioView:
    """Renderiza templates relacionados con usuarios."""

    def render_registro(self):
        """
        Renderiza el formulario de registro.

        Returns:
            str: HTML del formulario de registro.
        """
        return render_template("registro.html")

    def render_error(self, codigo=500):
        """
        Renderiza página de error.

        Args:
            codigo (int): Código de error HTTP.

        Returns:
            str: HTML de error.
        """
        return render_template("error.html"), codigo

    # Agregado método para renderizar login
    def render_login(self):
        """
            Renderiza el formulario de inicio de sesión.

            Returns:
                str: HTML del formulario de login.
        """
        return render_template("login.html")
