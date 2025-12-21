from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    CourseCategory, Course, CompanyCourseAssignment,  # Make sure Course is imported
    CompanyCourseGroup, Quiz, QuizQuestion, EmployeeCourseAssignment
)

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color_display', 'course_count')
    list_filter = ('icon',)
    search_fields = ('name', 'description')
    
    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<span style="display:inline-block; width:20px; height:20px; '
                'background-color:{}; border:1px solid #ccc;"></span> {}',
                obj.color, obj.color
            )
        return "-"
    color_display.short_description = 'Color'
    
    def course_count(self, obj):
        # This requires Course model to be imported
        from .models import Course  # Add this line
        return Course.objects.filter(category=obj).count()
    course_count.short_description = 'Courses'

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'created_by', 'is_published', 
        'visibility', 'created_at'  # REMOVED: 'actions' - this might be causing error
    )
    list_filter = ('is_published', 'visibility', 'category', 'created_at')
    search_fields = ('title', 'brief_description', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at', 'published_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'brief_description', 'category', 'thumbnail')
        }),
        ('Content', {
            'fields': ('video_url', 'video_duration_minutes')
        }),
        ('Settings', {
            'fields': ('visibility', 'points_reward', 'is_published')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',),
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        if obj.is_published and not obj.published_at:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)

@admin.register(CompanyCourseAssignment)
class CompanyCourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ('company', 'course', 'assigned_by', 'assigned_at')
    list_filter = ('company', 'course')
    readonly_fields = ('assigned_at',)

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'passing_score', 'time_limit_minutes')

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'question_text_short', 'question_type', 'points')
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'