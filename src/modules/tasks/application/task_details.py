from src.modules.auth.public import AccountRepository
from src.modules.tasks.domain.entities import Task, TaskDetail


def to_details(account: AccountRepository, tasks: list[Task]) -> list[TaskDetail]:
    user_ids = {task.created_by for task in tasks}
    user_ids |= {task.assigned_to for task in tasks if task.assigned_to is not None}
    usernames = {a.user_id: a.username for a in account.list_by_user_ids(list(user_ids))}

    return [
        TaskDetail(
            task=task,
            created_by_username=usernames[task.created_by],
            assigned_to_username=usernames[task.assigned_to] if task.assigned_to else None,
        )
        for task in tasks
    ]
