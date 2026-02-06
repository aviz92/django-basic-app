"""View functions utility class for common CRUD (Create, Read, Update, Delete) operations in Django REST Framework."""

from typing import Any, Type

from django.db import models
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from custom_python_logger import build_logger

logger = build_logger(__name__)


class CRUDUtils:
    """Utility class providing common CRUD operations for Django REST Framework views."""

    @staticmethod
    def get(
        request: Request,
        model_class: Type[models.Model],
        serializer_class: Type[ModelSerializer],
        **kwargs: Any,
    ) -> Response:
        """Retrieve a single instance or list of instances.

        Args:
            request: The HTTP request object.
            model_class: The Django model class to query.
            serializer_class: The DRF serializer class for serialization.
            **kwargs: Additional keyword arguments, including 'pk' for single instance retrieval.

        Returns:
            Response: HTTP 200 with serialized data, or HTTP 404 if instance not found.
        """
        pk = kwargs.get('pk')
        if not pk:
            many = True
            queryset = model_class.objects.all()
        else:
            many = False
            try:
                queryset = model_class.objects.get(pk=pk)
            except model_class.DoesNotExist:
                logger.warning(f"{model_class.__name__} with pk={pk} not found")
                return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = serializer_class(queryset, context={'request': request}, many=many)
        return Response(serializer.data)

    @staticmethod
    def post(
        request: Request,
        serializer_class: Type[ModelSerializer],
    ) -> Response:
        """Create a new instance.

        Args:
            request: The HTTP request object containing the data to create.
            serializer_class: The DRF serializer class for validation and creation.

        Returns:
            Response: HTTP 201 with created instance data, or HTTP 400 with validation errors.
        """
        serializer = serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Created {serializer_class.Meta.model.__name__} with id={serializer.data.get('id')}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Validation failed for {serializer_class.Meta.model.__name__}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def put(
        request: Request,
        model_class: Type[models.Model],
        serializer_class: Type[ModelSerializer],
        **kwargs: Any,
    ) -> Response:
        """Update an existing instance with full replacement (PUT semantics).

        Args:
            request: The HTTP request object containing the complete replacement data.
            model_class: The Django model class to query.
            serializer_class: The DRF serializer class for validation and update.
            **kwargs: Additional keyword arguments, must include 'pk' for instance identification.

        Returns:
            Response: HTTP 200 with updated instance data, HTTP 404 if not found, or HTTP 400 with validation errors.
        """
        pk = kwargs.get('pk')
        if not pk:
            logger.warning(f"PUT request missing pk for {model_class.__name__}")
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            instance = model_class.objects.get(pk=pk)
        except model_class.DoesNotExist:
            logger.warning(f"{model_class.__name__} with pk={pk} not found")
            return Response(status=status.HTTP_404_NOT_FOUND)

        # PUT uses partial=False for full replacement semantics
        serializer = serializer_class(instance, data=request.data, context={'request': request}, partial=False)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Updated {model_class.__name__} with pk={pk}")
            return Response(serializer.data)
        logger.warning(f"Validation failed for {model_class.__name__} pk={pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def patch(
        request: Request,
        model_class: Type[models.Model],
        serializer_class: Type[ModelSerializer],
        **kwargs: Any,
    ) -> Response:
        """Partially update an existing instance (PATCH semantics).

        Args:
            request: The HTTP request object containing partial update data.
            model_class: The Django model class to query.
            serializer_class: The DRF serializer class for validation and update.
            **kwargs: Additional keyword arguments, must include 'pk' for instance identification.

        Returns:
            Response: HTTP 200 with updated instance data, HTTP 404 if not found, or HTTP 400 with validation errors.
        """
        pk = kwargs.get('pk')
        if not pk:
            logger.warning(f"PATCH request missing pk for {model_class.__name__}")
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            instance = model_class.objects.get(pk=pk)
        except model_class.DoesNotExist:
            logger.warning(f"{model_class.__name__} with pk={pk} not found")
            return Response(status=status.HTTP_404_NOT_FOUND)

        # PATCH uses partial=True for partial update semantics
        serializer = serializer_class(instance, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Partially updated {model_class.__name__} with pk={pk}")
            return Response(serializer.data)
        logger.warning(f"Validation failed for {model_class.__name__} pk={pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(
        request: Request,
        model_class: Type[models.Model],
        **kwargs: Any,
    ) -> Response:
        """Delete an existing instance.

        Args:
            request: The HTTP request object.
            model_class: The Django model class to query.
            **kwargs: Additional keyword arguments, must include 'pk' for instance identification.

        Returns:
            Response: HTTP 204 on successful deletion, HTTP 404 if instance not found.
        """
        pk = kwargs.get('pk')
        if not pk:
            logger.warning(f"DELETE request missing pk for {model_class.__name__}")
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            instance = model_class.objects.get(pk=pk)
        except model_class.DoesNotExist:
            logger.warning(f"{model_class.__name__} with pk={pk} not found")
            return Response(status=status.HTTP_404_NOT_FOUND)

        instance.delete()
        logger.info(f"Deleted {model_class.__name__} with pk={pk}")
        return Response(status=status.HTTP_204_NO_CONTENT)
