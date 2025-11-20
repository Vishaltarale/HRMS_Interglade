from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from Shifts.serializer import ShiftSerializer
from Shifts.models import Shift


# Create your views here.
@api_view(['POST'])
def create_shift(request):
    shift = ShiftSerializer(data=request.data)
    if shift.is_valid():
        shift.save()
        return Response(shift.data, status=status.HTTP_201_CREATED)
    return Response(shift.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def list_shift(request):
    shifts = Shift.objects.all()
    serializer = ShiftSerializer(shifts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def fetch_shift(request, pk):
    try:
        shift = Shift.objects.get(id=pk)
    except Shift.DoesNotExist:
        return Response({"error": "Shift not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ShiftSerializer(shift)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
def update_shift(request, pk):
    try:
        shift = Shift.objects.get(id=pk)
    except Shift.DoesNotExist:
        return Response({"error": "Shift not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ShiftSerializer(shift, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_shift(request, pk):
    try:
        shift = Shift.objects.get(id=pk)
    except Shift.DoesNotExist:
        return Response({"error": "Shift not found"}, status=status.HTTP_404_NOT_FOUND)
    
    shift.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

