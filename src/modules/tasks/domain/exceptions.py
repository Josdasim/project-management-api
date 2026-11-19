class TasksError(Exception):
    pass


class TaskNotFoundError(TasksError):
    pass


class TaskPermissionDeniedError(TasksError):
    pass


class InvalidAssigneeError(TasksError):
    pass


class InvalidStatusTransitionError(TasksError):
    pass


class TaskNotEditableError(TasksError):
    pass
