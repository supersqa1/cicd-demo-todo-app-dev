from pathlib import Path

import pytest


@pytest.mark.parametrize("status", ["in progress", "completed"])
def test_task_lifecycle_through_routes(client, task_store, status):
    response = client.post("/add", data={"title": "Practice CI", "description": "Run tests"})
    assert response.status_code == 302
    assert response.headers["Location"] == "/view_tasks"

    page = client.get("/view_tasks")
    assert page.status_code == 200
    assert b"Practice CI" in page.data
    assert b"Run tests" in page.data
    saved = Path(task_store.tasks_folder) / "Practice CI.txt"
    assert saved.read_text().splitlines() == ["Run tests", "todo"]

    response = client.post("/update_status/Practice%20CI.txt", data={"status": status})
    assert response.status_code == 302
    assert saved.read_text().splitlines() == ["Run tests", status]
    assert client.get("/view_tasks").status_code == 200

    response = client.get("/delete/Practice%20CI.txt")
    assert response.status_code == 302
    assert not saved.exists()
    assert b"Practice CI" not in client.get("/view_tasks").data


def test_missing_title_is_rejected_without_saving(client, task_store):
    response = client.post("/add", data={"description": "Missing title"})

    assert response.status_code == 400
    assert not Path(task_store.tasks_folder).exists()
