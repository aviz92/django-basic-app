from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import get_resolver


def index(request: HttpRequest) -> HttpResponse:
    """ Introspects project URLs and provides a developer dashboard. """

    readme_url: str = "https://github.com/aviz92/django-basic-app#readme"

    resolver = get_resolver()
    links = []
    for pattern in resolver.url_patterns:
        try:
            route: str = str(pattern.pattern).replace('^', '').replace('$', '')
            if route and route not in ['admin/jsi18n/']:
                display_name: str = route.replace('/', '').replace('_', ' ').title()
                links.append(
                    {
                        'route': f"/{route}",
                        'name': display_name or "Home"
                    }
                )
        except AttributeError:
            continue
    context = {
        'links': links,
        'readme_url': readme_url
    }
    return render(request, 'index.html', context)
