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
            return redirect('account:platform-login')
        
        # if not (request.user.is_platform_admin or request.user.is_superuser):
        #     return HttpResponseForbidden("Access denied. Platform admin privileges required.")
        if not request.user.is_superuser:
            return HttpResponseForbidden("Platform admin only.")

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
        # employees_count = EmployeeProfile.objects.filter(company=company).count()
        employees_count = EmployeeProfile.objects.filter( user__company=company).count()
        # completed_in_company = EmployeeCourseAssignment.objects.filter(
        #     employee__company=company,
        #     status='completed'
        # ).count()
        completed_in_company = EmployeeCourseAssignment.objects.filter(
            employee__user__company=company,
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
        # 'employee__user',
        # 'employee__company',
        # 'course'

        # 'employee__user__company',
        # 'course'
        'employee',
        'employee__user',
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
        # 'employee__user',
        # 'employee__company',
        # 'course'
        'employee',
        'employee__user',
        'course'
    )[:5]
    
    # ========== QUIZ PERFORMANCE ==========
    quiz_stats = QuizAttempt.objects.aggregate(
        avg_score=Avg('score'),
        total_attempts=Count('id')
    )
    
    return render(request, 'courses/dashboard.html', {
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
    # Get all existing courses for the table (only when not in edit mode)
    courses = Course.objects.all().order_by('-created_at')  # Show newest first
    
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
                return redirect('courses:assign_course_to_companies', course_id=course.id)
            else:
                return redirect('courses:platform_admin_dashboard')
    else:
        form = CourseForm()
    
    # Render with all necessary context
    return render(request, 'courses/create_course.html', {
        'form': form,
        'courses': courses,  # For the courses table
        'is_edit': False,    # Important: tells template this is create mode
    })

# ==================== COURSE EDITING ====================
@login_required
@platform_admin_required
def edit_course(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        messages.error(request, '❌ Course not found.')
        return redirect('courses:platform_admin_dashboard')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            updated_course = form.save(commit=False)
            
            # Handle publish date
            if updated_course.is_published and not updated_course.published_at:
                updated_course.published_at = timezone.now()
            
            updated_course.save()
            messages.success(request, f'✅ Course "{updated_course.title}" updated!')
            return redirect('courses:platform_admin_dashboard')
    else:
        form = CourseForm(instance=course)
    
    # Render edit template
    return render(request, 'courses/create_course.html', {
        'form': form,
        'course': course,    # Current course being edited
        'is_edit': True,     # Important: tells template this is edit mode
        # Don't need 'courses' in edit mode since table won't show
    })

@login_required
@platform_admin_required
def courses_dashboard(request):
    # Get all courses
    courses = Course.objects.all().order_by('-created_at')
    
    # Get categories with course counts
    categories = CourseCategory.objects.annotate(
        course_count=Count('course')
    )
    
    # Apply filters if provided
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    
    if status_filter:
        if status_filter == 'published':
            courses = courses.filter(is_published=True)
        elif status_filter == 'draft':
            courses = courses.filter(is_published=False)
    
    if category_filter:
        courses = courses.filter(category_id=category_filter)
    
    return render(request, 'courses/courses_dashboard.html', {
        'courses': courses,
        'categories': categories,
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
        
        return redirect('courses:platform_admin_dashboard')
    
    all_companies = Company.objects.filter(status='ACTIVE').order_by('name')
    already_assigned = course.companies.values_list('id', flat=True)
    
    return render(request, 'courses/assign_course.html', {
        'course': course,
        'all_companies': all_companies,
        'already_assigned': list(already_assigned),
        # REMOVED: 'user': request.user,  # Not needed
    })