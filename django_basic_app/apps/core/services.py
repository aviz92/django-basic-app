"""
apps/core/services.py

The single place that knows how to create a new release from an existing one.
CI calls create_release() — this handles copying all versioned data automatically.

Models are discovered automatically — no manual registration needed.
Any model that inherits from VersionedModel is included in the copy,
ordered automatically by FK dependencies (topological sort).
"""
from django.db import transaction
from django.apps import apps


# ── Auto-discovery ────────────────────────────────────────────────────────────

def get_versioned_models():
    """
    Find every model that inherits from VersionedModel — automatically.
    No manual list to maintain. Adding a new model that inherits from
    VersionedModel is enough — it will be included in the next release copy.
    """
    from apps.core.mixins import VersionedModel
    return [
        model for model in apps.get_models()
        if issubclass(model, VersionedModel) and model is not VersionedModel
    ]


def get_versioned_models_ordered():
    """
    Returns versioned models sorted by FK dependencies (parents before children).

    This is needed because copying a PriceEntry before its Product exists
    in the new release would cause an FK constraint error.

    Uses Kahn's topological sort algorithm on the FK dependency graph.
    """
    models = get_versioned_models()
    model_set = set(models)

    # Build dependency graph: model -> set of models it depends on
    graph = {m: set() for m in models}
    for model in models:
        for field in model._meta.get_fields():
            if not field.is_relation or not field.many_to_one:
                continue
            related = field.related_model
            if related in model_set and related is not model:
                graph[model].add(related)

    # Kahn's algorithm
    ordered = []
    no_deps = [m for m, deps in graph.items() if not deps]

    while no_deps:
        m = no_deps.pop()
        ordered.append(m)
        for other, deps in graph.items():
            if m in deps:
                deps.discard(m)
                if not deps and other not in ordered:
                    no_deps.append(other)

    # Catch circular dependencies (shouldn't happen in a well-designed schema)
    if len(ordered) != len(models):
        remaining = [m.__name__ for m in models if m not in ordered]
        raise RuntimeError(
            f'Circular FK dependency detected among versioned models: {remaining}'
        )

    return ordered


@transaction.atomic
def create_release(version: str, based_on_version: str, description: str = '', user=None):
    """
    Called by CI when a new release (or patch) is needed.

    Steps:
      1. Validate that based_on_version exists and is locked
      2. Create the new Release record
      3. Copy ALL versioned rows from based_on -> new release (auto-discovered)
      4. Return the new Release (ready for architects to edit)
    """
    from apps.core.models import Release

    try:
        source_release = Release.objects.get(version=based_on_version)
    except Release.DoesNotExist:
        raise ValueError(f'Source release "{based_on_version}" does not exist.')

    if not source_release.is_locked:
        raise ValueError(
            f'Source release "{based_on_version}" is not locked yet. '
            f'You can only branch from a locked (released) version.'
        )

    new_release = Release.objects.create(
        version=version,
        description=description,
        based_on=source_release,
        is_locked=False,
        created_by=user,
    )

    # Copy all versioned rows -- auto-discovered and topologically sorted
    id_mapping = {}

    for model in get_versioned_models_ordered():
        _copy_model_rows(model, source_release, new_release, id_mapping)

    return new_release


def _copy_model_rows(model, source_release, new_release, id_mapping):
    """
    Copies all rows of a model from source_release to new_release.
    Handles FK remapping so relations point to the new copies, not the originals.
    """
    source_rows = model.objects.for_release(source_release).select_related('release')
    model_key = f'{model._meta.app_label}.{model.__name__}'
    id_mapping[model_key] = {}

    for row in source_rows:
        old_id = row.pk
        field_values = {}

        for field in model._meta.get_fields():
            if not hasattr(field, 'column'):
                continue
            if field.primary_key:
                continue
            if field.name == 'release':
                continue

            if field.is_relation and field.many_to_one:
                related_model = field.related_model
                related_key = f'{related_model._meta.app_label}.{related_model.__name__}'
                if related_key in id_mapping:
                    old_fk_id = getattr(row, f'{field.name}_id')
                    if old_fk_id is not None:
                        new_related = id_mapping[related_key].get(old_fk_id)
                        field_values[f'{field.name}_id'] = (
                            new_related.pk if new_related else old_fk_id
                        )
                    else:
                        field_values[f'{field.name}_id'] = None
                    continue

            field_values[field.name] = getattr(row, field.attname)

        new_row = model(**field_values, release=new_release)
        model.objects.bulk_create([new_row])  # bypass save() lock check intentionally
        new_row = model.objects.for_release(new_release).order_by('-pk').first()
        id_mapping[model_key][old_id] = new_row


@transaction.atomic
def lock_release(version: str):
    """
    Called by CI when a version is officially released.
    After this, no edits are possible -- patches must create a new version.
    """
    from apps.core.models import Release
    try:
        release = Release.objects.get(version=version)
    except Release.DoesNotExist:
        raise ValueError(f'Release "{version}" does not exist.')

    if release.is_locked:
        raise ValueError(f'Release "{version}" is already locked.')

    release.lock()
    return release
