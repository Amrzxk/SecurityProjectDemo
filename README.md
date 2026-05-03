# Flask Auth + RBAC Demo

Minimal Flask project demonstrating secure authentication (Argon2), role-based access control (RBAC), optional **AES-CBC** field encryption at rest, and Flask-Login sessions.

## Quick start (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\seed.py
python run.py
```

Browse `instance/app.db` in a browser (optional dev tool: [sqlite-web](https://github.com/coleifer/sqlite-web)):

```powershell
pip install -r requirements-dev.txt
python scripts\view_db.py
```

Then open `http://127.0.0.1:8080` (defaults to **read-only**; use `--writable` only when the Flask server is stopped).

**Default seeded admin:** `admin` / `adminpass`

**Run tests:** `pip install -r requirements.txt` then `pytest -q`

---

## Security measures (overview)

| Area | Implementation | Where |
|------|------------------|--------|
| Password storage | Argon2 hashing (salt + params embedded in hash string) | [`app/security.py`](app/security.py) |
| Registration | Strength rules before hash | [`app/auth/routes.py`](app/auth/routes.py) |
| Authentication | Flask-Login sessions; signed cookies need `SECRET_KEY` | [`config.py`](config.py), [`app/__init__.py`](app/__init__.py) |
| Account control | `active` flag; suspended users cannot log in | [`app/models.py`](app/models.py), [`app/auth/routes.py`](app/auth/routes.py) |
| Authorization | RBAC: users ↔ roles ↔ permissions | [`app/models.py`](app/models.py) |
| Route enforcement | `@roles_required`, `@permissions_required`, `@dynamic_permission` | [`app/auth/decorators.py`](app/auth/decorators.py) |
| Admin UI | Only `admin` role; unauthenticated users redirected to login | [`app/admin/routes.py`](app/admin/routes.py) |
| Sensitive data at rest | AES-256-CBC, PKCS7, random IV per encrypt | [`app/field_crypto.py`](app/field_crypto.py), [`config.py`](config.py) |
| Template safety | Anonymous user implements `has_role` / `has_permission` | [`app/models.py`](app/models.py) |
| Rate limiting | Flask-Limiter wired; login limits are **commented** (optional) | [`app/extensions.py`](app/extensions.py), [`app/auth/routes.py`](app/auth/routes.py) |

---

### 1. Password hashing (Argon2)

Passwords are never stored in plaintext. Argon2 derives a **salted, memory-hard** hash; each stored string encodes algorithm parameters and salt (PHC format).

**[`app/security.py`](app/security.py)**

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash

ph = PasswordHasher()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    try:
        return ph.verify(stored_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False
```

**[`app/models.py`](app/models.py)** (user model wires hashing)

```python
    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        return verify_password(self.password_hash, password)
```

---

### 2. Registration password policy

New accounts must meet minimum length and complexity (lowercase, uppercase, digit, symbol) before hashing.

**[`app/auth/routes.py`](app/auth/routes.py)**

```python
def is_strong_password(password: str):
    if not password or len(password) < 8:
        return False, 'Password must be at least 8 characters long.'
    if not re.search(r'[a-z]', password):
        return False, 'Password must include a lowercase letter.'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must include an uppercase letter.'
    if not re.search(r'\d', password):
        return False, 'Password must include a digit.'
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, 'Password must include a symbol (e.g. !@#$%).'
    return True, None
```

Duplicate usernames are rejected; new users receive the default `user` role when that role exists.

---

### 3. Login, generic errors, and suspension

- **Suspension:** `active` is false → login blocked with an explicit message (no password check).
- **Invalid credentials:** Same user-facing message whether the user exists or not, to avoid username enumeration.

**[`app/auth/routes.py`](app/auth/routes.py)**

```python
        if user:
            if not user.is_active:
                flash('Account suspended. Contact the administrator.', 'danger')
                return render_template('login.html')
            if user.check_password(password):
                login_user(user)
                flash('Logged in successfully', 'success')
                return redirect(url_for('main.dashboard'))
        flash('Invalid credentials', 'danger')
```

**[`app/auth/routes.py`](app/auth/routes.py)** — logout requires an authenticated session (`@login_required`).

---

### 4. Sessions and application secrets

Flask signs session data with **`SECRET_KEY`**. Flask-Login stores the authenticated user id in that session; the full user is reloaded each request via **`user_loader`**.

**[`config.py`](config.py)**

```python
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-me'
```

**[`app/__init__.py`](app/__init__.py)**

```python
    login_manager.init_app(app)
    from .models import AnonymousUser
    login_manager.anonymous_user = AnonymousUser
    login_manager.login_view = 'auth.login'
```

**[`app/models.py`](app/models.py)** — load user by id for the session

```python
@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None
```

For production, set a strong random **`SECRET_KEY`** in the environment.

---

### 5. RBAC and permission resolution

Users have many **roles**; roles have many **permissions**. Checks are done in Python (and mirrored in templates via `current_user`).

**[`app/models.py`](app/models.py)** — association tables and checks

```python
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
)
```

```python
    def has_role(self, role_name):
        return any(r.name == role_name for r in self.roles)

    def has_permission(self, permission_name):
        for role in self.roles:
            for p in role.permissions:
                if p.name == permission_name:
                    return True
        return False

    def has_mapped_permission(self, resource, action):
        name = resolve_mapped_permission_name(resource, action)
        return bool(name and self.has_permission(name))
```

Inventory actions can map permission **names** via `Setting` rows (admin UI); otherwise conventional names like `inventory.view` are used:

```python
def resolve_mapped_permission_name(resource: str, action: str) -> str:
    key = f"{resource}.permission.{action}"
    row = Setting.query.filter_by(key=key).first()
    val = row.value.strip() if row and row.value else ''
    return val if val else _MAPPED_PERM_FALLBACKS.get((resource, action), '')
```

**[`app/models.py`](app/models.py)** — unauthenticated requests use a safe anonymous user

```python
class AnonymousUser(AnonymousUserMixin):
    def has_role(self, role_name):
        return False
    def has_permission(self, permission_name):
        return False
    def has_mapped_permission(self, resource, action):
        return False
```

---

### 6. Authorization decorators (routes)

**[`app/auth/decorators.py`](app/auth/decorators.py)**

```python
def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            for role in roles:
                if current_user.has_role(role):
                    return f(*args, **kwargs)
            abort(403)
        return wrapped
    return decorator
```

```python
def dynamic_permission(resource, action):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.has_mapped_permission(resource, action):
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator
```

Inventory routes use `@dynamic_permission('inventory', ...)` so **view / add / edit / delete** enforce the mapped permission names consistently with the templates.

---

### 7. Admin area protection

The admin blueprint denies access unless the user is logged in **and** has the **`admin`** role.

**[`app/admin/routes.py`](app/admin/routes.py)**

```python
@admin_bp.before_request
def require_admin():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login', next=request.path))
    if not current_user.has_role('admin'):
        abort(403)
```

Admins manage roles, permissions, user-role assignment, suspension, and inventory permission mappings via forms on the admin dashboard.

---

### 8. Field encryption (AES-CBC + IV)

Optional **inventory “sensitive note”** is stored encrypted in **`sensitive_note_cipher`**. Each encryption uses a **fresh 16-byte IV**, AES-256 in **CBC** mode with **PKCS7** padding; the stored value is **URL-safe base64( IV ‖ ciphertext )**.

Keys are configured separately from the session secret (preferred in production):

**[`config.py`](config.py)**

```python
    FIELD_ENCRYPTION_KEY = os.environ.get('FIELD_ENCRYPTION_KEY') or hashlib.sha256(
        ((os.environ.get('SECRET_KEY') or 'dev-secret-change-me') + ':field_encryption').encode('utf-8')
    ).hexdigest()
```

**[`app/field_crypto.py`](app/field_crypto.py)** — core encrypt/decrypt

```python
def encrypt_field(plaintext: str, *, key: bytes) -> str:
    if plaintext is None or plaintext == '':
        return ''
    raw = plaintext.encode('utf-8')
    iv = os.urandom(_BLOCK)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    padder = sym_padding.PKCS7(algorithms.AES.block_size).padder()
    padded = padder.update(raw) + padder.finalize()
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.urlsafe_b64encode(iv + ciphertext).decode('ascii')
```

Passwords remain **hashed only** with Argon2; this layer is **reversible encryption** for a specific DB field only.

---

### 9. Rate limiting (optional)

**[`app/extensions.py`](app/extensions.py)** registers Flask-Limiter. Login route decorators for per-IP/per-user limits exist in **`app/auth/routes.py`** as **comments** (`# @limiter.limit(...)`). Uncomment and tune for brute-force mitigation in deployment.

---

## Project layout

- `app/` — application factory, extensions, models, security, field crypto
- `app/auth` — register, login, logout
- `app/admin` — RBAC administration (admin role only)
- `app/inventory` — permission-mapped CRUD + encrypted sensitive note
- `app/main` — example routes
- `scripts/seed.py` — initial roles, permissions, admin user, sample items
- `tests/` — pytest (auth, RBAC, inventory mapping, field crypto)

---

## Inventory demo (RBAC)

After `python scripts\seed.py`, roles and inventory permissions exist and sample items are created.

1. Register a user at `/register`.
2. Log in as `admin` / `adminpass` and open `/admin/`.
3. Assign **`viewer`** for read-only inventory; **`editor`** (or **`admin`**) for add/edit; granular delete can use a custom role with `inventory.delete` only.
4. Visit `/inventory/` and confirm buttons match assigned permissions.

To verify **encryption** in the DB UI: save a sensitive note on an item and inspect table **`item`**, column **`sensitive_note_cipher`** — it should contain opaque base64, not plaintext.
