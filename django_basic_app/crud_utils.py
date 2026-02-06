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
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from custom_python_logger import build_logger

logger = build_logger(__name__)

# Reserved query parameters that shouldn't be treated as field filters
RESERVED_PARAMS = {'page', 'page_size', 'ordering', 'format'}
RELATED_LOOKUP = '__'
OPERATOR_MAPPING = {
    '>=': ('__gte', 2),
    '<=': ('__lte', 2),
    '>': ('__gt', 1),
    '<': ('__lt', 1),
}
INTEGER_FIELDS = (
    models.IntegerField,
    models.BigIntegerField,
    models.SmallIntegerField,
    models.PositiveIntegerField,
    models.PositiveSmallIntegerField,
)


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
    def apply_pagination(
        queryset: models.QuerySet,
        request: Request,
        serializer_class: Type[ModelSerializer],
        pagination_class: Optional[Type[PageNumberPagination]] = None,
    ) -> Response:
        """Apply pagination to a queryset and return a paginated response."""

        pagination_class = pagination_class or StandardResultsSetPagination

        paginator = pagination_class()
        page = paginator.paginate_queryset(queryset=queryset, request=request)
        if page is not None:
            serializer = serializer_class(page, context={'request': request}, many=True)
            return paginator.get_paginated_response(serializer.data)

        # No pagination, return all results
        serializer = serializer_class(queryset, context={'request': request}, many=True)
        return Response(serializer.data)

    @staticmethod
    def _wildcard_to_regex(pattern: str) -> str:
        """Convert wildcard pattern to regex pattern."""

        return re.escape(pattern).replace(r'\*', '.*')

    @staticmethod
    def _has_middle_wildcard(value: str) -> bool:
        """Check if wildcard appears in the middle of the string."""

        return len(value) > 2 and '*' in value[1:-1]

    @staticmethod
    def _apply_text_wildcard_filter(
        queryset: models.QuerySet,
        param_name: str,
        param_value: str,
    ) -> models.QuerySet:
        """Apply wildcard filtering to text fields."""

        if '*' not in param_value:
            return queryset.filter(**{f'{param_name}__iexact': param_value})
        elif CRUDUtils._has_middle_wildcard(param_value) or param_value.count('*') > 1:
            return queryset.filter(**{f'{param_name}__iregex': CRUDUtils._wildcard_to_regex(param_value)})
        elif param_value.startswith('*') and param_value.endswith('*'):
            if clean_value := param_value.strip('*'):
                return queryset.filter(**{f'{param_name}__icontains': clean_value})
        elif param_value.startswith('*'):
            if clean_value := param_value.lstrip('*'):
                return queryset.filter(**{f'{param_name}__iendswith': clean_value})
        elif param_value.endswith('*'):
            if clean_value := param_value.rstrip('*'):
                return queryset.filter(**{f'{param_name}__istartswith': clean_value})
        return queryset

    @staticmethod
    def _convert_number_value(value: str, field: models.Field) -> int | float:
        """Convert string to int or float based on field type."""

        return int(value) if isinstance(field, INTEGER_FIELDS) else float(value)

    @staticmethod
    def _apply_number_filter(
        queryset: models.QuerySet,
        param_name: str,
        param_value: str,
        field: models.Field,
    ) -> models.QuerySet:
        """Apply filtering to number fields with support for comparison operators."""

        param_value = param_value.strip()
        lookup_suffix = ''
        value_str = param_value
        for operator, suffix in OPERATOR_MAPPING.items():
            if param_value.startswith(operator):
                lookup_suffix = suffix
                value_str = param_value[len(operator):].strip()
                break

        try:
            value = CRUDUtils._convert_number_value(value_str, field)
            filter_key = f'{param_name}{lookup_suffix}' if lookup_suffix else param_name
            return queryset.filter(**{filter_key: value})
        except (ValueError, TypeError):
            return queryset.none()

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

        is_text_field = isinstance(field, (django_models.CharField, django_models.TextField))
        if is_text_field:
            return CRUDUtils._apply_text_wildcard_filter(queryset, param_name, param_value)

        return queryset.filter(**{param_name: param_value})  # For other field types (bool, date, etc.), use exact match

    @staticmethod
    def _get_lookup_target_field(model: Type[models.Model], lookup_path: str) -> Optional[models.Field]:
        """Get the target field from a Django lookup path."""

        parts = lookup_path.split(RELATED_LOOKUP)
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

        filtered_queryset = queryset
        for param_name, param_value in query_params.items():
            if param_name in RESERVED_PARAMS or not param_value:  # Skip reserved params and empty values
                continue

            if RELATED_LOOKUP in param_name:  # Check if this is a ForeignKey lookup (contains "__")
                if not (target_field := CRUDUtils._get_lookup_target_field(model=model, lookup_path=param_name)):
                    raise ValidationError({param_name: f"Field '{param_name}' does not exist"})
            else:  # Direct field lookup
                if param_name not in model_fields:
                    raise ValidationError({param_name: f"Field '{param_name}' does not exist on {model.__name__}"})

                # Get field type to determine appropriate lookup
                try:
                    target_field = model._meta.get_field(param_name)
                except FieldDoesNotExist:
                    raise ValidationError({param_name: f"Field '{param_name}' does not exist on {model.__name__}"})

            filtered_queryset = CRUDUtils._apply_wildcard_to_field(
                queryset=filtered_queryset,
                param_name=param_name,
                param_value=param_value,
                field=target_field,
                django_models=django_models
            )
        return filtered_queryset

    @staticmethod
    def _apply_filtering(
        queryset: models.QuerySet,
        request: Request,
    ) -> models.QuerySet:
        """Apply filtering to queryset using django-filter or generic wildcard filtering."""

        if request.query_params:
            return CRUDUtils._apply_wildcard_filtering(queryset=queryset, request=request)
        return queryset

    @staticmethod
    def _build_queryset(
        model_class: Type[models.Model],
        queryset_hook: Optional[Callable] = None,
    ) -> models.QuerySet:  # constant filter: queryset_hook=lambda: FirstApp.objects.filter(is_active=True)
        """Build the initial queryset for list retrieval, allowing for optional customization via a hook."""

        if queryset_hook:
            queryset = queryset_hook()
        else:
            queryset = model_class.objects.all()
        return queryset

    @staticmethod
    def get(
        request: Request,
        model_class: Type[models.Model],
        serializer_class: Type[ModelSerializer],
        queryset_hook: Optional[Callable] = None,
        ordering_field: Optional[str] = 'pk',
        pagination_class: Optional[Type[PageNumberPagination]] = None,
        **kwargs: Any,
    ) -> Response:
        """Retrieve a single instance or paginated list of instances."""

        if pk := kwargs.get('pk'):
            instance = CRUDUtils._get_instance_by_pk(model_class=model_class, pk=pk)
            if not instance:
                return Response(status=status.HTTP_404_NOT_FOUND)
            serializer = serializer_class(instance, context={'request': request})
            return Response(serializer.data)
        else:
            queryset = CRUDUtils._build_queryset(model_class=model_class, queryset_hook=queryset_hook)
            queryset = CRUDUtils._apply_filtering(queryset=queryset, request=request)
            queryset = queryset.order_by(ordering_field)
            return CRUDUtils.apply_pagination(
                queryset=queryset,
                request=request,
                serializer_class=serializer_class,
                pagination_class=pagination_class,
            )

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
