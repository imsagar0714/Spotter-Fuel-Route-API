from django.urls import path
from route_planner.views import RoutePlanView

urlpatterns = [path("route-plan/", RoutePlanView.as_view(), name="route-plan")]

