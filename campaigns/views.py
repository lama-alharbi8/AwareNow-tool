from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import HttpResponse
from django.template import Template, Context

from .models import PhishingCampaign, EmailTemplate
from .forms import PhishingCampaignForm


@login_required
def phishing_list(request):
    q = request.GET.get("q", "").strip()

    campaigns = PhishingCampaign.objects.all().order_by("-created_at")

    if q:
        campaigns = campaigns.filter(
            Q(title__icontains=q) |
            Q(sender__icontains=q) |
            Q(user_group__icontains=q)
        )

    active_campaign = campaigns.filter(status="published").first()
    completed_campaigns = campaigns.filter(status="completed")[:8]

    context = {
        "q": q,
        "active_campaign": active_campaign,
        "completed_campaigns": completed_campaigns,
    }
    return render(request, "campaigns/phishing/phishing_list.html", context)


@login_required
def phishing_create(request):
    templates = EmailTemplate.objects.filter(is_active=True).order_by("-created_at")

    if request.method == "POST":
        form = PhishingCampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)

            # ✅ تأكد أن التيمبلت المختارة موجودة وفعالة
            if campaign.template_id:
                is_ok = EmailTemplate.objects.filter(
                    id=campaign.template_id,
                    is_active=True
                ).exists()
                if not is_ok:
                    form.add_error("template", "Selected template is invalid.")
                    return render(request, "campaigns/phishing/phishing_create.html", {
                        "form": form,
                        "templates": templates,
                    })
            else:
                form.add_error("template", "Please select a template.")
                return render(request, "campaigns/phishing/phishing_create.html", {
                    "form": form,
                    "templates": templates,
                })

            campaign.save()
            return redirect("campaigns:phishing")
    else:
        form = PhishingCampaignForm()

    return render(request, "campaigns/phishing/phishing_create.html", {
        "form": form,
        "templates": templates,
    })


@login_required
def template_preview(request, pk):
    """
    يعرض HTML template (مع placeholders) كـ preview في المتصفح.
    ملاحظة: هذا Preview فقط. التراكنق الحقيقي بنربطه لاحقًا.
    """
    t = get_object_or_404(EmailTemplate, pk=pk, is_active=True)

    ctx = Context({
        "first_name": "John",
        "company": "@ContosoCorp",
        "invoice_id": "10492",
        "decision_date": "Mon Dec 22 2025 09:17:41 GMT+0300 (Arabian Standard Time)",
        "tracking_url": "#",  # لاحقاً: رابط click tracking
    })

    rendered_html = Template(t.html_content).render(ctx)
    return HttpResponse(rendered_html, content_type="text/html; charset=utf-8")


# =========================
# Tracking Views (Open/Click/Fall)
# =========================

@login_required
def track_open(request, token):
    """
    Open tracking:
    يُستدعى من صورة 1x1 داخل الإيميل
    """
    # لاحقاً: نخزن token + وقت الفتح + اليوزر
    # حالياً: بس نرجّع pixel (gif 1x1)
    pixel = (
        b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00"
        b"\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00"
        b"\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00"
        b"\x00\x02\x02\x44\x01\x00\x3b"
    )
    return HttpResponse(pixel, content_type="image/gif")


@login_required
def track_click(request, token):
    """
    Click tracking:
    أي زر أو رابط داخل الإيميل يمر من هنا
    """
    # لاحقاً: نسجل click event + نعيد توجيه للرابط الحقيقي
    return redirect("campaigns:phishing")


@login_required
def track_fall(request, token):
    """
    Fall for phishing:
    اليوزر دخل صفحة مزيفة (مثلاً fake login)
    """
    # لاحقاً: نخزن fall=True + تفاصيل أكثر
    return HttpResponse(
        "<h2>Access Recorded</h2><p>This action has been logged.</p>",
        content_type="text/html; charset=utf-8"
    )
