from django.urls import path

from .views import SupportTicketListCreateView

urlpatterns = [
    path("tickets/", SupportTicketListCreateView.as_view(), name="support-tickets"),
]
