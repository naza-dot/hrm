from django import forms
from .models import Client


class ClientAdminForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for slug, label in Client.FEATURES.items():
            self.fields[f"feature_{slug}"] = forms.BooleanField(
                label=label,
                required=False,
                initial=self.instance.features.get(slug, False) if self.instance.pk else False,
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        features = {}
        for slug in Client.FEATURES:
            features[slug] = self.cleaned_data.get(f"feature_{slug}", False)
        instance.features = features
        if commit:
            instance.save()
        return instance
