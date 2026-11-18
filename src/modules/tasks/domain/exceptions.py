class TasksError(Exception):
    pass


class TaskNotFoundError(TasksError):
    pass


class TaskPermissionDeniedError(TasksError):
    pass


class InvalidAssigneeError(TasksError):
    pass