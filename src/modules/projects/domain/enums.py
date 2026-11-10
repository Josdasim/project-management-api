from enum import StrEnum

class ProjectStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completado"

class ProjectRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"