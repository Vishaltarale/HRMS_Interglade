from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from Shifts.serializer import ShiftSerializer
from Shifts.models import Shift
from Employee.models import Employee
from HRMS.permissions import IsAdmin,IsHR,IsSREmployee, IsJREmployee, IsAuthenticated
import pytz
from datetime import datetime
from utils.timezone_utils import get_current_datetime_ist,get_current_time_ist

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated,IsHR | IsAdmin])
def create_shift(request):
    serializer = ShiftSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated,IsHR | IsAdmin])
def list_shift(request):
    shifts = Shift.objects.all()
    serializer = ShiftSerializer(shifts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated,IsHR | IsAdmin])
def fetch_shift(request, pk):
    try:
        shift = Shift.objects.get(id=pk)
    except Shift.DoesNotExist:
        return Response({"error": "Shift not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ShiftSerializer(shift)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated,IsHR | IsAdmin])
def update_shift(request, pk):
    try:
        shift = Shift.objects.get(id=pk)
    except Shift.DoesNotExist:
        return Response({"error": "Shift not found"}, status=status.HTTP_404_NOT_FOUND)
    print("curent time",get_current_time_ist())
    serializer = ShiftSerializer(shift, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated,IsHR | IsAdmin])
def delete_shift(request, pk):
    try:
        shift = Shift.objects.get(id=pk)
    except Shift.DoesNotExist:
        return Response({"error": "Shift not found"}, status=status.HTTP_404_NOT_FOUND)
    
    shift.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)