from tests.modules.projects.conftest import PROJECTS_URL, access_token, bearer
from tests.modules.tasks.conftest import new_task, project


# MOD-01
def test_conservar_las_tareas_al_eliminar_y_recuperarlas_al_restaurar(
    client, access_token, project
):
    task = new_task(
        client,
        access_token,
        project["id"],
        title="Mi tarea",
        description="Detalle",
        priority="high",
        assigned_to="dana_01",
    )
    task_url = f"{PROJECTS_URL}/{project['id']}/tasks/{task['id']}"

    client.delete(f"{PROJECTS_URL}/{project['id']}", headers=bearer(access_token))
    hidden = client.get(task_url, headers=bearer(access_token))
    client.post(f"{PROJECTS_URL}/{project['id']}/restore", headers=bearer(access_token))
    back = client.get(task_url, headers=bearer(access_token))

    assert hidden.status_code == 404
    assert back.status_code == 200
    assert back.json()["title"] == "Mi tarea"
    assert back.json()["description"] == "Detalle"
    assert back.json()["priority"] == "high"
    assert back.json()["assigned_to"] == "dana_01"
