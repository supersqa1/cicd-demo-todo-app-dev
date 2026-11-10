import pytest


@pytest.fixture
def task_store(tmp_path, monkeypatch):
    """Give each backend test its own storage, never the app's real tasks."""
    from app import main

    monkeypatch.setattr(main, "tasks_folder", str(tmp_path / "tasks"))
    monkeypatch.setitem(main.app.config, "TESTING", True)
    return main


@pytest.fixture
def client(task_store):
    return task_store.app.test_client()
