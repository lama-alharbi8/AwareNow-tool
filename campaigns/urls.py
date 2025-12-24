from django.urls import path
from . import views

app_name = "campaigns"

urlpatterns = [
    path("phishing/", views.phishing_list, name="phishing"),
    path("phishing/create/", views.phishing_create, name="phishing-create"),

    path("template/preview/<int:pk>/", views.template_preview, name="template-preview"),


    path("t/open/<uuid:token>.png", views.track_open, name="track-open"),
    path("t/click/<uuid:token>/", views.track_click, name="track-click"),
    path("t/fall/<uuid:token>/", views.track_fall, name="track-fall"),

    path("phishing/<int:campaign_id>/send/", views.publish_and_send, name="publish-send"),
    path("phishing/<int:campaign_id>/report/", views.phishing_report, name="phishing-report"),

    # ===== Platform Admin: Email Templates =====
    path("templates/", views.templates_dashboard, name="templates_dashboard"),
    path("templates/create/", views.create_template, name="create_template"),
    path("templates/<int:template_id>/edit/", views.edit_template, name="edit_template"),
    path("templates/<int:template_id>/deactivate/", views.deactivate_template, name="deactivate_template"),
    path("templates/<int:template_id>/activate/", views.activate_template, name="activate_template"),

    # (Modal) View published companies (JSON)
    path("templates/<int:template_id>/companies/", views.template_companies_view, name="template_companies_view"),
]
