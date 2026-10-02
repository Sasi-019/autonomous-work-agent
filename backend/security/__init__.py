from models import Permission


def check_permission(
    db,
    user_id,
    service,
    action
):
    permission = db.query(Permission).filter(
        Permission.user_id == user_id,
        Permission.service == service,
        Permission.action == action,
        Permission.allowed == 1
    ).first()

    return permission is not None