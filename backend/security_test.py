"""
Security isolation test for Autonomous Work Agent.

Run from the backend folder:
    python security_test.py

This test creates two temporary users, creates test records directly in the
database, then uses the real FastAPI endpoints with each user's JWT.

It verifies that one user cannot access another user's:
- tasks
- approvals
- connections
- permissions
- tool activity
- approval creation referencing another user's task
"""

import uuid
from pathlib import Path
import sys

# Make imports work when this file is executed from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bcrypt
from fastapi.testclient import TestClient

import models
from database import SessionLocal
from main import app, create_access_token


def assert_status(response, expected, label):
    if response.status_code != expected:
        raise AssertionError(
            f"{label}: expected HTTP {expected}, "
            f"got {response.status_code}: {response.text}"
        )


def main():
    suffix = uuid.uuid4().hex[:10]

    user_a_email = f"security_a_{suffix}@example.test"
    user_b_email = f"security_b_{suffix}@example.test"
    password = "SecurityTest123!"

    db = SessionLocal()
    user_a = user_b = None

    try:
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        user_a = models.User(
            email=user_a_email,
            password_hash=password_hash
        )
        user_b = models.User(
            email=user_b_email,
            password_hash=password_hash
        )

        db.add_all([user_a, user_b])
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)

        # Create records belonging to each user.
        task_a = models.Task(
            goal="Security test task A",
            status="pending",
            user_id=user_a.id,
            workspace="browser"
        )
        task_b = models.Task(
            goal="Security test task B",
            status="pending",
            user_id=user_b.id,
            workspace="browser"
        )

        connection_a = models.Connection(
            service="test_service_a",
            status="connected",
            user_id=user_a.id
        )
        connection_b = models.Connection(
            service="test_service_b",
            status="connected",
            user_id=user_b.id
        )

        permission_a = models.Permission(
            service="google_sheets",
            action="update_sheet",
            allowed=1,
            user_id=user_a.id
        )
        permission_b = models.Permission(
            service="google_sheets",
            action="update_sheet",
            allowed=1,
            user_id=user_b.id
        )

        approval_a = models.Approval(
            service="google_sheets",
            action="update_sheet",
            status="pending",
            user_id=user_a.id
        )
        approval_b = models.Approval(
            service="google_sheets",
            action="update_sheet",
            status="pending",
            user_id=user_b.id
        )

        db.add_all([
            task_a, task_b,
            connection_a, connection_b,
            permission_a, permission_b,
            approval_a, approval_b
        ])
        db.commit()

        db.refresh(task_a)
        db.refresh(task_b)
        db.refresh(connection_a)
        db.refresh(connection_b)
        db.refresh(permission_a)
        db.refresh(permission_b)
        db.refresh(approval_a)
        db.refresh(approval_b)

        activity_a = models.ToolActivity(
            task_id=task_a.id,
            tool="security_test",
            result="A activity",
            user_id=user_a.id
        )
        activity_b = models.ToolActivity(
            task_id=task_b.id,
            tool="security_test",
            result="B activity",
            user_id=user_b.id
        )

        db.add_all([activity_a, activity_b])
        db.commit()

        token_a = create_access_token(user_a.id)
        token_b = create_access_token(user_b.id)

        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        client = TestClient(app)

        print("\n=== SECURITY ISOLATION TEST ===\n")

        # --------------------------------------------------
        # 1. TASK LIST ISOLATION
        # --------------------------------------------------
        response = client.get("/tasks", headers=headers_a)
        assert_status(response, 200, "User A GET /tasks")
        task_ids_a = {item["id"] for item in response.json()}
        assert task_a.id in task_ids_a
        assert task_b.id not in task_ids_a
        print("PASS  User A sees only User A tasks")

        response = client.get("/tasks", headers=headers_b)
        assert_status(response, 200, "User B GET /tasks")
        task_ids_b = {item["id"] for item in response.json()}
        assert task_b.id in task_ids_b
        assert task_a.id not in task_ids_b
        print("PASS  User B sees only User B tasks")

        # --------------------------------------------------
        # 2. CONNECTION ISOLATION
        # --------------------------------------------------
        response = client.get("/connections", headers=headers_a)
        assert_status(response, 200, "User A GET /connections")
        connection_ids_a = {item["id"] for item in response.json()}
        assert connection_a.id in connection_ids_a
        assert connection_b.id not in connection_ids_a
        print("PASS  User A sees only User A connections")

        response = client.get("/connections", headers=headers_b)
        assert_status(response, 200, "User B GET /connections")
        connection_ids_b = {item["id"] for item in response.json()}
        assert connection_b.id in connection_ids_b
        assert connection_a.id not in connection_ids_b
        print("PASS  User B sees only User B connections")

        # --------------------------------------------------
        # 3. PERMISSION ISOLATION
        # --------------------------------------------------
        response = client.get("/permissions", headers=headers_a)
        assert_status(response, 200, "User A GET /permissions")
        permission_ids_a = {item["id"] for item in response.json()}
        assert permission_a.id in permission_ids_a
        assert permission_b.id not in permission_ids_a
        print("PASS  User A sees only User A permissions")

        response = client.get("/permissions", headers=headers_b)
        assert_status(response, 200, "User B GET /permissions")
        permission_ids_b = {item["id"] for item in response.json()}
        assert permission_b.id in permission_ids_b
        assert permission_a.id not in permission_ids_b
        print("PASS  User B sees only User B permissions")

        # --------------------------------------------------
        # 4. APPROVAL ISOLATION
        # --------------------------------------------------
        response = client.get("/approvals", headers=headers_a)
        assert_status(response, 200, "User A GET /approvals")
        approval_ids_a = {item["id"] for item in response.json()}
        assert approval_a.id in approval_ids_a
        assert approval_b.id not in approval_ids_a
        print("PASS  User A sees only User A approvals")

        response = client.get("/approvals", headers=headers_b)
        assert_status(response, 200, "User B GET /approvals")
        approval_ids_b = {item["id"] for item in response.json()}
        assert approval_b.id in approval_ids_b
        assert approval_a.id not in approval_ids_b
        print("PASS  User B sees only User B approvals")

        # --------------------------------------------------
        # 5. CROSS-USER APPROVAL EXECUTION
        # --------------------------------------------------
        response = client.post(
            f"/approvals/{approval_b.id}",
            json={"status": "rejected"},
            headers=headers_a
        )
        assert_status(response, 404, "User A executes User B approval")
        print("PASS  User A cannot execute User B approval")

        response = client.post(
            f"/approvals/{approval_a.id}",
            json={"status": "rejected"},
            headers=headers_b
        )
        assert_status(response, 404, "User B executes User A approval")
        print("PASS  User B cannot execute User A approval")

        # --------------------------------------------------
        # 6. CROSS-USER APPROVAL CREATION
        # --------------------------------------------------
        response = client.post(
            "/approvals",
            json={
                "service": "google_sheets",
                "action": "update_sheet",
                "task_id": task_b.id
            },
            headers=headers_a
        )
        assert_status(response, 404, "User A creates approval for User B task")
        print("PASS  User A cannot create approval for User B task")

        response = client.post(
            "/approvals",
            json={
                "service": "google_sheets",
                "action": "update_sheet",
                "task_id": task_a.id
            },
            headers=headers_b
        )
        assert_status(response, 404, "User B creates approval for User A task")
        print("PASS  User B cannot create approval for User A task")

        # --------------------------------------------------
        # 7. ACTIVITY ISOLATION
        # --------------------------------------------------
        response = client.get("/activity", headers=headers_a)
        assert_status(response, 200, "User A GET /activity")
        activity_ids_a = {item["id"] for item in response.json()}
        assert activity_a.id in activity_ids_a
        assert activity_b.id not in activity_ids_a
        print("PASS  User A sees only User A activity")

        response = client.get("/activity", headers=headers_b)
        assert_status(response, 200, "User B GET /activity")
        activity_ids_b = {item["id"] for item in response.json()}
        assert activity_b.id in activity_ids_b
        assert activity_a.id not in activity_ids_b
        print("PASS  User B sees only User B activity")

        # --------------------------------------------------
        # 8. CROSS-USER ACTIVITY CREATION
        # --------------------------------------------------
        response = client.post(
            "/activity",
            json={
                "task_id": task_b.id,
                "tool": "security_test",
                "result": "cross-user attempt"
            },
            headers=headers_a
        )
        assert_status(response, 404, "User A creates activity on User B task")
        print("PASS  User A cannot create activity for User B task")

        print("\n================================")
        print("ALL USER-ISOLATION TESTS PASSED")
        print("================================\n")

    finally:
        # Remove every test record and test user.
        if user_a is not None or user_b is not None:
            user_ids = [
                u.id for u in (user_a, user_b)
                if u is not None
            ]

            # All non-User tables use user_id.
            for model in [
                models.ToolActivity,
                models.Approval,
                models.Permission,
                models.Connection,
                models.Task,
            ]:
                db.query(model).filter(
                    model.user_id.in_(user_ids)
                ).delete(synchronize_session=False)

            # User itself uses id, not user_id.
            db.query(models.User).filter(
                models.User.id.in_(user_ids)
            ).delete(synchronize_session=False)

            db.commit()

        db.close()


if __name__ == "__main__":
    main()
