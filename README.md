# Flask Auth + RBAC Demo

Minimal Flask project demonstrating secure authentication (Argon2) and role-based access control (RBAC) using SQLite.

Quick start (PowerShell):

```powershell
# create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# install dependencies
pip install -r requirements.txt

# seed the database (creates admin/adminpass and roles)
python scripts\seed.py

# run the dev server
python run.py
```

Browse `instance/app.db` in a browser (optional dev tool: [sqlite-web](https://github.com/coleifer/sqlite-web)):

```powershell
pip install -r requirements-dev.txt
python scripts\view_db.py
```

Then open `http://127.0.0.1:8080` (defaults to **read-only**; use `--writable` only when the Flask server is stopped).

Default admin credentials created by the seed script:

- username: `admin`
- password: `adminpass`

Run tests:

```powershell
pip install -r requirements.txt
pytest -q
```

Files added:

- `app/` - application package (factory, extensions, models, security)
- `app/auth` - authentication blueprint (register/login/logout)
- `app/admin` - admin blueprint (protected by `admin` role)
- `app/main` - public and protected example routes
- `scripts/seed.py` - initialize DB and create an admin user
- `tests/` - pytest tests for auth and RBAC

Inventory demo

- After running `python scripts\seed.py` the seed creates roles and permissions for the inventory demo (`inventory.view`, `inventory.edit`) and two sample items.
- To test RBAC:
	1. Register a new user via the web UI (`/register`).
	2. Login as the seeded admin (`admin` / `adminpass`) and open the Admin panel (`/admin/`).
	3. Assign the `viewer` role to a user to allow viewing the inventory (no edit buttons).
	4. Assign the `editor` role to allow creating and editing items.
 5. Visit `/inventory/` while logged in as the user to confirm the UI reflects permissions (Add/Edit buttons visible only for editors/admins).

