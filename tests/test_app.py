
import pytest
import app as cloudtask


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"

    monkeypatch.setattr(
        cloudtask,
        "DATABASE",
        str(db_path)
    )

    cloudtask.app.config["TESTING"] = True
    cloudtask.app.config["SECRET_KEY"] = "test-secret-key"

    cloudtask.init_db()

    with cloudtask.app.test_client() as client:
        yield client


def register(client, username="testuser", password="password123"):
    return client.post(
        "/register",
        data={"username": username, "password": password},
        follow_redirects=True
    )


def login(client, username="testuser", password="password123"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True
    )


def test_home_redirects_to_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.location


def test_user_registration(client):
    response = register(client)

    assert response.status_code == 200
    assert b"Registration successful" in response.data


def test_duplicate_username(client):
    register(client)
    response = register(client)

    assert b"Username already exists" in response.data


def test_short_password_rejected(client):
    response = register(client, password="123")

    assert b"at least 6 characters" in response.data


def test_successful_login(client):
    register(client)
    response = login(client)

    assert response.status_code == 200
    assert b"Dashboard" in response.data or b"Add Task" in response.data


def test_invalid_login(client):
    register(client)
    response = login(client, password="wrongpassword")

    assert b"Invalid username or password" in response.data


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")

    assert response.status_code == 302
    assert "/login" in response.location


def test_add_task(client):
    register(client)
    login(client)

    response = client.post(
        "/add",
        data={
            "title": "Test Task",
            "description": "Testing CloudTask"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Test Task" in response.data


def test_update_task_status(client):
    register(client)
    login(client)

    client.post(
        "/add",
        data={"title": "Update Test", "description": ""}
    )

    conn = cloudtask.get_db()
    task = conn.execute(
        "SELECT id FROM tasks WHERE title = ?",
        ("Update Test",)
    ).fetchone()
    conn.close()

    response = client.post(
        f"/update/{task['id']}",
        data={"status": "Completed"},
        follow_redirects=True
    )

    assert response.status_code == 200

    conn = cloudtask.get_db()
    updated = conn.execute(
        "SELECT status FROM tasks WHERE id = ?",
        (task["id"],)
    ).fetchone()
    conn.close()

    assert updated["status"] == "Completed"


def test_invalid_task_status(client):
    register(client)
    login(client)

    response = client.post(
        "/update/1",
        data={"status": "Invalid"}
    )

    assert response.status_code == 400


def test_delete_task(client):
    register(client)
    login(client)

    client.post(
        "/add",
        data={"title": "Delete Test", "description": ""}
    )

    conn = cloudtask.get_db()
    task = conn.execute(
        "SELECT id FROM tasks WHERE title = ?",
        ("Delete Test",)
    ).fetchone()
    conn.close()

    response = client.post(
        f"/delete/{task['id']}",
        follow_redirects=True
    )

    assert response.status_code == 200

    conn = cloudtask.get_db()
    deleted = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task["id"],)
    ).fetchone()
    conn.close()

    assert deleted is None


def test_user_cannot_update_another_users_task(client):
    register(client, "user1")
    login(client, "user1")

    client.post(
        "/add",
        data={"title": "Private Task", "description": ""}
    )

    conn = cloudtask.get_db()
    task = conn.execute(
        "SELECT id FROM tasks WHERE title = ?",
        ("Private Task",)
    ).fetchone()
    conn.close()

    client.get("/logout")

    register(client, "user2")
    login(client, "user2")

    client.post(
        f"/update/{task['id']}",
        data={"status": "Completed"}
    )

    conn = cloudtask.get_db()
    result = conn.execute(
        "SELECT status FROM tasks WHERE id = ?",
        (task["id"],)
    ).fetchone()
    conn.close()

    assert result["status"] == "Pending"
