# Django Commands
This document provides a list of common Django management commands that can be used to perform various tasks in a Django project.

## Common Django Commands

### App Management
- `django-admin startproject <project_name>`: Creates a new Django project with the specified name.
- `uv run python manage.py startapp <app_name>`: Creates a new Django app with the specified name.
- `uv run python manage.py runserver`: Starts the development server.

### Database and Migrations
- `uv run python manage.py makemigrations`: Creates new migrations based on the changes detected in models.
- `uv run python manage.py migrate`: Applies the migrations to the database.
- `uv run python manage.py createsuperuser`: Creates a new superuser for the admin interface.

### Data Management
- `uv run python manage.py flush`: Resets the database by removing all data and reapplying migrations.
- `uv run python manage.py loaddata <fixture_name>`: Loads data from a fixture file into the database.
- `uv run python manage.py dumpdata <app_name>.<model_name>`: Exports data from the specified model into a JSON format.

### Utility Commands
- `python manage.py check`: Checks the entire Django project for potential issues without making database migrations.
- `uv run python manage.py dbshell`: Opens the database shell for the configured database.
- `uv run python manage.py diffsettings`: Displays the differences between the current settings and Django's default settings.
- `uv run python manage.py inspectdb`: Generates model code by introspecting the database tables.
