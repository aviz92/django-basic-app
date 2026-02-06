from rest_framework import status
from rest_framework.response import Response


class ViewFunctions:
    @staticmethod
    def get(request, model_class, model_serializer_class, **kwargs):
        pk = kwargs.get('pk')
        if not pk:
            many = True
            response = model_class.objects.all()
        else:
            many = False
            try:
                response = model_class.objects.get(pk=pk)
            except model_class.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = model_serializer_class(response, context={'request': request}, many=many)
        return Response(serializer.data)

    @staticmethod
    def post(request, model_serializer_set_class):
        serializer = model_serializer_set_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def put(request, model_class, model_serializer_class, model_serializer_set_class, **kwargs):
        pk = kwargs.get('pk')
        if not pk:
            print('pk not exist')
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            queryset = model_class.objects.get(pk=pk)
        except model_class.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = model_serializer_set_class(queryset, context={'request': request}, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            serializer = model_serializer_class(
                model_class.objects.get(pk=serializer.data['id']),
                context={'request': request}
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
