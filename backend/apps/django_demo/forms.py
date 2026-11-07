"""Unit IV demo: a Django Form with server-side validation."""
from django import forms

BUILDINGS = [("", "Select a building"), ("Block-A", "Block A"), ("Block-B", "Block B"), ("Library", "Central Library"), ("Hostel-1", "Hostel 1")]


class DemoFeedbackForm(forms.Form):
    name = forms.CharField(max_length=60)
    building = forms.ChoiceField(choices=BUILDINGS)
    urgency = forms.IntegerField(min_value=1, max_value=5, help_text="1 = low, 5 = very urgent")
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), min_length=10, max_length=500)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name.replace(" ", "").isalpha():
            raise forms.ValidationError("Name may contain letters and spaces only.")
        return name

    def clean(self):
        cleaned = super().clean()
        # cross-field validation example
        if cleaned.get("urgency") == 5 and len(cleaned.get("message", "")) < 30:
            self.add_error("message", "Very urgent reports need at least 30 characters of detail.")
        return cleaned


class BuildingPreferenceForm(forms.Form):
    building = forms.ChoiceField(choices=BUILDINGS[1:])
