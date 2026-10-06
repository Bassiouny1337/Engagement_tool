from django import forms

from .models import ChecklistItem, Scenario


class ChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ("domain_key", "category", "title", "guidance", "order", "is_active")
        widgets = {"guidance": forms.Textarea(attrs={"rows": 3})}


class ScenarioForm(forms.ModelForm):
    class Meta:
        model = Scenario
        fields = ("title", "domain_key", "summary", "steps", "payloads",
                  "references", "tags", "is_active")
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 2}),
            "steps": forms.Textarea(attrs={"rows": 4}),
            "payloads": forms.Textarea(attrs={"rows": 3}),
            "references": forms.Textarea(attrs={"rows": 2}),
        }
