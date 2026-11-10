class ProjectsError(Exception):
    """Error base del modulo de proyectos"""

class ProjectNameAlreadyExistsError(ProjectsError):
    """El propietario ya tiene un proyecto con ese nombre"""
