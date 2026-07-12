from django.urls import path

from .views import PublicSiteView


urlpatterns = [
    path("<slug:website_slug>/", PublicSiteView.as_view(), name="websitebuilder-public-home"),
    path("<slug:website_slug>/<slug:page_slug>/", PublicSiteView.as_view(), name="websitebuilder-public-page"),
]

