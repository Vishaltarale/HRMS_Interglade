from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "limit"

    def paginate_queryset(self, queryset, request, view=None):
        self.page_size = int(request.query_params.get("limit", self.page_size))
        self.page_number = int(request.query_params.get("page", 1))

        total_count = queryset.count()
        start = (self.page_number - 1) * self.page_size
        end = start + self.page_size

        self.total_pages = math.ceil(total_count / self.page_size)
        self.total_count = total_count

        return queryset[start:end]

    def get_paginated_response(self, data):
        return Response({
            "statusCode": 200,
            "message": "Attendance fetched successfully",
            "data": data,
            "meta": {
                "total": self.total_count,
                "page": self.page_number,
                "pages": self.total_pages
            }
        })
