# courses/test_models.py
import os
import django
import sys
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AwareNow_Project.settings')
django.setup()

from django.contrib.auth import get_user_model
from account.models import Company, SubscriptionPlan, EmployeeProfile
from courses.models import (
    CourseCategory, Course, CompanyCourseAssignment, 
    CompanyCourseGroup, EmployeeCourseAssignment,
    EmployeeCourseProgress, Quiz, QuizQuestion, QuizAttempt,
    CourseCompletionCertificate
)

User = get_user_model()

def test_all_models():
    """Test the complete course journey with your current models"""
    print("=" * 60)
    print("TESTING COURSE MODELS WITH YOUR ACCOUNT MODELS")
    print("=" * 60)
    
    try:
        # Step 1: Create Subscription Plan
        print("\n1. Creating Subscription Plan...")
        plan, created = SubscriptionPlan.objects.get_or_create(
            name='Basic',
            defaults={
                'max_users': 50,
                'price': 99.99,
                'has_platform_support': False
            }
        )
        print(f"   Plan: {plan.name} (Max users: {plan.max_users})")
        
        # Step 2: Create Company
        print("\n2. Creating Company...")
        company, created = Company.objects.get_or_create(
            name='Test Company Ltd',
            defaults={
                'email_domain': 'testcompany.com',
                'subscription_plan': plan,
                'license_start_date': '2024-01-01',
                'license_end_date': '2025-12-31',
                'status': 'ACTIVE'
            }
        )
        print(f"   Company: {company.name}")
        print(f"   Domain: {company.email_domain}")
        print(f"   Status: {company.status}")
        
        # Step 3: Create Platform Admin (no company)
        print("\n3. Creating Platform Admin...")
        platform_admin, created = User.objects.get_or_create(
            username='platform_admin',
            defaults={
                'email': 'admin@platform.com',
                'first_name': 'Platform',
                'last_name': 'Admin',
                'role': 'PLATFORM_ADMIN',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            platform_admin.set_password('password123')
            platform_admin.save()
            print("   Created Platform Admin")
        
        # Test platform admin properties
        print(f"   Is platform admin: {platform_admin.is_platform_admin}")
        print(f"   Is company admin: {platform_admin.is_company_admin}")
        print(f"   Is employee: {platform_admin.is_employee}")
        
        # Step 4: Create Company Admin
        print("\n4. Creating Company Admin...")
        company_admin, created = User.objects.get_or_create(
            username='company_admin',
            defaults={
                'email': 'admin@testcompany.com',
                'first_name': 'Company',
                'last_name': 'Admin',
                'role': 'COMPANY_ADMIN',
                'company': company,
                'department': 'Management'
            }
        )
        if created:
            company_admin.set_password('password123')
            company_admin.save()
            print("   Created Company Admin")
        
        # Test company admin properties
        print(f"   Is platform admin: {company_admin.is_platform_admin}")
        print(f"   Is company admin: {company_admin.is_company_admin}")
        print(f"   Is employee: {company_admin.is_employee}")
        print(f"   Department: {company_admin.department}")
        
        # Step 5: Create Employee User
        print("\n5. Creating Employee User...")
        employee_user, created = User.objects.get_or_create(
            username='employee1',
            defaults={
                'email': 'john.doe@testcompany.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'EMPLOYEE',
                'company': company,
                'department': 'IT Department',
                'phone_number': '+966501234567',
                'job_title': 'Security Analyst'
            }
        )
        if created:
            employee_user.set_password('password123')
            employee_user.save()
            print("   Created Employee User")
        
        # Test employee properties
        print(f"   Is employee: {employee_user.is_employee}")
        print(f"   Job title: {employee_user.job_title}")
        print(f"   Phone: {employee_user.phone_number}")
        
        # Step 6: Create Employee Profile
        print("\n6. Creating Employee Profile...")
        employee_profile, created = EmployeeProfile.objects.get_or_create(
            user=employee_user,
            defaults={
                'employee_id': 'EMP-001'
            }
        )
        print(f"   Employee Profile: {employee_profile}")
        print(f"   Employee ID: {employee_profile.employee_id}")
        print(f"   Company (from profile): {employee_profile.company}")
        print(f"   Department (from profile): {employee_profile.department}")
        
        # Test EmployeeProfile methods
        print("\n7. Testing EmployeeProfile calculations...")
        employee_profile.completed_courses_count = 3
        employee_profile.average_quiz_score = 85.0
        employee_profile.phishing_tests_taken = 5
        employee_profile.phishing_tests_passed = 4
        employee_profile.save()  # This triggers calculate_awareness_score()
        
        print(f"   Awareness score: {employee_profile.awareness_score}")
        print(f"   Phishing pass rate: {(employee_profile.phishing_tests_passed/employee_profile.phishing_tests_taken)*100:.1f}%")
        
        # Step 7: Create Course Category
        print("\n8. Creating Course Category...")
        category = CourseCategory.objects.create(
            name='Phishing Awareness',
            description='Learn to identify and avoid phishing attacks',
            icon='fish',
            color='#e74c3c'
        )
        print(f"   Category: {category.name}")
        print(f"   Icon: {category.icon}")
        print(f"   Color: {category.color}")
        
        # Step 8: Create Course
        print("\n9. Platform Admin creates Course...")
        course = Course.objects.create(
            title='Introduction to Phishing Attacks',
            brief_description='Learn how to identify phishing emails, avoid suspicious links, and protect your personal and company information from cyber threats.',
            category=category,
            created_by=platform_admin,
            visibility='specific',
            is_published=True,
            points_reward=150,
            video_url='https://example.com/video/phishing-course',
            video_duration_minutes=45
        )
        print(f"   Course: {course.title}")
        print(f"   Created by: {course.created_by}")
        print(f"   Points reward: {course.points_reward}")
        print(f"   Thumbnail: {course.thumbnail.name}")
        
        # Test course thumbnail
        print(f"   Has thumbnail: {bool(course.thumbnail)}")
        
        # Step 9: Assign Course to Company
        print("\n10. Platform Admin assigns Course to Company...")
        company_assignment = CompanyCourseAssignment.objects.create(
            company=company,
            course=course,
            assigned_by=platform_admin
        )
        print(f"   Assignment: {company.company} - {course.title}")
        print(f"   Assigned by: {company_assignment.assigned_by}")
        
        # Step 10: Create Course Group
        print("\n11. Company Admin creates Course Group...")
        course_group = CompanyCourseGroup.objects.create(
            company=company,
            name='Q1 2024 Security Training',
            description='Mandatory security awareness training for all employees',
            created_by=company_admin
        )
        course_group.courses.add(course)
        print(f"   Group: {course_group.name}")
        print(f"   Courses in group: {course_group.courses.count()}")
        
        # Step 11: Assign Course to Employee
        print("\n12. Assigning Course to Employee...")
        employee_assignment = EmployeeCourseAssignment.objects.create(
            employee=employee_profile,  # Using EmployeeProfile
            course=course,
            assigned_by=company_admin,
            due_date=datetime.now().date() + timedelta(days=30),
            status='assigned'
        )
        print(f"   Employee Assignment: {employee_assignment}")
        print(f"   Due date: {employee_assignment.due_date}")
        print(f"   Status: {employee_assignment.status}")
        
        # Add employee to group
        course_group.assigned_to_employees.add(employee_profile)
        print(f"   Employees in group: {course_group.assigned_to_employees.count()}")
        
        # Step 12: Create Employee Progress
        print("\n13. Creating Employee Progress...")
        progress = EmployeeCourseProgress.objects.create(
            assignment=employee_assignment,
            video_total_seconds=2700,  # 45 minutes
            required_watch_percentage=80,
            required_quiz_score=70
        )
        
        # Simulate watching video
        progress.video_watched_seconds = 1350  # Watched 50%
        progress.total_time_spent = 1500  # 25 minutes spent
        progress.save()
        
        # Update assignment progress
        watch_percentage = (progress.video_watched_seconds / progress.video_total_seconds) * 100
        employee_assignment.progress_percentage = watch_percentage
        employee_assignment.status = 'in_progress'
        employee_assignment.started_at = datetime.now()
        employee_assignment.save()
        
        print(f"   Progress: {employee_assignment.progress_percentage:.1f}%")
        print(f"   Status: {employee_assignment.status}")
        
        # Step 13: Create Quiz
        print("\n14. Creating Quiz...")
        quiz = Quiz.objects.create(
            course=course,
            title='Phishing Awareness Assessment',
            description='Test your understanding of phishing threats and prevention',
            passing_score=70,
            time_limit_minutes=30,
            max_attempts=2
        )
        print(f"   Quiz: {quiz.title}")
        print(f"   Passing score: {quiz.passing_score}%")
        
        # Add quiz questions
        questions = [
            {
                'question_text': 'Which of the following is a common sign of a phishing email?',
                'question_type': 'multiple_choice',
                'option_a': 'Personalized greeting with your full name',
                'option_b': 'Urgent request for immediate action',
                'option_c': 'Official company logo in the header',
                'option_d': 'Professional email signature',
                'correct_answers': 'B',
                'points': 10,
                'explanation': 'Phishing emails often create a sense of urgency to prompt quick action without thinking.'
            },
            {
                'question_text': 'What should you do if you receive a suspicious email?',
                'question_type': 'multiple_select',
                'option_a': 'Click on links to verify',
                'option_b': 'Report it to your IT department',
                'option_c': 'Forward it to coworkers as a warning',
                'option_d': 'Delete it immediately',
                'correct_answers': 'B,D',
                'points': 15,
                'explanation': 'Always report suspicious emails and avoid clicking links or forwarding potentially harmful content.'
            }
        ]
        
        for i, q_data in enumerate(questions, 1):
            question = QuizQuestion.objects.create(
                quiz=quiz,
                question_text=q_data['question_text'],
                question_type=q_data['question_type'],
                option_a=q_data.get('option_a', ''),
                option_b=q_data.get('option_b', ''),
                option_c=q_data.get('option_c', ''),
                option_d=q_data.get('option_d', ''),
                correct_answers=q_data['correct_answers'],
                points=q_data['points'],
                explanation=q_data['explanation'],
                order=i
            )
            print(f"   Question {i}: {question.question_text[:60]}...")
        
        # Step 14: Employee takes Quiz
        print("\n15. Employee takes Quiz...")
        quiz_attempt = QuizAttempt.objects.create(
            employee=employee_profile,
            quiz=quiz,
            attempt_number=1,
            score=85.0,
            passed=True,
            time_taken_seconds=1200,  # 20 minutes
            completed_at=datetime.now(),
            answers_data={
                'question_1': 'B',
                'question_2': ['B', 'D']
            }
        )
        print(f"   Quiz attempt: Score {quiz_attempt.score}%")
        print(f"   Passed: {quiz_attempt.passed}")
        
        # Update progress with quiz results
        progress.quiz_attempts = 1
        progress.best_quiz_score = quiz_attempt.score
        progress.passed_quiz = True
        progress.save()
        
        # Step 15: Check course completion
        print("\n16. Checking Course Completion...")
        video_complete = progress.video_watched_seconds >= (progress.video_total_seconds * progress.required_watch_percentage / 100)
        quiz_complete = progress.passed_quiz
        
        if video_complete and quiz_complete:
            employee_assignment.status = 'completed'
            employee_assignment.completed_at = datetime.now()
            employee_assignment.progress_percentage = 100.0
            employee_assignment.save()
            
            print(f"   ✅ Course completed!")
            
            # Generate certificate
            import uuid
            certificate = CourseCompletionCertificate.objects.create(
                employee=employee_profile,
                course=course,
                assignment=employee_assignment,
                certificate_id=f"CERT-{uuid.uuid4().hex[:12].upper()}",
                verification_token=uuid.uuid4().hex,
                issued_by=company_admin
            )
            print(f"   Certificate: {certificate.certificate_id}")
        else:
            print(f"   ⏳ Course in progress")
            print(f"   Video complete: {video_complete} ({progress.video_watched_seconds/progress.video_total_seconds*100:.1f}% / {progress.required_watch_percentage}% required)")
            print(f"   Quiz complete: {quiz_complete}")
        
        # Final Summary
        print("\n" + "=" * 60)
        print("✅ ALL MODELS TESTED SUCCESSFULLY!")
        print("=" * 60)
        print("\nSummary of Created Objects:")
        print(f"  Users: {User.objects.count()} (Platform Admin: 1, Company Admin: 1, Employee: 1)")
        print(f"  Employee Profiles: {EmployeeProfile.objects.count()}")
        print(f"  Courses: {Course.objects.count()}")
        print(f"  Quizzes: {Quiz.objects.count()}")
        print(f"  Quiz Questions: {QuizQuestion.objects.count()}")
        print(f"  Company Assignments: {CompanyCourseAssignment.objects.count()}")
        print(f"  Employee Assignments: {EmployeeCourseAssignment.objects.count()}")
        print(f"  Quiz Attempts: {QuizAttempt.objects.count()}")
        
        return {
            'company': company,
            'platform_admin': platform_admin,
            'company_admin': company_admin,
            'employee_user': employee_user,
            'employee_profile': employee_profile,
            'course': course,
            'quiz': quiz,
            'employee_assignment': employee_assignment
        }
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    test_all_models()