from pathlib import Path


def test_missing_storage_returns_empty_list(task_store):
    assert task_store.load_tasks() == []


def test_save_creates_storage_and_writes_task(task_store):
    task_store.save_task("Read book", "Chapter one", "todo")

    saved = Path(task_store.tasks_folder) / "Read book.txt"
    assert saved.read_text() == "Chapter one\ntodo"


def test_status_update_preserves_description(task_store):
    folder = Path(task_store.tasks_folder)
    folder.mkdir()
    saved = folder / "Read book.txt"
    saved.write_text("Chapter one\ntodo")

    task_store.update_task_status(saved.name, "completed")

    assert saved.read_text().splitlines() == ["Chapter one", "completed"]


def test_delete_removes_only_requested_task(task_store):
    folder = Path(task_store.tasks_folder)
    folder.mkdir()
    selected = folder / "First.txt"
    other = folder / "Second.txt"
    selected.write_text("First task\ntodo")
    other.write_text("Second task\ntodo")

    task_store.delete_task(selected.name)

    assert not selected.exists()
    assert other.read_text() == "Second task\ntodo"
