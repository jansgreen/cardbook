from django.urls import path

from .views import PushDeviceDisableView, PushDeviceListCreateView, PushTestView

urlpatterns = [
    path("devices/", PushDeviceListCreateView.as_view(), name="push-devices"),
    path("devices/disable/", PushDeviceDisableView.as_view(), name="push-device-disable"),
    path("test/", PushTestView.as_view(), name="push-test"),
]
