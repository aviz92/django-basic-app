![PyPI version](https://img.shields.io/pypi/v/django-basic-app)
![Python](https://img.shields.io/badge/python->=3.12-blue)
![Development Status](https://img.shields.io/badge/status-stable-green)
![Maintenance](https://img.shields.io/maintenance/yes/2026)
![PyPI](https://img.shields.io/pypi/dm/django-basic-app)
![License](https://img.shields.io/pypi/l/django-basic-app)

---

# Django Basic App

A production-ready Django REST Framework template with enterprise-grade CRUD utilities, featuring advanced filtering, pagination, and bulk operations out of the box.

## 🚀 Features

### Enterprise-Grade CRUD Utilities (`CRUDUtils`)

- **🔍 Advanced Filtering**
  - Wildcard search patterns for text fields (`name=test*`, `name=*test*`)
  - Comparison operators for number fields (`age=>=18`, `age=10-20`)
  - ForeignKey lookups (`first_app__name=test*`)
  - Nested ForeignKey support (`first_app__category__name=prod*`)
  - Automatic validation - invalid fields return empty results

- **📄 Pagination**
  - Built-in pagination with customizable page size
  - Default: 20 items per page, max: 100

- **🔄 Bulk Operations**
  - Bulk create, update, and delete operations
  - Partial success handling with detailed error reporting

- **⚡ Performance Optimizations**
  - `select_related` and `prefetch_related` support
  - Queryset customization hooks
  - Efficient database queries

- **🛡️ Error Handling**
  - Comprehensive validation
  - Database constraint violation handling
  - Detailed error messages

- **📊 Sorting & Ordering**
  - Flexible field-based sorting
  - Multiple field ordering support
  - Default ordering fallbacks

---

### Environment Setup
Create a `.env` file in the project root:
```bash
# Required
SECRET_DJANGO_KEY=your-secret-key-here

# Optional
DJANGO_DEBUG=True
```

---

## 🏃 Quick Start

### 1. Run Migrations
```bash
uv run python manage.py migrate
```

### 2. Create Superuser
```bash
uv run python manage.py createsuperuser
```

### 3. Start Development Server
```bash
uv run python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000`

---

### 4. Get Authentication Token
Visit the Django admin panel at `http://127.0.0.1:8000/admin/` and create a token for your user, or use the admin interface to generate tokens.

---

### Advanced Filtering Examples
**Text Field Wildcards:**
```bash
# Starts with
GET /api/items/?name=test*

# Ends with
GET /api/items/?name=*test

# Contains
GET /api/items/?name=*test*

# Middle wildcard
GET /api/items/?name=t*t
```

**Number Field Comparisons:**
```bash
# Exact match
GET /api/items/?age=25

# Greater than or equal
GET /api/items/?age=>=18

# Less than or equal
GET /api/items/?age=<=65

# Range (inclusive)
GET /api/items/?age=18-30
```

**ForeignKey Lookups:**
```bash
# Filter by related text field
GET /api/items/?category__name=prod*

# Filter by related number field
GET /api/items/?category__age=>=18

# Nested ForeignKey
GET /api/items/?category__parent__name=test*
```

**Combined Filters:**
```bash
GET /api/items/?name=test*&age=>=18&category__name=prod*&ordering=-created_at&page=1&page_size=20
```

---

## 🤝 Contributing
If you have a helpful tool, pattern, or improvement to suggest:
Fork the repo <br>
Create a new branch <br>
Submit a pull request <br>
I welcome additions that promote clean, productive, and maintainable development. <br>

---

## 🙏 Thanks
Thanks for exploring this repository! <br>
Happy coding! <br>
