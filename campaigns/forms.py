from django import forms

from .models import PhishingCampaign, EmailTemplate
from account.models import CompanyGroup


# =====================================================
# Phishing Campaign Form (نفس فورمك – بدون أي تغيير)
# =====================================================
class PhishingCampaignForm(forms.ModelForm):
    class Meta:
        model = PhishingCampaign
        fields = [
            "title",
            "user_group",
            "sender",
            "scheduled_date",
            "template",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Campaign title"
            }),
            "user_group": forms.Select(attrs={
                "class": "form-select"
            }),
            "sender": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "sender@example.com"
            }),
            "scheduled_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "template": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        qs = CompanyGroup.objects.all().order_by("-id")

        if company:
            qs = qs.filter(company=company, is_system=False)

        self.fields["user_group"].queryset = qs
        self.fields["user_group"].empty_label = "Select user group"


# =====================================================
# Email Template Form (هذا اللي كان ناقص)
# =====================================================
class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = [
            "name",
            "subject",
            "preview_image",
            "html_content",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Template name"
            }),
            "subject": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Email subject"
            }),
            "preview_image": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),
            "html_content": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 12,
                "placeholder": "Paste HTML email content here"
            }),
        }
