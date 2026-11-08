class AuthError(Exception):
    """Base de los error de dominio del modulo AUTH"""


class UsernameAlreadyExistsError(AuthError):
    """El nombre de usuario ya esta registrado"""


class EmailAlreadyExistsError(AuthError):
    """El correo electronico ya esta registrado"""


class InvalidTokenError(AuthError):
    """El Token es invalido, esta vencido o esta mal formado"""


class InvalidCredentialsError(AuthError):
    """Credenciales incorrectas o cuenta no habilitada para iniciar sesion"""
