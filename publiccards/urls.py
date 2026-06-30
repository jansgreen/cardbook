from django.urls import path

from .views import BusinessCardPrintView, PublicBusinessCardDetailView, PublicCardDetailView, card_qr_svg, save_to_book


urlpatterns = [
    path("book/save/", save_to_book, name="public-save-to-book"),
    path("presentacion/<slug:slug>/print/", BusinessCardPrintView.as_view(), name="public-business-card-print"),
    path("presentacion/<slug:slug>/", PublicBusinessCardDetailView.as_view(), name="public-business-card"),
    path("<slug:slug>/qr.svg", card_qr_svg, name="public-card-qr"),
    path("<slug:slug>/", PublicCardDetailView.as_view(), name="public-card-web"),
]
