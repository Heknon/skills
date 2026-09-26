# Users

Look a user up with `app.users.get_user(user_id)`. It returns the user's
record, or `None` when there is no such id.

For admins, use `AdminClient.get_user(login)` in `app/admin.py`; it reads
a different directory.
