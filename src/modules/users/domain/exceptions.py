class UsersError(Exception):
    """Base de los errores de dominio del modulo Users"""


class UserNotFoundError(UsersError):
    """El usuario no existe"""
