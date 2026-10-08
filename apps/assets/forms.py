from django import forms

from .constants import ASSET_TYPE_CHOICES, attribute_spec
from .models import Asset, Credential, FileArtifact, Function, Service


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ("asset_type", "name", "primary_target", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class AttributesForm(forms.Form):
    """Dynamic form for an asset's type-specific attributes."""

    def __init__(self, *args, asset_type=None, initial_attrs=None, **kwargs):
        super().__init__(*args, **kwargs)
        initial_attrs = initial_attrs or {}
        for key, label, placeholder in attribute_spec(asset_type):
            self.fields[key] = forms.CharField(
                label=label, required=False,
                initial=initial_attrs.get(key, ""),
                widget=forms.TextInput(attrs={"placeholder": placeholder}),
            )

    def as_attributes(self):
        return {k: v for k, v in self.cleaned_data.items() if v}


class WalkthroughForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ("walkthrough",)
        widgets = {"walkthrough": forms.Textarea(attrs={"rows": 16, "id": "md-input"})}


class CredentialForm(forms.ModelForm):
    secret = forms.CharField(
        required=False, widget=forms.PasswordInput(render_value=False),
        help_text="Stored encrypted. Leave blank to keep the current value.",
    )

    class Meta:
        model = Credential
        fields = ("label", "username", "kind", "notes")

    def save(self, commit=True):
        obj = super().save(commit=False)
        secret = self.cleaned_data.get("secret")
        if secret:
            obj.secret = secret
        if commit:
            obj.save()
        return obj


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ("port", "protocol", "name", "product", "version", "notes")


class FileArtifactForm(forms.ModelForm):
    class Meta:
        model = FileArtifact
        fields = ("name", "kind", "path", "sha256", "notes")


class FunctionForm(forms.ModelForm):
    class Meta:
        model = Function
        fields = ("name", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}
