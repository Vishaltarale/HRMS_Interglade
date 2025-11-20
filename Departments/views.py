from django.shortcuts import render
from Departments.serializer import DepartmentsSerializer
from Departments.models import Departments
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from Employee.serializer import StudentSerializer
import logging



@api_view(['POST'])
def create_dept(request):
    serializer = DepartmentsSerializer(data=request.data)
    print("fetched data",request.data)
    if serializer.is_valid():
        serializer.save()
        print("serialised data",serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# GET /org/fetch/?page=1
# GET /org/fetch/?page=2
@api_view(['GET'])
def list_dept(request):
    paginator = PageNumberPagination()
    paginator.page_size = 10  

    org = Departments.objects.all()

    result_page = paginator.paginate_queryset(org, request)
    serializer = DepartmentsSerializer(result_page, many=True)

    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def fetch_dept(request,pk):
    try:
        org = Departments.objects.get(id=pk)
    except Departments.DoesNotExist:
        return Response({'error':'data not found'},status=status.HTTP_204_NO_CONTENT)
    serializer = DepartmentsSerializer(org)
    return Response(serializer.data,status=status.HTTP_200_OK)

@api_view(['PUT'])
def update_dept(request,pk):
    try:
        dept = Departments.objects.get(id=pk)
    except Departments.DoesNotExist:
        return Response({'error':'data not found'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = DepartmentsSerializer(dept,data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_dept(request,pk):
    try:
        dept = Departments.objects.get(id=pk)
    except Departments.DoesNotExist:
        return Response({'error':'data not found'}, status=status.HTTP_400_BAD_REQUEST)
    dept.delete()
    return Response({"Message":'Departments Record deleted successfully'},status=status.HTTP_200_OK)