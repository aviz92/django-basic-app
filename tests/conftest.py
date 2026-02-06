"""Shared pytest fixtures for all tests."""

import os
import sys
from pathlib import Path

# Add django_basic_app to Python path for pytest
# This allows imports like 'core.settings' to work
project_root = Path(__file__).resolve().parent.parent
django_basic_app_path = project_root / 'django_basic_app'
if str(django_basic_app_path) not in sys.path:
    sys.path.insert(0, str(django_basic_app_path))

# Set Django settings module for pytest-django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
