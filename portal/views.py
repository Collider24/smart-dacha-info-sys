from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from core.models import Sensor, Actuator, Facility, Rule, Alert
from core import influx
from django.views.decorators.http import require_GET
import logging

from portal.forms import AlertForm

log = logging.getLogger(__name__)

User = get_user_model()

class LoginView(View):
    def get(self, request):
        return render(request, "portal/login.html", {"form": AuthenticationForm()})
    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("portal:dashboard")
        messages.error(request, "Неверные данные")
        return render(request, "portal/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("portal:login")

class SignupView(View):
    def get(self, request):
        return render(request, "portal/signup.html", {"form": UserCreationForm()})
    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("portal:dashboard")
        return render(request, "portal/signup.html", {"form": form})

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("portal:login")
    alerts_recent = (
        Alert.objects.select_related('rule')
        .order_by('-started_at')[:10]
    )

    active_sensors = list(
        Sensor.objects.filter(is_active=True)
        .select_related('facility', 'unit')
        .values('id', 'name', 'facility__name', 'unit__code')
        .order_by('facility__name', 'name')
    )

    ctx = {
        "sensors_active_count" : f"{Sensor.objects.filter(is_active=True).count()}/{Sensor.objects.count()}",
        "sensors_count": Sensor.objects.count(),
        "actuators_active_count": f"{Actuator.objects.filter(is_active=True).count()}/{Actuator.objects.count()}",
        "actuators_count": Actuator.objects.count(),
        "facilities_count": Facility.objects.count(),
        "rules_count": Rule.objects.count(),
        "alerts_recent": alerts_recent,
        'active_sensors': active_sensors,
    }
    return render(request, "portal/dashboard.html", ctx)

class SensorListView(LoginRequiredMixin, ListView):
    model = Sensor
    template_name = "portal/sensors_list.html"
    paginate_by = 20
    ordering = ["facility__name", "name"]

class SensorCreateView(LoginRequiredMixin, CreateView):
    model = Sensor
    fields = ["user", "facility", "name", "unit", "min_val", "max_val",
              "sampling_s", "is_active"]
    template_name = "portal/form.html"
    success_url = reverse_lazy("portal:sensors_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Добавить датчик"
        return ctx

class SensorUpdateView(LoginRequiredMixin, UpdateView):
    model = Sensor
    fields = ["user", "facility", "name", "unit", "min_val", "max_val",
              "sampling_s", "is_active"]
    template_name = "portal/form.html"
    success_url = reverse_lazy("portal:sensors_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # можно и так: f"Править датчик: {self.object.name}"
        ctx["page_title"] = "Править датчик"
        return ctx


class SensorDeleteView(LoginRequiredMixin, DeleteView):
    model = Sensor
    template_name = "portal/confirm_delete.html"
    success_url = reverse_lazy("portal:sensors_list")

class ActuatorListView(LoginRequiredMixin, ListView):
    model = Actuator
    template_name = "portal/actuators_list.html"
    paginate_by = 40
    ordering = ["facility__name", "name"]

class ActuatorCreateView(LoginRequiredMixin, CreateView):
    model = Actuator
    fields = ["facility", "name", "type", "range_min", "range_max", "step", "is_active"]
    template_name = "portal/form.html"
    success_url = reverse_lazy("portal:actuators_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Добавить привод"
        return ctx

class ActuatorUpdateView(LoginRequiredMixin, UpdateView):
    model = Actuator
    fields = ["facility", "name", "type", "range_min", "range_max", "step", "is_active", "current_value"]
    template_name = "portal/form.html"
    success_url = reverse_lazy("portal:actuators_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Править привод"
        return ctx


class ActuatorDeleteView(LoginRequiredMixin, DeleteView):
    model = Actuator
    template_name = "portal/confirm_delete.html"
    success_url = reverse_lazy("portal:actuators_list")

class FacilityListView(LoginRequiredMixin, ListView):
    model = Facility
    template_name = "portal/facilities_list.html"
    paginate_by = 20
    ordering = ["name"]

class FacilityCreateView(LoginRequiredMixin, CreateView):
    model = Facility
    fields = ["name", "type"]
    template_name = "portal/form.html"
    success_url = reverse_lazy("portal:facilities_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Добавить постройку"
        return ctx

class FacilityUpdateView(LoginRequiredMixin, UpdateView):
    model = Facility
    fields = ["name", "type"]
    template_name = "portal/form.html"
    success_url = reverse_lazy("portal:facilities_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Править постройку"
        return ctx

class FacilityDeleteView(LoginRequiredMixin, DeleteView):
    model = Facility
    template_name = "portal/confirm_delete.html"
    success_url = reverse_lazy("portal:facilities_list")

class RuleListView(LoginRequiredMixin, ListView):
    model = Rule
    template_name = "portal/rules_list.html"
    paginate_by = 20
    ordering = ["-created_at"]

class RuleCreateView(LoginRequiredMixin, CreateView):
    model = Rule
    fields = ["user", "name", "expr", "window_s", "severity", "enabled"]
    template_name = "portal/form.html"
    success_url = reverse_lazy("portal:rules_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Добавить правило"
        return ctx


class RuleUpdateView(LoginRequiredMixin, UpdateView):
    model = Rule
    fields = ["user", "name", "expr", "window_s", "severity", "enabled"]
    template_name = "portal/form.html"
    success_url = reverse_lazy("portal:rules_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Править правило"
        return ctx

class RuleDeleteView(LoginRequiredMixin, DeleteView):
    model = Rule
    template_name = "portal/confirm_delete.html"
    success_url = reverse_lazy("portal:rules_list")

class AlertsListView(ListView):
    model = Alert
    template_name = "portal/alerts_list.html"
    context_object_name = "object_list"
    paginate_by = 20

    def get_queryset(self):
        return (
            Alert.objects.select_related("rule")
            .order_by("-started_at")
        )

class AlertUpdateView(UpdateView):
    model = Alert
    form_class = AlertForm
    template_name = "portal/form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Правка оповещения"
        return ctx

    def get_success_url(self):
        return reverse_lazy("portal:alerts_list")

class AlertDeleteView(DeleteView):
    model = Alert
    template_name = "portal/confirm_delete.html"
    success_url = reverse_lazy("portal:alerts_list")


def api_sensors(request):
    data = list(Sensor.objects.filter(is_active=True)
                .order_by("facility__name","name")
                .values("id","name","facility__name"))
    return JsonResponse({"sensors": data})


@require_GET
def api_sensor_series(request, sensor_id: int):
    rng = request.GET.get("range", "24h")
    from django.conf import settings
    flux = f'''
from(bucket: "{settings.INFLUX_BUCKET}")
  |> range(start: -{rng})
  |> filter(fn: (r) => r["_measurement"] == "{influx.MEASUREMENT}")
  |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
  |> filter(fn: (r) => r["_field"] == "value")
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"])
'''
    tables = influx._query.query(flux, org=settings.INFLUX_ORG)
    series = []
    for tbl in tables:
        for rec in tbl.records:
            ts_ms = int(rec.get_time().timestamp() * 1000)
            series.append({"t": ts_ms, "v": rec.get_value()})
    return JsonResponse({"series": series})
