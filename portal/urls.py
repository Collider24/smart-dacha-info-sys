from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", views.SignupView.as_view(), name="signup"),

    path("", views.dashboard, name="dashboard"),

    path("sensors/", views.SensorListView.as_view(), name="sensors_list"),
    path("sensors/new/", views.SensorCreateView.as_view(), name="sensors_create"),
    path("sensors/<int:pk>/edit/", views.SensorUpdateView.as_view(), name="sensors_edit"),
    path("sensors/<int:pk>/delete/", views.SensorDeleteView.as_view(), name="sensors_delete"),

    path("actuators/", views.ActuatorListView.as_view(), name="actuators_list"),
    path("actuators/new/", views.ActuatorCreateView.as_view(), name="actuators_create"),
    path("actuators/<int:pk>/edit/", views.ActuatorUpdateView.as_view(), name="actuators_edit"),
    path("actuators/<int:pk>/delete/", views.ActuatorDeleteView.as_view(), name="actuators_delete"),

    path("facilities/", views.FacilityListView.as_view(), name="facilities_list"),
    path("facilities/new/", views.FacilityCreateView.as_view(), name="facilities_create"),
    path("facilities/<int:pk>/edit/", views.FacilityUpdateView.as_view(), name="facilities_edit"),
    path("facilities/<int:pk>/delete/", views.FacilityDeleteView.as_view(), name="facilities_delete"),

    path("rules/", views.RuleListView.as_view(), name="rules_list"),
    path("rules/new/", views.RuleCreateView.as_view(), name="rules_create"),
    path("rules/<int:pk>/edit/", views.RuleUpdateView.as_view(), name="rules_edit"),
    path("rules/<int:pk>/delete/", views.RuleDeleteView.as_view(), name="rules_delete"),

    path("alerts/", views.AlertsListView.as_view(), name="alerts_list"),
    path("alerts/<int:pk>/edit/", views.AlertUpdateView.as_view(), name="alerts_edit"),
    path("alerts/<int:pk>/delete/", views.AlertDeleteView.as_view(), name="alerts_delete"),

    path("api/sensors/", views.api_sensors, name="api_sensors"),
    path("api/sensors/<int:sensor_id>/series/", views.api_sensor_series, name="api_sensor_series"),
]
