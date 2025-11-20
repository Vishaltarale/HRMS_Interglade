from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'

    def get_paginated_response(self, data):
        return Response({
            "data": data,
            "message": "Organizations fetched successfully",
            "statusCode": 200,
            "meta": {
                "total": self.page.paginator.count,
                "page": self.page.number,
                "pages": self.page.paginator.num_pages
            }
        })
