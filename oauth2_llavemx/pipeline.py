from django.contrib.auth.models import User

def auto_create_user_for_llavemx(strategy, backend, details, user=None, *args, **kwargs):
    """
    Automatically create users coming from Llave MX.
    Prevents redirection to /register.
    """

    # Only apply to Llave MX provider
    if backend.name != "llavemx":
        return

    # If user already exists, nothing to do
    if user:
        return

    username = details.get("username")
    email = details.get("email") or f"{username}@llavemx.temp"
    first_name = details.get("first_name", "")
    last_name = details.get("last_name", "")

    # If user exists in DB already, reuse it
    existing = User.objects.filter(username=username).first()
    if existing:
        return {
            "user": existing,
            "is_new": False,
            "details": details,
        }

    # Create NEW user
    new_user = User.objects.create(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_active=True,
    )

    return {
        "user": new_user,
        "is_new": False,   # <-- CRÍTICO para NO mandar a /register
        "details": details,
    }
