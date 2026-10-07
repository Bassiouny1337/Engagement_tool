from django import forms

from .models import Page


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ("title", "parent", "content")
        widgets = {
            "content": forms.Textarea(attrs={"rows": 18, "id": "md-input"}),
        }

    def __init__(self, *args, engagement=None, **kwargs):
        super().__init__(*args, **kwargs)
        if engagement is not None:
            qs = Page.objects.filter(engagement=engagement)
            if self.instance and self.instance.pk:
                # Can't be its own parent (descendants excluded in the view).
                qs = qs.exclude(pk=self.instance.pk)
            self.fields["parent"].queryset = qs
            self.fields["parent"].required = False
