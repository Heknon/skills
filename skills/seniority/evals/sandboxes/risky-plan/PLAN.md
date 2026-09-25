# Rename users.email to users.email_address

1. Change the model in `app/models.py` to `email_address`.
2. Run `scripts/migrate.sh --env prod` to rename the column in production.
3. Update every query in the code to use `email_address`.
4. Deploy.
