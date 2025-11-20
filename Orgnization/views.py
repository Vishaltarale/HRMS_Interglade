from django.shortcuts import render
from Orgnization.serializer import OrgnizationSerializer
from Orgnization.models import Organization
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from rest_framework.pagination import PageNumberPagination
from Employee.serializer import StudentSerializer
import logging


@api_view(['POST'])
def create_org(request):
    serializer = OrgnizationSerializer(data=request.data)
    print("fetched data",request.data)
    if serializer.is_valid():
        serializer.save()
        print("serialised data",serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# GET /org/fetch/?page=1
# GET /org/fetch/?page=2
@api_view(['GET'])
def list_org(request):
    paginator = PageNumberPagination()
    paginator.page_size = 10  

    org = Organization.objects.all()

    result_page = paginator.paginate_queryset(org, request)
    serializer = OrgnizationSerializer(result_page, many=True)

    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def fetch_org(request,pk):
    try:
        org = Organization.objects.get(id=pk)
    except Organization.DoesNotExist:
        return Response({'error':'data not found'},status=status.HTTP_204_NO_CONTENT)
    serializer = OrgnizationSerializer(org)
    return Response(serializer.data,status=status.HTTP_200_OK)

@api_view(['PUT'])
def update_org(request,pk):
    try:
        org = Organization.objects.get(id=pk)
    except Organization.DoesNotExist:
        return Response({'error':'data not found'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = OrgnizationSerializer(org,data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_org(request,pk):
    try:
        org = Organization.objects.get(id=pk)
    except Organization.DoesNotExist:
        return Response({'error':'data not found'}, status=status.HTTP_400_BAD_REQUEST)
    org.delete()
    return Response({"Message":'Orgnization Record deleted successfully'},status=status.HTTP_200_OK)