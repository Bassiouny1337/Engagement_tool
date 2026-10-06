from django import forms


class ScanUploadForm(forms.Form):
    file = forms.FileField(
        label="Nmap XML (-oX output)",
        help_text="Upload the XML produced by `nmap -oX scan.xml …` (max 25 MB).",
    )
