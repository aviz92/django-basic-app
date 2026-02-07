from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import get_resolver


def index(request: HttpRequest) -> HttpResponse:
    links = []
    resolver = get_resolver()
    for pattern in resolver.url_patterns:
        route = str(pattern.pattern).replace('^', '').replace('$', '')
        if route and route not in ['admin/jsi18n/']:
            display_name = route.replace('/', '').replace('_', ' ').title()
            links.append(
                {
                    'route': f"/{route}",
                    'name': display_name or "Home"
                }
            )
    return render(request, 'index.html', {'links': links})
