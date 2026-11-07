from uuid import uuid4

import pytest


@pytest.fixture
def task_data(page, base_url):
    """Give each test unique data; clean up only that test's task."""
    title = f"regression-{uuid4().hex}"
    yield {"title": title, "description": "Created by the regression suite"}
    # HTTP cleanup works even if the browser assertion failed.
    response = page.request.get(f"{base_url.rstrip('/')}/delete/{title}.txt")
    assert response.ok, f"Could not clean up test task {title}: {response.status}"
