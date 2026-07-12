from django import template

from forms_builder.forms import PublicFormSubmissionForm
from forms_builder.models import FormDefinition

register = template.Library()


@register.inclusion_tag("forms_builder/public/embed.html", takes_context=True)
def render_section_form(context, section):
    request = context.get("request")
    form_definition = None
    form_id = (section.settings or {}).get("form_id")
    queryset = FormDefinition.objects.filter(company=section.layout.page.website.company, is_active=True).prefetch_related("fields")
    if form_id:
        form_definition = queryset.filter(pk=form_id).first()
    if not form_definition:
        form_definition = queryset.order_by("name").first()
    status = request.GET.get("form_status") if request else ""
    status_form_id = request.GET.get("form_id") if request else ""
    return {
        "request": request,
        "section": section,
        "form_definition": form_definition,
        "submission_form": PublicFormSubmissionForm(form_definition) if form_definition else None,
        "status": status if str(status_form_id) == str(form_definition.id if form_definition else "") else "",
    }

