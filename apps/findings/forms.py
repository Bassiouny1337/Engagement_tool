from django import forms

from .models import Finding


class FindingForm(forms.ModelForm):
    class Meta:
        model = Finding
        fields = (
            "title", "domain_key", "severity", "status",
            "cvss_vector", "cvss_score", "affected",
            "description", "impact", "remediation", "references",
        )
        widgets = {
            "affected": forms.Textarea(attrs={"rows": 2}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "impact": forms.Textarea(attrs={"rows": 3}),
            "remediation": forms.Textarea(attrs={"rows": 3}),
            "references": forms.Textarea(attrs={"rows": 2}),
        }
