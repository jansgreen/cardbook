from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView, View

from companies.models import Company
from websitebuilder.models import Section
from websitebuilder.services import can_manage_website_builder
from .forms import FormDefinitionForm, FormFieldForm, PublicFormSubmissionForm
from .models import FormDefinition, FormField, FormSubmission
from .services import send_submission_email


class CompanyFormsAccessMixin(LoginRequiredMixin):
    login_url = "/login/"

    def get_company(self):
        company = get_object_or_404(Company, pk=self.kwargs["company_id"], is_active=True)
        if not can_manage_website_builder(self.request.user, company):
            raise Http404("Company not found.")
        return company


class DashboardFormListView(CompanyFormsAccessMixin, ListView):
    template_name = "dashboard/forms_builder/form_list.html"
    context_object_name = "forms"

    def get_queryset(self):
        self.company = self.get_company()
        return self.company.forms.prefetch_related("fields").order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "company": self.company,
            "active_company": self.company,
            "website": getattr(self.company, "builder_website", None),
            "definition_form": FormDefinitionForm(company=self.company, initial={"recipient_email": self.company.email or self.request.user.email}),
        })
        return context


class DashboardFormCreateView(CompanyFormsAccessMixin, View):
    def post(self, request, company_id):
        company = self.get_company()
        form = FormDefinitionForm(request.POST, company=company)
        if form.is_valid():
            form_definition = form.save(commit=False)
            form_definition.company = company
            form_definition.created_by = request.user
            form_definition.save()
            messages.success(request, "Formulario creado correctamente.")
            return redirect("dashboard-form-builder-detail", company_id=company.id, form_id=form_definition.id)
        return render(request, "dashboard/forms_builder/form_list.html", {
            "company": company,
            "active_company": company,
            "website": getattr(company, "builder_website", None),
            "forms": company.forms.prefetch_related("fields").order_by("name"),
            "definition_form": form,
        })


class DashboardFormDetailView(CompanyFormsAccessMixin, DetailView):
    template_name = "dashboard/forms_builder/form_detail.html"
    context_object_name = "form_definition"
    pk_url_kwarg = "form_id"

    def get_queryset(self):
        self.company = self.get_company()
        return self.company.forms.prefetch_related("fields", "submissions")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_definition = self.object
        public_url = self.request.build_absolute_uri(
            reverse("forms-builder-public-detail", kwargs={"company_slug": self.company.slug, "form_slug": form_definition.slug})
        )
        context.update({
            "company": self.company,
            "active_company": self.company,
            "definition_form": FormDefinitionForm(company=self.company, instance=form_definition),
            "field_form": FormFieldForm(initial={"is_active": True, "order": form_definition.fields.count() + 1}),
            "public_url": public_url,
            "website": getattr(self.company, "builder_website", None),
            "sections": Section.objects.filter(layout__page__website__company=self.company, is_active=True).select_related("layout__page"),
        })
        return context


class DashboardFormUpdateView(CompanyFormsAccessMixin, View):
    def post(self, request, company_id, form_id):
        company = self.get_company()
        form_definition = get_object_or_404(FormDefinition, pk=form_id, company=company)
        form = FormDefinitionForm(request.POST, company=company, instance=form_definition)
        if form.is_valid():
            form.save()
            messages.success(request, "Formulario actualizado.")
        else:
            messages.error(request, "Revisa los datos del formulario.")
        return redirect("dashboard-form-builder-detail", company_id=company.id, form_id=form_definition.id)


class DashboardFormDeleteView(CompanyFormsAccessMixin, View):
    def post(self, request, company_id, form_id):
        company = self.get_company()
        form_definition = get_object_or_404(FormDefinition, pk=form_id, company=company)
        form_definition.delete()
        messages.success(request, "Formulario eliminado.")
        return redirect("dashboard-form-builder-list", company_id=company.id)


class DashboardFieldCreateView(CompanyFormsAccessMixin, View):
    def post(self, request, company_id, form_id):
        company = self.get_company()
        form_definition = get_object_or_404(FormDefinition, pk=form_id, company=company)
        form = FormFieldForm(request.POST)
        if form.is_valid():
            field = form.save(commit=False)
            field.form = form_definition
            field.save()
            messages.success(request, "Campo creado.")
        else:
            messages.error(request, "No se pudo crear el campo. Revisa tipo y opciones.")
        return redirect("dashboard-form-builder-detail", company_id=company.id, form_id=form_definition.id)


class DashboardFieldUpdateView(CompanyFormsAccessMixin, View):
    def post(self, request, company_id, form_id, field_id):
        company = self.get_company()
        form_definition = get_object_or_404(FormDefinition, pk=form_id, company=company)
        field = get_object_or_404(FormField, pk=field_id, form=form_definition)
        form = FormFieldForm(request.POST, instance=field)
        if form.is_valid():
            form.save()
            messages.success(request, "Campo actualizado.")
        else:
            messages.error(request, "No se pudo actualizar el campo.")
        return redirect("dashboard-form-builder-detail", company_id=company.id, form_id=form_definition.id)


class DashboardFieldDeleteView(CompanyFormsAccessMixin, View):
    def post(self, request, company_id, form_id, field_id):
        company = self.get_company()
        form_definition = get_object_or_404(FormDefinition, pk=form_id, company=company)
        field = get_object_or_404(FormField, pk=field_id, form=form_definition)
        field.delete()
        messages.success(request, "Campo eliminado.")
        return redirect("dashboard-form-builder-detail", company_id=company.id, form_id=form_definition.id)


class DashboardAttachFormToSectionView(CompanyFormsAccessMixin, View):
    def post(self, request, company_id, form_id):
        company = self.get_company()
        form_definition = get_object_or_404(FormDefinition, pk=form_id, company=company)
        section = get_object_or_404(Section, pk=request.POST.get("section_id"), layout__page__website__company=company)
        settings = section.settings or {}
        settings["form_id"] = form_definition.id
        section.settings = settings
        section.section_type = "contact_form"
        section.save(update_fields=["settings", "section_type", "updated_at"])
        messages.success(request, "Formulario integrado en la seccion seleccionada.")
        return redirect("dashboard-form-builder-detail", company_id=company.id, form_id=form_definition.id)


class PublicFormDetailView(DetailView):
    template_name = "forms_builder/public/form_detail.html"
    context_object_name = "form_definition"

    def get_object(self, queryset=None):
        return get_object_or_404(
            FormDefinition.objects.select_related("company").prefetch_related("fields"),
            company__slug=self.kwargs["company_slug"],
            slug=self.kwargs["form_slug"],
            is_active=True,
            company__is_active=True,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submission_form"] = PublicFormSubmissionForm(self.object)
        context["status"] = self.request.GET.get("form_status", "")
        return context


class PublicFormSubmitView(View):
    def post(self, request, company_slug, form_slug):
        form_definition = get_object_or_404(
            FormDefinition.objects.select_related("company").prefetch_related("fields"),
            company__slug=company_slug,
            slug=form_slug,
            is_active=True,
            company__is_active=True,
        )
        submission_form = PublicFormSubmissionForm(form_definition, request.POST)
        next_url = self.safe_next(request.POST.get("next") or reverse("forms-builder-public-detail", kwargs={"company_slug": company_slug, "form_slug": form_slug}))
        status_param = "sent"
        if submission_form.is_valid():
            data, sender_name, sender_email = submission_form.cleaned_submission_data()
            submission = FormSubmission.objects.create(
                form=form_definition,
                data=data,
                sender_name=sender_name,
                sender_email=sender_email,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
            )
            send_submission_email(submission)
        else:
            status_param = "error"
        separator = "&" if "?" in next_url else "?"
        return redirect(f"{next_url}{separator}form_status={status_param}&form_id={form_definition.id}#cardbook-form-{form_definition.id}")

    def safe_next(self, next_url):
        if not next_url:
            return "/"
        parsed = urlparse(next_url)
        if parsed.scheme or parsed.netloc:
            return parsed.path or "/"
        return next_url
