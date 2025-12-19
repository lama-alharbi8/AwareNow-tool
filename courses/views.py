from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.db.models import Avg, Count, Q
# Remove: from datetime import datetime, timedelta  # Don't need datetime anymore

from account.models import Company, EmployeeProfile
from courses.models import Course, CourseCategory, CompanyCourseAssignment, EmployeeCourseAssignment, QuizAttempt
from courses.forms import CourseForm


# ==================== PERMISSION CHECK ====================
def platform_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin:login')
        
        if not (request.user.is_platform_admin or request.user.is_superuser):
            return HttpResponseForbidden("Access denied. Platform admin privileges required.")
        
        return view_func(request, *args, **kwargs)
    return wrapper

# ==================== SIMPLIFIED DASHBOARD ====================
@login_required
@platform_admin_required
def platform_admin_dashboard(request):
    # ========== BASIC COURSE STATS ==========
    total_courses = Course.objects.count()
    published_courses = Course.objects.filter(is_published=True).count()
    total_companies = Company.objects.filter(status='ACTIVE').count()
    
    recent_courses = Course.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    
    # ========== SIMPLE EMPLOYEE PROGRESS ==========
    assigned_count = EmployeeCourseAssignment.objects.filter(status='assigned').count()
    in_progress_count = EmployeeCourseAssignment.objects.filter(status='in_progress').count()
    completed_count = EmployeeCourseAssignment.objects.filter(status='completed').count()
    total_assignments = EmployeeCourseAssignment.objects.count()
    
    completion_rate = (completed_count / total_assignments * 100) if total_assignments > 0 else 0
    
    # FIXED: Use timezone.now() instead of datetime.now()
    overdue_count = EmployeeCourseAssignment.objects.filter(
        due_date__lt=timezone.now().date(),  # FIXED HERE
        status__in=['assigned', 'in_progress']
    ).count()
    
    # ========== COMPANY SUMMARY ==========
    companies = Company.objects.filter(status='ACTIVE')[:5]
    company_summary = []
    
    for company in companies:
        employees_count = EmployeeProfile.objects.filter(company=company).count()
        completed_in_company = EmployeeCourseAssignment.objects.filter(
            employee__company=company,
            status='completed'
        ).count()
        
        company_summary.append({
            'name': company.name,
            'employee_count': employees_count,
            'completed_courses': completed_in_company,
        })
    
    # ========== RECENT COMPLETIONS ==========
    recent_completions = EmployeeCourseAssignment.objects.filter(
        status='completed'
    ).select_related(
        'employee__user',
        'employee__company',
        'course'
    ).order_by('-completed_at')[:10]
    
    simple_completions = []
    for assignment in recent_completions:
        simple_completions.append({
            'employee_email': assignment.employee.user.email,
            'company': assignment.employee.company.name if assignment.employee.company else 'N/A',
            'course': assignment.course.title,
            'completed_date': assignment.completed_at.date() if assignment.completed_at else 'N/A',
        })
    
    # ========== OVERDUE LIST (SIMPLE) ==========
    # FIXED: Use timezone.now() here too
    overdue_list = EmployeeCourseAssignment.objects.filter(
        due_date__lt=timezone.now().date(),  # FIXED HERE
        status__in=['assigned', 'in_progress']
    ).select_related(
        'employee__user',
        'employee__company',
        'course'
    )[:5]
    
    # ========== QUIZ PERFORMANCE ==========
    quiz_stats = QuizAttempt.objects.aggregate(
        avg_score=Avg('score'),
        total_attempts=Count('id')
    )
    
    return render(request, 'courses/platform_admin/dashboard.html', {
        # Basic stats
        'total_courses': total_courses,
        'published_courses': published_courses,
        'total_companies': total_companies,
        'recent_courses': recent_courses,
        # REMOVED: 'user': request.user,  # Not needed
        
        # Simple progress stats
        'assigned_count': assigned_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'total_assignments': total_assignments,
        'completion_rate': round(completion_rate, 1),
        'overdue_count': overdue_count,
        
        # Company summary
        'company_summary': company_summary,
        
        # Recent completions
        'recent_completions': simple_completions,
        
        # Overdue list
        'overdue_list': overdue_list,
        
        # Quiz stats - IMPROVED: Use .get() for safety
        'avg_quiz_score': round(quiz_stats.get('avg_score') or 0, 1),
        'total_quiz_attempts': quiz_stats.get('total_attempts') or 0,
    })

# ==================== COURSE CREATION ====================
@login_required
@platform_admin_required
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user
            
            if course.is_published and not course.published_at:
                course.published_at = timezone.now()
            
            course.save()
            messages.success(request, f'✅ Course "{course.title}" created!')
            
            if 'save_and_assign' in request.POST:
                return redirect('assign_course_to_companies', course_id=course.id)
            else:
                return redirect('platform_admin_dashboard')
    else:
        form = CourseForm()
    
    return render(request, 'courses/platform_admin/create_course.html', {
        'form': form,
        # REMOVED: 'user': request.user,  # Not needed
    })

# ==================== COURSE EDITING ====================
@login_required
@platform_admin_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if not (request.user == course.created_by or request.user.is_superuser):
        messages.error(request, 'You can only edit courses you created.')
        return redirect('platform_admin_dashboard')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            updated_course = form.save()
            messages.success(request, f'✅ Course "{updated_course.title}" updated!')
            return redirect('platform_admin_dashboard')
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'courses/platform_admin/create_course.html', {
        'form': form,
        'course': course,
        'is_edit': True,
        # REMOVED: 'user': request.user,  # Not needed
    })

# ==================== COURSE ASSIGNMENT ====================
@login_required
@platform_admin_required
def assign_course_to_companies(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        company_ids = request.POST.getlist('companies')
        assigned_count = 0
        
        for company_id in company_ids:
            try:
                company = Company.objects.get(id=company_id, status='ACTIVE')
                
                if not CompanyCourseAssignment.objects.filter(
                    company=company, course=course
                ).exists():
                    CompanyCourseAssignment.objects.create(
                        company=company,
                        course=course,
                        assigned_by=request.user
                    )
                    assigned_count += 1
                    
            except Company.DoesNotExist:
                continue
        
        if assigned_count > 0:
            messages.success(request, f'✅ Course assigned to {assigned_count} company(s)')
        else:
            messages.info(request, 'No new companies assigned.')
        
        return redirect('platform_admin_dashboard')
    
    all_companies = Company.objects.filter(status='ACTIVE').order_by('name')
    already_assigned = course.companies.values_list('id', flat=True)
    
    return render(request, 'courses/platform_admin/assign_course.html', {
        'course': course,
        'all_companies': all_companies,
        'already_assigned': list(already_assigned),
        # REMOVED: 'user': request.user,  # Not needed
    })