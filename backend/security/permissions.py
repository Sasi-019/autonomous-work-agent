from models import Permission


def check_permission(db, user_id, service, action):
    service_aliases = {
        "sheets": "google_sheets",
        "google": "google_sheets",
        "google_sheets": "google_sheets",
        "gmail": "gmail",
        "browser": "browser",
    }

    normalized_service = service_aliases.get(
        service.lower(),
        service.lower()
    )

    permission = (
        db.query(Permission)
        .filter(
            Permission.user_id == user_id,
            Permission.action == action,
            Permission.allowed == 1
        )
        .all()
    )

    for item in permission:
        stored_service = service_aliases.get(
            item.service.lower(),
            item.service.lower()
        )

        if stored_service == normalized_service:
            return True

    return False