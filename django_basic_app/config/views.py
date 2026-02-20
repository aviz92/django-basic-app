from pathlib import Path

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import get_resolver


def _read_markdown_file(file_path: Path) -> dict:
    """Read and parse Markdown file, return structured content."""

    result = {
        "title": "",
        "description": [],
    }

    if not file_path.exists():
        return result

    md_content = file_path.read_text()
    lines = md_content.split("\n")

    for line in lines:
        if not (line := line.strip()):
            continue

        if line.startswith("# ") and not result["title"]:
            result["title"] = line[2:].strip()
        elif line and not line.startswith("#"):
            result["description"].append(line)
    return result


def index(request: HttpRequest) -> HttpResponse:
    """Introspects project URLs and provides a developer dashboard."""

    readme_url: str = "https://github.com/aviz92/django-basic-app#readme"

    resolver = get_resolver()
    links = []
    for pattern in resolver.url_patterns:
        try:
            route: str = str(pattern.pattern).replace("^", "").replace("$", "")
            if route and route not in ["admin/jsi18n/"]:
                display_name: str = route.replace("/", "").replace("_", " ").title()
                links.append({"route": f"/{route}", "name": display_name or "Home"})
        except AttributeError:
            continue

    # Read about content from markdown file
    project_root = Path(settings.BASE_DIR).parent
    about_md_path = project_root / "HOMEPAGE_ABOUT.md"
    about_data = _read_markdown_file(about_md_path)

    context = {"links": links, "readme_url": readme_url, "about_data": about_data}
    return render(request, "index.html", context)
