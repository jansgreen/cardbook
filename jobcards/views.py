from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView, View
from rest_framework import permissions, status
from rest_framework.views import APIView

from cardbookweb.qr import QRStyle, qr_svg_response, static_image_data_uri
from cardbookweb.responses import StandardPagination, error_response, success_response
from companies.models import Company
from companies.permissions import can_manage_company
from .forms import WhiteCardJobForm
from .models import SavedJobCard, Specialty, WhiteCardJob
from .serializers import SavedJobCardSerializer, SpecialtySerializer, WhiteCardJobSerializer
from .services import (
    ensure_default_specialties,
    get_company_for_user,
    recommended_job_cards,
    save_job_card_for_company,
    user_active_job_card,
)


WHITE_CARD_QR_STYLE = QRStyle(
    dot_color="#003875",
    marker_color="#0057b8",
    background_color="#fffaf0",
    shape="diamond",
)


def white_card_job_qr_svg(request, username):
    card = get_object_or_404(WhiteCardJob.objects.select_related("user", "specialty"), user__username=username, is_active=True)
    card_url = request.build_absolute_uri(reverse("public-white-card-job", kwargs={"username": card.username}))
    logo_url = static_image_data_uri("img/logo.png")
    return qr_svg_response(card_url, WHITE_CARD_QR_STYLE, logo_url=logo_url)


class WhiteCardJobListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = WhiteCardJob.objects.filter(is_active=True, is_available=True).select_related("user", "specialty")
        specialty = request.GET.get("specialty")
        city = request.GET.get("city")
        if specialty:
            queryset = queryset.filter(specialty__slug=specialty)
        if city:
            queryset = queryset.filter(address__icontains=city)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = WhiteCardJobSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = WhiteCardJobSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        card = serializer.save()
        return success_response("White Card Job creada.", WhiteCardJobSerializer(card, context={"request": request}).data, status.HTTP_201_CREATED)


class WhiteCardJobMeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request):
        return user_active_job_card(request.user)

    def get(self, request):
        card = self.get_object(request)
        if not card:
            return error_response("No tienes una White Card Job activa.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response("White Card Job.", WhiteCardJobSerializer(card, context={"request": request}).data)

    def patch(self, request):
        card = self.get_object(request)
        if not card:
            return error_response("No tienes una White Card Job activa.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = WhiteCardJobSerializer(card, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response("White Card Job actualizada.", serializer.data)

    def delete(self, request):
        card = self.get_object(request)
        if not card:
            return error_response("No tienes una White Card Job activa.", status_code=status.HTTP_404_NOT_FOUND)
        card.is_active = False
        card.is_available = False
        card.save(update_fields=["is_active", "is_available", "updated_at"])
        return success_response("White Card Job desactivada.")


class PublicWhiteCardJobAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, username):
        card = get_object_or_404(WhiteCardJob.objects.select_related("user", "specialty"), user__username=username, is_active=True)
        WhiteCardJob.objects.filter(pk=card.pk).update(card_views=F("card_views") + 1)
        return success_response("White Card Job publica.", WhiteCardJobSerializer(card, context={"request": request}).data)


class SpecialtyListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ensure_default_specialties()
        return success_response("Especialidades.", SpecialtySerializer(Specialty.objects.all(), many=True).data)


class HiringRecommendationsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        company = get_company_for_user(request.user, request.GET.get("company"))
        if not company:
            return error_response("Necesitas una empresa para ver candidatos.", status_code=status.HTTP_400_BAD_REQUEST)
        cards = recommended_job_cards(company, limit=5)
        return success_response("Candidatos recomendados.", WhiteCardJobSerializer(cards, many=True, context={"request": request}).data)


class SavedJobCardListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        company = get_company_for_user(request.user, request.GET.get("company"))
        if not company:
            return error_response("Necesitas una empresa para ver candidatos guardados.", status_code=status.HTTP_400_BAD_REQUEST)
        queryset = SavedJobCard.objects.filter(company=company).select_related("company", "job_card__user", "job_card__specialty", "saved_by")
        return success_response("Candidatos guardados.", SavedJobCardSerializer(queryset, many=True, context={"request": request}).data)


class SaveJobCardAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        company = get_company_for_user(request.user, request.data.get("company"))
        if not company:
            return error_response("Necesitas una empresa valida.", status_code=status.HTTP_400_BAD_REQUEST)
        job_card = get_object_or_404(WhiteCardJob, pk=request.data.get("job_card"), is_active=True)
        try:
            saved = save_job_card_for_company(company=company, job_card=job_card, saved_by=request.user, notes=request.data.get("notes") or "")
        except (PermissionError, ValueError) as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        return success_response("Candidato guardado.", SavedJobCardSerializer(saved, context={"request": request}).data, status.HTTP_201_CREATED)


class SavedJobCardDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        item = get_object_or_404(SavedJobCard.objects.select_related("company"), pk=pk)
        if not can_manage_company(request.user, item.company):
            return error_response("No puedes eliminar este candidato.", status_code=status.HTTP_403_FORBIDDEN)
        item.delete()
        return success_response("Candidato eliminado.")


class PublicWhiteCardJobView(TemplateView):
    template_name = "jobcards/public_card.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        card = get_object_or_404(WhiteCardJob.objects.select_related("user", "specialty"), user__username=kwargs["username"], is_active=True)
        WhiteCardJob.objects.filter(pk=card.pk).update(profile_views=F("profile_views") + 1)
        context["job_card"] = card
        context["saved_total"] = card.saved_by_companies.count()
        return context


class DashboardWhiteCardJobView(LoginRequiredMixin, TemplateView):
    login_url = "/login/"
    template_name = "dashboard/jobcards/white_card.html"

    def get_context_data(self, **kwargs):
        ensure_default_specialties()
        context = super().get_context_data(**kwargs)
        card = user_active_job_card(self.request.user)
        form = kwargs.get("form") or WhiteCardJobForm(instance=card, user=self.request.user)
        categories = list(
            Specialty.objects.exclude(category="")
            .order_by("category")
            .values_list("category", flat=True)
            .distinct()
        )
        specialties_by_category = {}
        for specialty in Specialty.objects.order_by("category", "name"):
            specialties_by_category.setdefault(specialty.category or "General", []).append({
                "id": specialty.id,
                "name": specialty.name,
            })
        context.update({
            "job_card": card,
            "form": form,
            "can_create_job_card": bool(card) or not Company.objects.filter(is_active=True, owner=self.request.user).exists(),
            "job_categories": categories,
            "specialties_by_category": specialties_by_category,
            "saved_total": card.saved_by_companies.count() if card else 0,
            "public_url": reverse("public-white-card-job", kwargs={"username": self.request.user.username}) if card else "",
        })
        return context

    def post(self, request, *args, **kwargs):
        card = user_active_job_card(request.user)
        if request.POST.get("action") == "toggle_availability" and card:
            card.is_available = not card.is_available
            card.save(update_fields=["is_available", "updated_at"])
            messages.success(request, "Disponibilidad actualizada.")
            return redirect("dashboard-white-card-job")
        if request.POST.get("action") == "delete_card" and card:
            card.is_active = False
            card.is_available = False
            card.save(update_fields=["is_active", "is_available", "updated_at"])
            messages.success(request, "White Card Job eliminada del panel publico.")
            return redirect("dashboard-white-card-job")
        form = WhiteCardJobForm(request.POST, request.FILES, instance=card, user=request.user)
        if form.is_valid():
            job_card = form.save(commit=False)
            job_card.user = request.user
            job_card.save()
            messages.success(request, "White Card Job guardada.")
            return redirect("dashboard-white-card-job")
        return self.render_to_response(self.get_context_data(form=form))


class DashboardSaveJobCardView(LoginRequiredMixin, View):
    login_url = "/login/"

    def post(self, request, pk):
        company = get_company_for_user(request.user, request.POST.get("company"))
        job_card = get_object_or_404(WhiteCardJob, pk=pk, is_active=True)
        if not company:
            messages.error(request, "Necesitas una empresa para guardar candidatos.")
            return redirect("dashboard-book")
        try:
            save_job_card_for_company(company=company, job_card=job_card, saved_by=request.user)
            messages.success(request, "Candidato guardado en Book.")
        except (PermissionError, ValueError) as exc:
            messages.error(request, str(exc))
        return redirect("dashboard-book")


class DashboardDeleteSavedJobCardView(LoginRequiredMixin, View):
    login_url = "/login/"

    def post(self, request, pk):
        item = get_object_or_404(SavedJobCard.objects.select_related("company"), pk=pk)
        if not can_manage_company(request.user, item.company):
            messages.error(request, "No puedes eliminar este candidato.")
            return redirect("dashboard-book")
        item.delete()
        messages.success(request, "Candidato eliminado de guardados.")
        return redirect("dashboard-book")
