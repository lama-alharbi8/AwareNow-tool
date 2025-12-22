from django.contrib import admin
from .models import EmailTemplate, PhishingCampaign

admin.site.register(EmailTemplate)
admin.site.register(PhishingCampaign)
