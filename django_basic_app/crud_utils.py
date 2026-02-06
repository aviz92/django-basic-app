"""Enterprise-grade CRUD utility class for Django REST Framework.

Provides comprehensive CRUD operations with:
- Pagination support
- Generic wildcard filtering (no FilterSet needed)
- Ordering and sorting
- Queryset customization hooks
- Performance optimizations (select_related/prefetch_related)
- Bulk operations
- Comprehensive error handling
"""

import re
from typing import Any, Callable, Optional, Type

from django.core.exceptions import FieldDoesNotExist, ValidationError as DjangoValidationError
from django.db import IntegrityError, models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from custom_python_logger import build_logger

logger = build_logger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination class for list endpoints."""

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CRUDUtils:
    """Enterprise-grade utility class providing comprehensive CRUD operations for Django REST Framework views."""

    @staticmethod
    def _get_instance_by_pk(
        model_class: Type[models.Model],
        pk: Any,
        select_related: Optional[list[str]] = None,
        prefetch_related: Optional[list[str]] = None,
    ) -> Optional[models.Model]:
        """Get a model instance by primary key with optional performance optimizations."""

        try:
            queryset = model_class.objects.all()
            if select_related:
                queryset = queryset.select_related(*select_related)
            if prefetch_related:
                queryset = queryset.prefetch_related(*prefetch_related)
            return queryset.get(pk=pk)
        except model_class.DoesNotExist:
            logger.warning(f"{model_class.__name__} with pk={pk} not found")
            return None

    @staticmethod
    def _apply_wildcard_to_field(
        queryset: models.QuerySet,
        param_name: str,
        param_value: str,
        field: models.Field,
        django_models: Any,
    ) -> models.QuerySet:
        """Apply wildcard filtering to a specific field.

        Supports:
        - Text fields: wildcard patterns (*test*, test*, *test, t*t)
        - Number fields: comparison operators (>=10, <=100, >5, <20) and ranges (10-20)
        - Other fields: exact match

        Args:
            queryset: The queryset to filter.
            param_name: The parameter name (field or lookup path).
            param_value: The parameter value (may contain wildcards or operators).
            field: The Django field object.
            django_models: Django models module.

        Returns:
            Filtered queryset.
        """
        # Check if this is a number field
        is_number_field = isinstance(
            field,
            (
                django_models.IntegerField,
                django_models.BigIntegerField,
                django_models.SmallIntegerField,
                django_models.PositiveIntegerField,
                django_models.PositiveSmallIntegerField,
                django_models.FloatField,
                django_models.DecimalField,
            )
        )

        if is_number_field:
            return CRUDUtils._apply_number_filter(queryset, param_name, param_value, field)

        # Check if this is a text field
        if isinstance(field, (django_models.CharField, django_models.TextField)):
            return CRUDUtils._apply_text_wildcard_filter(queryset, param_name, param_value)

        # For other field types (Boolean, Date, etc.), use exact match
        return queryset.filter(**{param_name: param_value})

    @staticmethod
    def _apply_number_filter(
        queryset: models.QuerySet,
        param_name: str,
        param_value: str,
        field: models.Field,
    ) -> models.QuerySet:
        """Apply filtering to number fields with support for comparison operators and ranges.

        Supports:
        - Exact match: age=25
        - Greater than or equal: age=>=25 or age=>=25
        - Less than or equal: age=<=100 or age=<=100
        - Greater than: age=>25 or age=>25
        - Less than: age=<25 or age=<25
        - Range: age=10-20 (inclusive)

        Args:
            queryset: The queryset to filter.
            param_name: The parameter name (field or lookup path).
            param_value: The parameter value (may contain operators).
            field: The Django field object.

        Returns:
            Filtered queryset.
        """
        param_value = param_value.strip()

        # Handle range queries (e.g., "10-20")
        if '-' in param_value and not param_value.startswith('-') and not param_value.startswith(
                '>') and not param_value.startswith('<'):
            try:
                parts = param_value.split('-', 1)
                if len(parts) == 2:
                    min_val = parts[0].strip()
                    max_val = parts[1].strip()
                    if min_val and max_val:
                        # Try to convert to appropriate number type
                        if isinstance(field, (models.IntegerField, models.BigIntegerField, models.SmallIntegerField,
                                              models.PositiveIntegerField, models.PositiveSmallIntegerField)):
                            min_val = int(min_val)
                            max_val = int(max_val)
                        else:
                            min_val = float(min_val)
                            max_val = float(max_val)
                        return queryset.filter(**{f'{param_name}__gte': min_val, f'{param_name}__lte': max_val})
            except (ValueError, TypeError):
                # If conversion fails, fall back to exact match attempt
                pass

        # Handle comparison operators
        if param_value.startswith('>='):
            try:
                value = param_value[2:].strip()
                if isinstance(field, (models.IntegerField, models.BigIntegerField, models.SmallIntegerField,
                                      models.PositiveIntegerField, models.PositiveSmallIntegerField)):
                    value = int(value)
                else:
                    value = float(value)
                return queryset.filter(**{f'{param_name}__gte': value})
            except (ValueError, TypeError):
                return queryset.none()

        if param_value.startswith('<='):
            try:
                value = param_value[2:].strip()
                if isinstance(field, (models.IntegerField, models.BigIntegerField, models.SmallIntegerField,
                                      models.PositiveIntegerField, models.PositiveSmallIntegerField)):
                    value = int(value)
                else:
                    value = float(value)
                return queryset.filter(**{f'{param_name}__lte': value})
            except (ValueError, TypeError):
                return queryset.none()

        if param_value.startswith('>'):
            try:
                value = param_value[1:].strip()
                if isinstance(field, (models.IntegerField, models.BigIntegerField, models.SmallIntegerField,
                                      models.PositiveIntegerField, models.PositiveSmallIntegerField)):
                    value = int(value)
                else:
                    value = float(value)
                return queryset.filter(**{f'{param_name}__gt': value})
            except (ValueError, TypeError):
                return queryset.none()

        if param_value.startswith('<'):
            try:
                value = param_value[1:].strip()
                if isinstance(field, (models.IntegerField, models.BigIntegerField, models.SmallIntegerField,
                                      models.PositiveIntegerField, models.PositiveSmallIntegerField)):
                    value = int(value)
                else:
                    value = float(value)
                return queryset.filter(**{f'{param_name}__lt': value})
            except (ValueError, TypeError):
                return queryset.none()

        # Default: exact match
        try:
            if isinstance(field, (models.IntegerField, models.BigIntegerField, models.SmallIntegerField,
                                  models.PositiveIntegerField, models.PositiveSmallIntegerField)):
                value = int(param_value)
            else:
                value = float(param_value)
            return queryset.filter(**{param_name: value})
        except (ValueError, TypeError):
            # Invalid number format - return empty queryset
            return queryset.none()

    @staticmethod
    def _apply_text_wildcard_filter(
        queryset: models.QuerySet,
        param_name: str,
        param_value: str,
    ) -> models.QuerySet:
        """Apply wildcard filtering to text fields."""

        # Handle wildcard patterns
        if '*' not in param_value:
            # No wildcard - use exact match (case-insensitive)
            return queryset.filter(**{f'{param_name}__iexact': param_value})
        elif param_value == '*':
            # Just * means match anything - skip this filter
            return queryset
        elif CRUDUtils._has_middle_wildcard(param_value) or param_value.count('*') > 1:
            # Multiple * or * in middle -> use regex
            return queryset.filter(**{f'{param_name}__iregex': CRUDUtils._wildcard_to_regex(param_value)})
        elif param_value.startswith('*') and param_value.endswith('*'):
            # *test* -> contains
            clean_value = param_value.strip('*')
            if clean_value:
                return queryset.filter(**{f'{param_name}__icontains': clean_value})
        elif param_value.startswith('*'):
            # *test -> ends with
            clean_value = param_value.lstrip('*')
            if clean_value:
                return queryset.filter(**{f'{param_name}__iendswith': clean_value})
        elif param_value.endswith('*'):
            # test* -> starts with
            clean_value = param_value.rstrip('*')
            if clean_value:
                return queryset.filter(**{f'{param_name}__istartswith': clean_value})

        return queryset

    @staticmethod
    def _has_middle_wildcard(value: str) -> bool:
        """Check if wildcard appears in the middle of the string."""

        return len(value) > 2 and '*' in value[1:-1]

    @staticmethod
    def _wildcard_to_regex(pattern: str) -> str:
        """Convert wildcard pattern to regex pattern."""

        return re.escape(pattern).replace(r'\*', '.*')

    @staticmethod
    def _apply_ordering(
        queryset: models.QuerySet,
        request: Request,
        ordering_fields: Optional[list[str]] = None,
        default_ordering: Optional[list[str]] = None,
    ) -> models.QuerySet:
        """Apply ordering to queryset."""

        ordering_param = request.query_params.get('ordering')

        if ordering_param:
            if ordering_fields:
                # Validate ordering fields
                valid_ordering = [
                    part for part in ordering_param.split(',')
                    if part.lstrip('-') in ordering_fields
                ]
                if valid_ordering:
                    return queryset.order_by(*valid_ordering)
            else:
                # Allow any field ordering (less secure but more flexible)
                return queryset.order_by(*ordering_param.split(','))

        # Apply default ordering if no user ordering specified
        if default_ordering:
            return queryset.order_by(*default_ordering)

        # Try to get default ordering from model Meta
        model = queryset.model
        if hasattr(model._meta, 'ordering') and model._meta.ordering:
            return queryset.order_by(*model._meta.ordering)

        # Fallback: order by pk to ensure consistent pagination
        return queryset.order_by('pk')

    @staticmethod
    def _get_lookup_target_field(model: Type[models.Model], lookup_path: str) -> Optional[models.Field]:
        """Get the target field from a Django lookup path."""

        parts = lookup_path.split('__')
        current_model = model

        for part in parts[:-1]:
            try:
                field = current_model._meta.get_field(part)
                if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                    current_model = field.related_model
                elif isinstance(field, models.ManyToManyField):
                    current_model = field.related_model
                else:
                    return None
            except FieldDoesNotExist:
                return None

        # Get the final field
        try:
            return current_model._meta.get_field(parts[-1])
        except FieldDoesNotExist:
            return None

    @staticmethod
    def _validate_lookup_path(model: Type[models.Model], lookup_path: str) -> bool:
        """Validate that a Django lookup path (e.g., 'first_app__name') exists."""

        parts = lookup_path.split('__')
        current_model = model

        for part in parts[:-1]:
            try:
                field = current_model._meta.get_field(part)
                if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                    current_model = field.related_model
                elif isinstance(field, models.ManyToManyField):
                    current_model = field.related_model
                else:
                    return False
            except FieldDoesNotExist:
                return False

        # Check if the final field exists
        try:
            current_model._meta.get_field(parts[-1])
            return True
        except FieldDoesNotExist:
            return False

    @staticmethod
    def _apply_wildcard_filtering(
        queryset: models.QuerySet,
        request: Request,
    ) -> models.QuerySet:
        """Apply generic wildcard filtering directly to queryset.

        Supports filtering for different field types:

        Text fields (wildcard patterns):
        - name=test*  -> name__istartswith=test (starts with)
        - name=*test  -> name__iendswith=test (ends with)
        - name=*test* -> name__icontains=test (contains)
        - name=t*t    -> name__iregex (regex pattern matching, e.g., matches "test", "tart")
        - name=test   -> name__iexact=test (exact match, default)

        Number fields (comparison operators and ranges):
        - age=25      -> exact match
        - age=>=25    -> greater than or equal
        - age=<=100   -> less than or equal
        - age=>25     -> greater than
        - age=<25     -> less than
        - age=10-20   -> range (inclusive)

        ForeignKey lookups:
        - first_app__name=t* -> Filter by related ForeignKey field
        - first_app__age=>=18 -> Filter by related number field

        Works generically for any field on any model, including ForeignKey lookups.

        Args:
            queryset: The queryset to filter.
            request: The HTTP request object.

        Returns:
            Filtered queryset.

        Raises:
            ValidationError: If a filter field doesn't exist on the model.
        """
        from django.db import models as django_models

        query_params = request.query_params.copy()
        model = queryset.model
        model_fields = {f.name for f in model._meta.get_fields()}

        # Reserved query parameters that shouldn't be treated as field filters
        reserved_params = {'page', 'page_size', 'ordering', 'format'}

        # Track if we have any non-reserved, non-empty query params
        has_filter_params = False
        filtered_queryset = queryset

        for param_name, param_value in query_params.items():
            # Skip reserved params and empty values
            if param_name in reserved_params or not param_value:
                continue

            # We have a filter parameter
            has_filter_params = True

            # Check if this is a ForeignKey lookup (contains __)
            is_related_lookup = '__' in param_name

            if is_related_lookup:
                # Validate ForeignKey lookup path exists
                if not CRUDUtils._validate_lookup_path(model, param_name):
                    # Invalid lookup path - raise exception
                    raise ValidationError(
                        {param_name: f"Invalid lookup path: '{param_name}' does not exist on {model.__name__}"}
                    )

                # For related lookups, determine the target field type
                target_field = CRUDUtils._get_lookup_target_field(model, param_name)
                if target_field is None:
                    # Field doesn't exist - raise exception
                    raise ValidationError(
                        {param_name: f"Field '{param_name}' does not exist on {model.__name__}"}
                    )

                # Apply wildcard filtering to related field
                filtered_queryset = CRUDUtils._apply_wildcard_to_field(
                    filtered_queryset, param_name, param_value, target_field, django_models
                )
            else:
                # Direct field lookup
                if param_name not in model_fields:
                    # Field doesn't exist - raise exception
                    raise ValidationError(
                        {param_name: f"Field '{param_name}' does not exist on {model.__name__}"}
                    )

                # Get field type to determine appropriate lookup
                try:
                    field = model._meta.get_field(param_name)
                except FieldDoesNotExist:
                    # Field doesn't exist - raise exception
                    raise ValidationError(
                        {param_name: f"Field '{param_name}' does not exist on {model.__name__}"}
                    )

                # Apply wildcard filtering to direct field
                filtered_queryset = CRUDUtils._apply_wildcard_to_field(
                    filtered_queryset, param_name, param_value, field, django_models
                )

        # If we had filter params but no valid filters were applied, return empty
        # This handles the case where all params were reserved or empty
        if has_filter_params:
            return filtered_queryset

        # No filter params at all - return original queryset
        return queryset

    @staticmethod
    def _apply_filtering(
        queryset: models.QuerySet,
        request: Request,
    ) -> models.QuerySet:
        """Apply filtering to queryset using django-filter or generic wildcard filtering."""

        # Use generic wildcard filtering
        # Apply wildcard filtering if there are query params
        # This ensures empty results when filters don't match, not all items
        if request.query_params:
            return CRUDUtils._apply_wildcard_filtering(queryset, request)
        return queryset

    @staticmethod
    def _build_queryset(
        model_class: Type[models.Model],
        queryset_hook: Optional[Callable] = None,
        select_related: Optional[list[str]] = None,
        prefetch_related: Optional[list[str]] = None,
    ) -> models.QuerySet:  # constant filter: queryset_hook=lambda: FirstApp.objects.filter(is_active=True)
        """Build and optimize a queryset."""

        if queryset_hook:
            queryset = queryset_hook()
        else:
            queryset = model_class.objects.all()

        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)

        return queryset

    @staticmethod
    def get(
        request: Request,
        model_class: Type[models.Model],
        serializer_class: Type[ModelSerializer],
        pagination_class: Optional[Type[PageNumberPagination]] = None,
        queryset_hook: Optional[Callable] = None,
        ordering_fields: Optional[list[str]] = None,
        default_ordering: Optional[list[str]] = None,
        select_related: Optional[list[str]] = None,
        prefetch_related: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> Response:
        """Retrieve a single instance or paginated list of instances.

        Supports:
        - Single instance: GET /resource/<pk>/
        - List with pagination: GET /resource/?page=1&page_size=20
        - Filtering: GET /resource/?name=something
        - Ordering: GET /resource/?ordering=-created_at,name

        Args:
            request: The HTTP request object.
            model_class: The Django model class to query.
            serializer_class: The DRF serializer class for serialization.
            pagination_class: Optional pagination class (defaults to StandardResultsSetPagination).
            queryset_hook: Optional function to customize base queryset.
            ordering_fields: List of allowed ordering fields.
            default_ordering: Default ordering if none specified (e.g., ['-created_at']).
            select_related: List of ForeignKey/OneToOne fields to optimize.
            prefetch_related: List of ManyToMany/ReverseForeignKey fields to optimize.
            **kwargs: Additional keyword arguments, including 'pk' for single instance retrieval.

        Returns:
            Response: HTTP 200 with serialized data, or HTTP 404 if instance not found.
        """
        if pk := kwargs.get('pk'):
            # Single instance retrieval
            instance = CRUDUtils._get_instance_by_pk(
                model_class=model_class,
                pk=pk,
                select_related=select_related,
                prefetch_related=prefetch_related,
            )
            if not instance:
                return Response(status=status.HTTP_404_NOT_FOUND)
            serializer = serializer_class(instance, context={'request': request})
            return Response(serializer.data)
        else:
            # List retrieval with pagination, filtering, and ordering
            queryset = CRUDUtils._build_queryset(
                model_class=model_class,
                queryset_hook=queryset_hook,
                select_related=select_related,
                prefetch_related=prefetch_related,
            )

            # Apply filtering
            queryset = CRUDUtils._apply_filtering(queryset=queryset, request=request)

            # Apply ordering (ensures consistent pagination - MUST be before pagination)
            print()
            queryset = CRUDUtils._apply_ordering(
                queryset=queryset, request=request, ordering_fields=ordering_fields, default_ordering=default_ordering
            )

            # Apply pagination
            print()
            if pagination_class is None:
                pagination_class = StandardResultsSetPagination

            paginator = pagination_class()
            page = paginator.paginate_queryset(queryset=queryset, request=request)

            if page is not None:
                serializer = serializer_class(page, context={'request': request}, many=True)
                return paginator.get_paginated_response(serializer.data)

            # No pagination, return all results
            print()
            serializer = serializer_class(queryset, context={'request': request}, many=True)
            return Response(serializer.data)

    @staticmethod
    def post(
        request: Request,
        serializer_class: Type[ModelSerializer],
        **kwargs: Any,
    ) -> Response:
        """Create a new instance."""

        serializer = serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                serializer.save(**kwargs)
                model_name = serializer_class.Meta.model.__name__
                instance_id = serializer.data.get('id')
                logger.info(f"Created {model_name} with id={instance_id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except (IntegrityError, DjangoValidationError) as e:
                logger.error(f"Database error creating {serializer_class.Meta.model.__name__}: {str(e)}")
                return Response(
                    {'error': 'Database constraint violation', 'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        model_name = serializer_class.Meta.model.__name__
        logger.warning(f"Validation failed for {model_name}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _update_instance(
        request: Request,
        model_class: Type[models.Model],
        serializer_class: Type[ModelSerializer],
        pk: Any,
        partial: bool,
        select_related: Optional[list[str]] = None,
        prefetch_related: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> Response:
        """Internal method to update an instance."""

        instance = CRUDUtils._get_instance_by_pk(
            model_class=model_class,
            pk=pk,
            select_related=select_related,
            prefetch_related=prefetch_related,
        )
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = serializer_class(
            instance,
            data=request.data,
            context={'request': request},
            partial=partial
        )
        if serializer.is_valid():
            try:
                serializer.save(**kwargs)
                update_type = "Partially updated" if partial else "Updated"
                logger.info(f"{update_type} {model_class.__name__} with pk={pk}")
                return Response(serializer.data)
            except (IntegrityError, DjangoValidationError) as e:
                logger.error(f"Database error updating {model_class.__name__} pk={pk}: {str(e)}")
                return Response(
                    {'error': 'Database constraint violation', 'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        logger.warning(f"Validation failed for {model_class.__name__} pk={pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def put(
        request: Request,
        model_class: Type[models.Model],
        serializer_class: Type[ModelSerializer],
        select_related: Optional[list[str]] = None,
        prefetch_related: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> Response:
        """Update an existing instance with full replacement (PUT semantics)."""

        if not (pk := kwargs.pop('pk', None)):
            logger.warning(f"PUT request missing pk for {model_class.__name__}")
            return Response(status=status.HTTP_404_NOT_FOUND)
        return CRUDUtils._update_instance(
            request=request,
            model_class=model_class,
            serializer_class=serializer_class,
            pk=pk,
            partial=False,
            select_related=select_related,
            prefetch_related=prefetch_related,
            **kwargs
        )

    @staticmethod
    def patch(
        request: Request,
        model_class: Type[models.Model],
        serializer_class: Type[ModelSerializer],
        select_related: Optional[list[str]] = None,
        prefetch_related: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> Response:
        """Partially update an existing instance (PATCH semantics)."""

        if not (pk := kwargs.pop('pk', None)):
            logger.warning(f"PATCH request missing pk for {model_class.__name__}")
            return Response(status=status.HTTP_404_NOT_FOUND)
        return CRUDUtils._update_instance(
            request=request,
            model_class=model_class,
            serializer_class=serializer_class,
            pk=pk,
            partial=True,
            select_related=select_related,
            prefetch_related=prefetch_related,
            **kwargs
        )

    @staticmethod
    def delete(
        request: Request,
        model_class: Type[models.Model],
        **kwargs: Any,
    ) -> Response:
        """Delete an existing instance."""

        if not (pk := kwargs.get('pk')):
            logger.warning(f"DELETE request missing pk for {model_class.__name__}")
            return Response(status=status.HTTP_404_NOT_FOUND)

        instance = CRUDUtils._get_instance_by_pk(model_class, pk)
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            instance.delete()
            logger.info(f"Deleted {model_class.__name__} with pk={pk}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting {model_class.__name__} pk={pk}: {str(e)}")
            return Response(
                {'error': 'Failed to delete instance', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
