from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Student
from Employee.serializer import StudentSerializer

# CREATE new student
# @api_view(['POST'])
# def create_student(request):
#     serializer = StudentSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# # READ all students
# @api_view(['GET'])
# def list_students(request):
#     students = Student.objects.all()
#     serializer = StudentSerializer(students, many=True)
#     return Response(serializer.data, status=status.HTTP_200_OK)


# # READ single student
# @api_view(['GET'])
# def get_student(request, pk):
#     try:
#         student = Student.objects.get(id=pk)
#     except Student.DoesNotExist:
#         return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

#     serializer = StudentSerializer(student)
#     return Response(serializer.data, status=status.HTTP_200_OK)


# # UPDATE student
# @api_view(['PUT'])
# def update_student(request, pk):
#     try:
#         student = Student.objects.get(id=pk)
#     except Student.DoesNotExist:
#         return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

#     serializer = StudentSerializer(student, data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# # DELETE student
# @api_view(['DELETE'])
# def delete_student(request, pk):
#     try:
#         student = Student.objects.get(id=pk)
#     except Student.DoesNotExist:
#         return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

#     student.delete()
#     return Response({'message': 'Student deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def list_students(request):
    student = Student.objects.all()
    serializer = StudentSerializer(student,many=True)
    return Response(serializer.data,status=status.HTTP_200_OK)

@api_view(['POST'])
def create_student(request):
    serializer = StudentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data,status=status.HTTP_200_OK)
    return Response({'error':'Serialiser is not valid'},status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def update_student(request,pk):
    try:
        student = Student.objects.get(id=pk)
    except Student.DoesNotExist:
        return Response({'error':'student not fetched proeprly'},status=status.HTTP_204_NO_CONTENT)

    serializer = StudentSerializer(student,data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data,status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_student(request,pk):
    try:
        student = Student.objects.get(id=pk)
    except Student.DoesNotExist:
        return Response({'error':'student not fetched proeprly'},status=status.HTTP_204_NO_CONTENT)
    serializer = StudentSerializer(student)
    return Response(serializer.data,status=status.HTTP_200_OK)

@api_view(['DELETE'])
def delete_student(request,pk):
    try:
        student = Student.objects.get(id=pk)
    except Student.DEosNotExist:
        return Response({'error':'student not fetched proeprly'},status=status.HTTP_204_NO_CONTENT)
    student.delete()
    return Response({"Message":'Student deleted successfully'},status=status.HTTP_200_OK)