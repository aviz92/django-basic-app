# Django Basic App
A production-ready Django REST Framework template with enterprise-grade CRUD utilities, versioned data management, data status workflow, and CI integration out of the box.

---

## 🚀 Features

### Enterprise-Grade CRUD Utilities (`CRUDUtils`)

**Advanced Filtering**
- Wildcard search patterns for text fields (`name=test*`, `name=*test*`)
- Comparison operators for number fields (`age=>=18`, `age=10-20`)
- ForeignKey lookups (`first_app__name=test*`)
- Nested ForeignKey support (`first_app__category__name=prod*`)
- Automatic validation - invalid fields return empty results

**Pagination**
- Built-in pagination with customizable page size
- Default: 20 items per page, max: 100

**Bulk Operations**
- Bulk create, update, and delete operations
- Partial success handling with detailed error reporting

**Performance Optimizations**
- `select_related` and `prefetch_related` support
- Queryset customization hooks
- Efficient database queries

**Error Handling**
- Comprehensive validation
- Database constraint violation handling
- Detailed error messages

**Sorting & Ordering**
- Flexible field-based sorting
- Multiple field ordering support
- Default ordering fallbacks

---

### Versioned Data Management (`apps/core`)

Every model that inherits from `VersionedModel` participates in full version control — automatically.

**Core concept:** every row in every table has `release = FK(Release)`. That's the entire versioning mechanism.

```python
class MyModel(VersionedModel):
    name = models.CharField(max_length=255)
    # Done. Auto-discovered, versioned, immutable when locked.
```

**What you get automatically:**
- `release` FK added to the table
- `status` field (`draft` / `future` / `approved`)
- `objects.for_release(release)` and `objects.approved(release)` manager methods
- Included in `create_release` copy — with topological FK sort
- Lock enforcement on `save()` and `delete()`

#### Release Lifecycle

```
create_release → architects edit → approve_release → lock_release
                                         ↑
                              (CI runs tests here)
```

#### Data Status Workflow

```
DRAFT ⇄ FUTURE → APPROVED  (one-way, CI only)
```

| Status | Who | Meaning |
|--------|-----|---------|
| `DRAFT` | Architects | Being worked on, not ready |
| `FUTURE` | Architects | Planned for a future release |
| `APPROVED` | CI only | Stable — what tests run against |

CI always queries `objects.approved(release)`. DRAFT and FUTURE rows are invisible to CI, so live edits never break tests.

---

## 🏃 Quick Start

### Environment Setup

Create a `.env` file in the project root:

```env
SECRET_DJANGO_KEY=your-secret-key-here
DJANGO_DEBUG=True
```

### 1. Install dependencies

```bash
uv sync
```

### 2. Run migrations

```bash
uv run python manage.py migrate
```

### 3. Create superuser

```bash
uv run python manage.py createsuperuser
```

### 4. Create the first release

The first release must be created manually via the shell (subsequent releases use the CI command):

```bash
uv run python manage.py shell
>>> from django_versioned_models.models import Release
>>> from django.utils import timezone
>>> Release.objects.create(version="v1.0.0", is_locked=True, locked_at=timezone.now())
>>> exit()
```

### 5. Start development server

```bash
uv run python manage.py runserver
```

The API is available at `http://127.0.0.1:8000`

---

## 🔧 Management Commands

All versioning commands live in `apps/core/management/commands/`.

### Release Management

**Create a new release** (branched from an existing locked one):
```bash
uv run python manage.py create_release --release-version v1.1.0 --based-on v1.0.0
```

**Lock a release** (immutable after this — no edits, no deletes):
```bash
uv run python manage.py lock_release --release-version v1.1.0
```

**Unlock a release** (only before deployment):
```bash
uv run python manage.py unlock_release --release-version v1.1.0
```

**Approve all DRAFT rows** (CI runs this — FUTURE rows are left untouched):
```bash
uv run python manage.py approve_release --release-version v1.1.0
```

**Deprecate a release** (soft delete — data preserved, hidden from API by default):
```bash
uv run python manage.py deprecate_release --release-version v1.0.0

# Undo if needed
uv run python manage.py deprecate_release --release-version v1.0.0 --undo
```

### Typical CI Flow

```
# New release
create_release --release-version v1.1.0 --based-on v1.0.0

# Architects edit data in v1.1.0 (status=DRAFT by default)

# CI approves stable rows
approve_release --release-version v1.1.0

# CI runs tests against approved data
pytest --release-version v1.1.0

# Ship it
lock_release --release-version v1.1.0

# Bug found after deployment? Never modify a locked release — patch instead
create_release --release-version v1.1.1 --based-on v1.1.0
```

---

## 📡 API

### Versioned Endpoints

All versioned endpoints accept a `version` query parameter:

```
GET /api/first_app/?version=v1.1.0              # all statuses
GET /api/first_app/?version=v1.1.0&status=approved
GET /api/first_app/?version=v1.1.0&status=draft
```

### Release Endpoints

```
GET  /api/releases/                          # active releases (deprecated hidden)
GET  /api/releases/?include_deprecated=true  # include deprecated
GET  /api/releases/<id>/
POST /api/releases/<id>/lock/                # lock a release (admin only)
```

### Advanced Filtering Examples

**Text Field Wildcards:**
```
GET /api/items/?name=test*       # starts with
GET /api/items/?name=*test       # ends with
GET /api/items/?name=*test*      # contains
```

**Number Field Comparisons:**
```
GET /api/items/?age=>=18         # greater than or equal
GET /api/items/?age=<=65         # less than or equal
GET /api/items/?age=18-30        # range (inclusive)
```

**ForeignKey Lookups:**
```
GET /api/items/?category__name=prod*
GET /api/items/?category__parent__name=test*
```

**Combined:**
```
GET /api/items/?name=test*&age=>=18&ordering=-created_at&page=1&page_size=20
```

---

## 🧪 Fetching Data for Tests

Use [`pyrest-model-client`](https://github.com/aviz92/pyrest-model-client) to fetch versioned data from the API in your test projects:

```bash
python scripts/fetch_release_data.py --release-version v1.1.0
python scripts/fetch_release_data.py --release-version v1.1.0 --status approved
python scripts/fetch_release_data.py --release-version v1.1.0 --base-url http://prod-server:8000
```

Define your models in the script:

```python
from pyrest_model_client.base import BaseAPIModel

class FirstApp(BaseAPIModel):
    name: str
    description: str | None = None
    status: str | None = None
    resource_path: str = "first_app"

MODELS = [FirstApp, ...]
```

The script sends `?version=v1.1.0&status=approved` on every request automatically, handles pagination, and returns typed model instances.

---

## 🏗️ Project Structure

```
django_basic_app/
├── apps/
│   ├── core/                        # Versioning engine
│   │   ├── models.py                # Release model
│   │   ├── mixins.py                # VersionedModel + DataStatus
│   │   ├── services.py              # create_release, lock_release (auto-discovery)
│   │   ├── views.py                 # ReleaseViewSet, ReleaseFilterMixin
│   │   └── management/commands/
│   │       ├── create_release.py
│   │       ├── lock_release.py
│   │       ├── unlock_release.py
│   │       ├── approve_release.py
│   │       └── deprecate_release.py
│   └── first_app/                   # Example versioned app
│       ├── models.py                # class FirstApp(VersionedModel)
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
│   └── second_app/                  # Example versioned app
│       ├── models.py                # class SecondAppApp(VersionedModel)
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
├── scripts/
│   └── fetch_release_data.py        # pyrest-model-client integration
└── manage.py
```

---

## 🤝 Contributing

Fork the repo, create a new branch, and submit a pull request. Additions that promote clean, maintainable development are welcome.

---

## 🙏 Thanks

Thanks for exploring this repository! Happy coding.
