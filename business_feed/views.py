from django.db.models import Count
from rest_framework import permissions, status
from rest_framework.views import APIView

from cardbookweb.responses import StandardPagination, error_response, success_response
from companies.permissions import can_access_company, can_manage_company
from .models import BusinessPost, BusinessPostExcellent
from .serializers import BusinessPostSerializer


class BusinessPostListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        posts = BusinessPost.objects.filter(is_active=True).select_related("company").annotate(
            excellent_count=Count("excellents", distinct=True)
        ).order_by("-created_at")
        company_id = request.query_params.get("company")
        if company_id:
            posts = posts.filter(company_id=company_id)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = BusinessPostSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = BusinessPostSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("Business post creation failed.", serializer.errors)
        company = serializer.validated_data["company"]
        if not can_manage_company(request.user, company):
            return error_response("You do not have permission to publish for this company.", status_code=status.HTTP_403_FORBIDDEN)
        post = serializer.save()
        return success_response(
            "Business post created successfully.",
            BusinessPostSerializer(post, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )


class BusinessPostDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        return BusinessPost.objects.filter(pk=pk, is_active=True).select_related("company").first()

    def delete(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return error_response("Post not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_manage_company(request.user, post.company):
            return error_response("You do not have permission to delete this post.", status_code=status.HTTP_403_FORBIDDEN)
        post.is_active = False
        post.save(update_fields=["is_active"])
        return success_response("Post deleted successfully.")


class BusinessPostExcellentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        post = BusinessPost.objects.filter(pk=pk, is_active=True).select_related("company").first()
        if not post:
            return error_response("Post not found.", status_code=status.HTTP_404_NOT_FOUND)
        if not can_access_company(request.user, post.company):
            return error_response("You must belong to the business network to react.", status_code=status.HTTP_403_FORBIDDEN)
        _, created = BusinessPostExcellent.objects.get_or_create(post=post, user=request.user)
        message = "Excelente registered." if created else "Excelente already registered."
        return success_response(message, {"excellent_count": post.excellents.count(), "created": created})
