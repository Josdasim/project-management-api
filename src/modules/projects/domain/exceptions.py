class ProjectsError(Exception):
    """Error base del modulo de proyectos"""


class ProjectNameAlreadyExistsError(ProjectsError):
    """El propietario ya tiene un proyecto con ese nombre"""


class ProjectNotFoundError(ProjectsError):
    """El proyecto no existe o la persona no tiene acceso a el"""


class ProjectPermissionDeniedError(ProjectsError):
    """El rol del usuario en el proyecto no permite esta accion"""
