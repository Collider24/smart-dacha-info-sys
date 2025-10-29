from django import forms
from core.models import Alert

class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ["rule", "started_at", "message"]
        widgets = {
            "started_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "message": forms.Textarea(attrs={"rows": 3}),
        }
