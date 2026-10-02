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

    normalized_action = action.lower().strip()

    permission = (
        db.query(Permission)
        .filter(
            Permission.user_id == user_id,
            Permission.allowed == 1
        )
        .all()
    )

    for item in permission:
        stored_service = service_aliases.get(
            item.service.lower(),
            item.service.lower()
        )

        stored_action = item.action.lower().strip()

        if (
            stored_service == normalized_service
            and stored_action == normalized_action
        ):
            return True

    return False