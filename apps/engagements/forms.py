from django import forms

from apps.domains.constants import DOMAIN_CHOICES

from .models import Engagement, ScopeItem


class EngagementForm(forms.ModelForm):
    class Meta:
        model = Engagement
        fields = ("client", "title", "code", "start_date", "end_date", "summary")
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "summary": forms.Textarea(attrs={"rows": 3}),
        }


class AddDomainForm(forms.Form):
    domain_key = forms.ChoiceField(choices=DOMAIN_CHOICES, label="Domain")


class ScopeItemForm(forms.ModelForm):
    class Meta:
        model = ScopeItem
        fields = ("kind", "value", "domain_key", "in_scope", "notes")
