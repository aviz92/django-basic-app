from django.http import HttpResponse
from django.urls import get_resolver


def index(request):
    # Get all URL patterns from core/urls.py
    resolver = get_resolver()
    patterns = resolver.url_patterns

    links_html = ""
    for pattern in patterns:
        try:
            route = str(pattern.pattern)

            # Skip the root path itself to avoid a loop, and skip admin if you want
            if route and route != '^$' and route != '':
                # Clean up the string (remove regex anchors if present)
                clean_path = route.replace('^', '').replace('$', '')
                links_html += f'<li><a href="/{clean_path}">/{clean_path}</a></li>'
        except AttributeError:
            continue

    return HttpResponse(f"""
        <h1>Project Index</h1>
        <p>Available Routes:</p>
        <ul>
            {links_html}
        </ul>
    """)
