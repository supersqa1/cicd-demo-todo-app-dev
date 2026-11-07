import pytest
from playwright.sync_api import expect


def create_task(page, task_data):
    page.goto("/create_task")
    page.get_by_label("Title:", exact=True).fill(task_data["title"])
    page.get_by_label("Description:", exact=True).fill(task_data["description"])
    page.get_by_role("button", name="Add Task", exact=True).click()
    expect(page).to_have_url("/view_tasks")
    return page.get_by_role("listitem").filter(
        has=page.get_by_role("heading", name=task_data["title"], exact=True)
    )


def test_create_task_survives_reload(page, task_data):
    task = create_task(page, task_data)
    expect(task).to_contain_text(task_data["description"])
    expect(task.get_by_role("combobox")).to_have_value("todo")
    page.reload()
    expect(task).to_be_visible()
    expect(task).to_contain_text(task_data["description"])
    expect(task.get_by_role("combobox")).to_have_value("todo")


@pytest.mark.parametrize("status", ["in progress", "completed"])
def test_change_status_survives_reload(page, task_data, status):
    task = create_task(page, task_data)
    # Changing status submits a form and navigates back to the task list.
    with page.expect_navigation(wait_until="domcontentloaded"):
        task.get_by_role("combobox").select_option(status)
    page.reload()
    expect(task.get_by_role("combobox")).to_have_value(status)


def test_delete_task_stays_deleted(page, task_data):
    task = create_task(page, task_data)
    task.get_by_role("link", name="Delete", exact=True).click()
    expect(task).to_have_count(0)
    page.reload()
    expect(task).to_have_count(0)
