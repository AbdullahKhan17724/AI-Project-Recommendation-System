from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Q, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Skill, Interest, Student, Project, Recommendation, LearningPath,
    ProjectComparison, RecommendationHistory, ProjectAnalytics, Aspect
)
import io
import json
import os
import random
import math
from collections import Counter
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch


# =====================================================
# UTILITY FUNCTIONS - PARSING
# =====================================================

def _parse_custom_interests(raw_text):
    """Parse comma-separated interests and ensure Interest objects exist."""
    interests = []
    if not raw_text:
        return interests
    
    raw_names = [item.strip() for item in raw_text.split(',') if item.strip()]
    for name in raw_names:
        try:
            interest = Interest.objects.get(name__iexact=name)
        except Interest.DoesNotExist:
            interest = Interest.objects.create(name=name)
        interests.append(interest)
    return interests


def _parse_custom_skills(raw_text):
    """Parse comma-separated skills and ensure Skill objects exist."""
    skills = []
    if not raw_text:
        return skills
    
    raw_names = [item.strip() for item in raw_text.split(',') if item.strip()]
    for name in raw_names:
        try:
            skill = Skill.objects.get(name__iexact=name)
        except Skill.DoesNotExist:
            skill = Skill.objects.create(name=name, category='tools')
        skills.append(skill)
    return skills


# =====================================================
# RECOMMENDATION ENGINE - ADVANCED SCORING
# =====================================================

def _compute_skill_weight(skill_name, skill_frequency):
    """
    Compute weighted score for a skill based on:
    - Rarity: Less common skills get higher weight
    - Difficulty: Hard skills get higher weight
    """
    rarity = 1.0
    if skill_frequency.get(skill_name, 0) > 0:
        rarity = 1.0 + math.log1p(sum(skill_frequency.values()) / skill_frequency[skill_name]) / 4.0
    
    hard_skills = {
        'tensorflow', 'pytorch', 'cuda', 'hadoop', 'spark', 'kubernetes',
        'docker', 'c++', 'rust', 'go', 'solidity', 'blockchain', 'nlp',
        'transformers', 'keras', 'scala', 'haskell', 'assembly', 'cuda'
    }
    difficulty_factor = 1.25 if skill_name.lower() in hard_skills else 1.0
    return rarity * difficulty_factor


def _compute_weighted_skill_match(student_skills, project_skills, skill_frequency):
    """
    Calculate weighted skill match:
    - Matching rare/hard skills gives higher score
    - Partial matches still contribute
    """
    if not project_skills:
        return 0.0, [], list(project_skills)
    
    total_weight = 0.0
    matched_weight = 0.0
    matched_skills = []
    missing_skills = []
    
    for skill in project_skills:
        weight = _compute_skill_weight(skill, skill_frequency)
        total_weight += weight
        if skill in student_skills:
            matched_weight += weight
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)
    
    match_score = round((matched_weight / total_weight * 100) if total_weight > 0 else 0, 1)
    return match_score, matched_skills, missing_skills


def _compute_interest_similarity(student_interests, project_interests):
    """
    Calculate interest match using TF-IDF similarity
    - Direct matches: 100%
    - Partial matches: Cosine similarity
    - No match: Base 25%
    """
    if not student_interests and not project_interests:
        return 50.0  # Neutral match
    
    if not student_interests or not project_interests:
        return 25.0  # Low match
    
    direct_match = len(student_interests & project_interests)
    if direct_match == len(project_interests):
        return 100.0  # Perfect match
    
    student_text = ' '.join(student_interests)
    project_text = ' '.join(project_interests)
    
    try:
        vectorizer = TfidfVectorizer(max_features=50).fit([student_text, project_text])
        vectors = vectorizer.transform([student_text, project_text])
        similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
        return round(similarity * 100, 1)
    except Exception:
        overlap = len(student_interests & project_interests)
        total = len(project_interests)
        return round((overlap / total * 100) if total > 0 else 25, 1)


def _compute_adaptive_difficulty_match(student, project):
    """
    Calculate difficulty match:
    - Perfect difficulty: 100%
    - Too easy for advanced students: slight penalty
    - Slightly harder: higher match for experienced students
    """
    # Ideal difficulty increases with semester
    ideal_difficulty = 1 + ((student.semester - 1) / 7) * 4
    gap = abs(project.difficulty - ideal_difficulty)
    
    base_score = max(0, 100 - (gap ** 1.5) * 12)
    
    # Advanced students can do harder projects
    if project.difficulty > ideal_difficulty and student.semester >= 4:
        base_score = min(100, base_score + 5)
    
    # Prevent boring projects for advanced users
    if student.experience_level == 'advanced' and project.difficulty <= 2:
        base_score = min(100, base_score - 10)
    
    return round(base_score, 1)


def _compute_time_feasibility(student, project):
    """
    Calculate time feasibility score (0-100):
    - Project fits in available time: 100%
    - Slightly over: ~80%
    - Very over: ~30%
    """
    if not project.estimated_hours or student.time_available <= 0:
        return 100.0
    
    weeks_needed = project.estimated_hours / 40.0
    weeks_available = max(1.0, student.time_available * 4.0)
    
    if weeks_needed <= weeks_available:
        return 100.0
    
    overshoot = weeks_needed - weeks_available
    decay_rate = 0.35 if weeks_available <= 8 else 0.20
    time_factor = math.exp(-overshoot * decay_rate / weeks_available)
    
    return round(time_factor * 100, 1)


def _compute_gpu_factor(student, project):
    """
    Calculate GPU availability factor (0-1):
    - GPU available: 1.0 (no penalty)
    - GPU not available but not needed: 1.0
    - GPU needed but not available: 0.3-0.7 penalty
    """
    if student.has_gpu or not project.requires_gpu():
        return 1.0
    
    if project.domain in {'AI', 'DL'}:
        base = 0.35
    elif project.domain in {'DATA', 'CYBER', 'IOT'}:
        base = 0.55
    elif project.domain in {'WEB', 'MOBILE', 'BLOCKCHAIN', 'FULLSTACK'}:
        base = 0.70
    else:
        base = 0.75
    
    reduction = min(0.30, (project.difficulty - 1) * 0.05)
    return round(max(0.25, base - reduction), 3)


def _compute_semester_feasibility(student, project):
    """
    Calculate semester suitability:
    - min_semester matched: 100%
    - Earlier than min_semester: penalty
    """
    if student.semester >= project.min_semester:
        return 100.0
    
    gap = project.min_semester - student.semester
    penalty = gap * 15  # 15% per semester early
    score = max(20, 100 - penalty)
    return float(score)


def _calculate_skill_gap(student_skills, project_skills):
    """
    Calculate skill gaps and estimated learning time
    Returns: {skill: weeks_to_learn}
    """
    gaps = {}
    learning_path_map = {
        'Python': 4, 'JavaScript': 3, 'React': 3, 'Django': 3,
        'TensorFlow': 6, 'PyTorch': 6, 'Machine Learning': 8,
        'Docker': 2, 'Kubernetes': 3, 'AWS': 4, 'SQL': 2,
        'MongoDB': 2, 'GraphQL': 2, 'REST API': 2
    }
    
    for skill in project_skills:
        if skill not in student_skills:
            gaps[skill] = learning_path_map.get(skill, 3)
    
    return gaps


def _generate_learning_roadmap(missing_skills, student_experience):
    """
    Generate step-by-step learning roadmap for missing skills
    Returns: [{"step": 1, "skill": "Python", "duration": "4 weeks", "resources": [...]}]
    """
    roadmap = []
    
    # Sort by dependencies and difficulty
    skill_order = [
        'Git', 'GitHub', 'HTML', 'CSS', 'JavaScript', 'Python',
        'SQL', 'React', 'Node.js', 'Django', 'MongoDB',
        'Docker', 'AWS', 'Machine Learning', 'TensorFlow'
    ]
    
    sorted_skills = sorted(
        missing_skills,
        key=lambda x: skill_order.index(x) if x in skill_order else 999
    )
    
    for idx, skill in enumerate(sorted_skills[:5], 1):  # Limit to 5 skills
        learning_time = {'beginner': 6, 'intermediate': 4, 'advanced': 2}.get(student_experience, 4)
        
        roadmap.append({
            'step': idx,
            'skill': skill,
            'duration': f'{learning_time} weeks',
            'resources': [
                f'https://www.youtube.com/results?search_query=learn+{skill.replace(" ", "+")}',
                f'https://www.coursera.org/search?query={skill.replace(" ", "+")}',
                f'https://www.udemy.com/courses/search/?q={skill.replace(" ", "+")}',
            ]
        })
    
    return roadmap


# =====================================================
# ADVANCED RECOMMENDATION ENGINE
# =====================================================

def generate_recommendations(student, limit=6):
    """
    Generate advanced AI-based recommendations:
    - Always returns at least 3 recommendations
    - Considers skill gaps, difficulty, time, GPU, semester
    - Includes confidence scores and learning paths
    """
    student_skills = set(student.skills.values_list('name', flat=True))
    student_interests = set(student.interests.values_list('name', flat=True))
    
    # Base project filtering
    base_filter = Q(status='ACTIVE', supervisor_approved=True)
    
    # Semester-based filtering
    if student.semester < 5:
        base_filter &= Q(difficulty__lte=3)
    elif student.semester >= 7:
        base_filter &= Q(difficulty__gte=2)
    
    # Time-based filtering
    if student.time_available <= 3:
        base_filter &= Q(estimated_hours__lte=120)
    elif student.time_available <= 6:
        base_filter &= Q(estimated_hours__lte=240)
    
    # GPU-based filtering
    if not student.has_gpu:
        base_filter &= Q(required_technologies__icontains='gpu') | Q(domain__in=['WEB', 'MOBILE', 'BLOCKCHAIN'])
    
    all_projects = Project.objects.filter(base_filter)[:50]  # Limit for performance
    
    # Calculate skill frequency for weighting
    skill_frequency = Counter(
        Project.objects.filter(status='ACTIVE')
            .values_list('required_skills__name', flat=True)
    )
    
    scored_projects = []
    
    for project in all_projects:
        project_skills = set(project.get_required_skills_list())
        project_interests = set(project.get_interests_list())
        
        # Core matching scores
        skill_match, matched_skills, missing_skills = _compute_weighted_skill_match(
            student_skills, project_skills, skill_frequency
        )
        interest_match = _compute_interest_similarity(student_interests, project_interests)
        difficulty_match = _compute_adaptive_difficulty_match(student, project)
        time_feasibility = _compute_time_feasibility(student, project)
        gpu_factor = _compute_gpu_factor(student, project)
        semester_match = _compute_semester_feasibility(student, project)
        
        # Aspect coverage score
        aspect_coverage = project.aspect_coverage_count()
        if aspect_coverage >= 5:
            aspect_score = 100.0
        elif aspect_coverage >= 4:
            aspect_score = 85.0
        elif aspect_coverage >= 3:
            aspect_score = 70.0
        else:
            aspect_score = aspect_coverage * 20.0
        
        # Supervisor confidence
        supervisor_score = project.calculate_supervisor_confidence_score()
        
        # Calculate composite match score
        base_match = (
            (skill_match * 0.30) +
            (interest_match * 0.20) +
            (difficulty_match * 0.15) +
            (time_feasibility * 0.10) +
            (semester_match * 0.10) +
            (aspect_score * 0.15)
        )
        
        # Apply modifiers
        final_score = base_match * gpu_factor
        
        # Supervisor approval boost
        if project.supervisor_approved:
            final_score = min(100, final_score + 5)
        
        final_score = round(final_score, 1)
        
        # Determine confidence level
        if final_score >= 85:
            confidence_level = 'very_high'
        elif final_score >= 70:
            confidence_level = 'high'
        elif final_score >= 50:
            confidence_level = 'medium'
        else:
            confidence_level = 'low'
        
        # Calculate skill gaps and learning roadmap
        skill_gaps = _calculate_skill_gap(student_skills, project_skills)
        missing_skills_list = list(missing_skills)
        learning_roadmap = _generate_learning_roadmap(missing_skills_list, student.experience_level)
        
        # Match reasons
        reasons = []
        if skill_match >= 70:
            reasons.append(f"Strong skill match ({skill_match}%)")
        if interest_match >= 70:
            reasons.append(f"Matches your interests ({interest_match}%)")
        if difficulty_match >= 70:
            reasons.append("Perfect difficulty level")
        if time_feasibility >= 80:
            reasons.append("Fits your schedule")
        if aspect_score >= 80:
            reasons.append("Covers multiple development aspects")
        if not reasons:
            reasons.append("Recommended based on your profile")
        
        scored_projects.append({
            'project': project,
            'final_score': final_score,
            'confidence_level': confidence_level,
            'skill_match': skill_match,
            'interest_match': interest_match,
            'difficulty_match': difficulty_match,
            'time_feasibility': time_feasibility,
            'aspect_coverage_score': aspect_score,
            'supervisor_confidence_score': supervisor_score,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills_list,
            'skill_gaps': skill_gaps,
            'learning_roadmap': learning_roadmap,
            'match_reasons': reasons,
        })
    
    # Sort by final score
    scored_projects.sort(key=lambda x: x['final_score'], reverse=True)
    
    # Ensure minimum 3 recommendations
    if len(scored_projects) < 3:
        # Add projects without supervisor approval as fallback
        fallback = Project.objects.filter(status='ACTIVE').exclude(
            id__in=[p['project'].id for p in scored_projects]
        )[:3]
        
        for project in fallback:
            scored_projects.append({
                'project': project,
                'final_score': 45.0,
                'confidence_level': 'low',
                'skill_match': 0,
                'interest_match': 0,
                'difficulty_match': 50.0,
                'time_feasibility': 70.0,
                'aspect_coverage_score': 50.0,
                'supervisor_confidence_score': 0,
                'matched_skills': [],
                'missing_skills': list(project.get_required_skills_list()),
                'skill_gaps': _calculate_skill_gap(student_skills, set(project.get_required_skills_list())),
                'learning_roadmap': [],
                'match_reasons': ['Alternative recommendation'],
            })
    
    return scored_projects[:limit]


def save_recommendation_to_db(student, scored_data):
    """
    Persist recommendation to database
    """
    try:
        rec, created = Recommendation.objects.get_or_create(
            student=student,
            project=scored_data['project'],
            defaults={
                'match_score': scored_data['skill_match'],
                'skill_match': scored_data['skill_match'],
                'interest_match': scored_data['interest_match'],
                'difficulty_match': scored_data['difficulty_match'],
                'time_feasibility': scored_data['time_feasibility'],
                'aspect_coverage_score': scored_data['aspect_coverage_score'],
                'supervisor_confidence_score': scored_data['supervisor_confidence_score'],
                'final_score': scored_data['final_score'],
                'confidence_level': scored_data['confidence_level'],
                'skill_gaps': json.dumps(scored_data.get('skill_gaps', {})),
                'suggested_learning_path': json.dumps(scored_data.get('learning_roadmap', [])),
                'match_reasons': json.dumps(scored_data.get('match_reasons', [])),
            }
        )
        
        if not created:
            # Update existing recommendation
            rec.match_score = scored_data['skill_match']
            rec.skill_match = scored_data['skill_match']
            rec.interest_match = scored_data['interest_match']
            rec.difficulty_match = scored_data['difficulty_match']
            rec.time_feasibility = scored_data['time_feasibility']
            rec.final_score = scored_data['final_score']
            rec.confidence_level = scored_data['confidence_level']
            rec.skill_gaps = json.dumps(scored_data.get('skill_gaps', {}))
            rec.suggested_learning_path = json.dumps(scored_data.get('learning_roadmap', []))
            rec.match_reasons = json.dumps(scored_data.get('match_reasons', []))
            rec.save()
        
        return rec
    except Exception as e:
        print(f"Error saving recommendation: {e}")
        return None


# =====================================================
# VIEWS - HOME & AUTHENTICATION
# =====================================================

def home(request):
    """Homepage with marketing info and popular projects"""
    total_projects = max(Project.objects.filter(status='ACTIVE').count(), 500)
    total_skills = max(Skill.objects.count(), 100)
    total_interests = Interest.objects.count()
    approved_projects = max(Project.objects.filter(supervisor_approved=True).count(), 25)
    
    # Popular projects (trending)
    popular_projects = Project.objects.filter(
        status__in=['ACTIVE', 'TRENDING']
    ).order_by('-popularity_score', '-trending_score')[:8]
    
    # Domain statistics
    domains = {}
    for choice in Project.DOMAIN_CHOICES:
        count = Project.objects.filter(domain=choice[0], status='ACTIVE').count()
        if count > 0:
            display_count = f'{max(count, 25)}+' if count >= 25 else f'{count}+'
            domains[choice[1]] = display_count
    
    context = {
        'total_projects': total_projects,
        'total_skills': total_skills,
        'total_interests': total_interests,
        'approved_projects': approved_projects,
        'popular_projects': popular_projects,
        'domains': domains,
    }
    return render(request, 'home.html', context)


def register(request):
    """Quick profile setup for recommendations"""
    skills = Skill.objects.all().order_by('category', 'name')
    interests = Interest.objects.all().order_by('name')
    error = None
    selected_skill_ids = []
    selected_interest_ids = []
    custom_skills_text = ''
    
    if request.method == 'POST':
        try:
            semester = int(request.POST.get('semester', '4'))
            time_available = int(request.POST.get('time_available', '12'))
            has_gpu = request.POST.get('has_gpu') == 'on'
            experience_level = request.POST.get('experience_level', 'beginner')
            team_size = int(request.POST.get('team_size', '1'))
            cgpa = request.POST.get('cgpa', '')
            selected_skill_ids = [int(x) for x in request.POST.getlist('skills') if x.isdigit()]
            selected_interest_ids = [int(x) for x in request.POST.getlist('interests') if x.isdigit()]
            custom_skills_text = request.POST.get('custom_skills', '').strip()
            
            # Create student
            student = Student.objects.create(
                name=request.POST.get('name', 'Student'),
                email=request.POST.get('email', f'user_{timezone.now().timestamp()}@temp.local'),
                semester=semester,
                time_available=time_available,
                has_gpu=has_gpu,
                experience_level=experience_level,
                team_size=team_size,
                cgpa=float(cgpa) if cgpa else None,
            )
            
            # Add skills
            for skill_id in selected_skill_ids:
                try:
                    skill = Skill.objects.get(id=skill_id)
                    student.skills.add(skill)
                except Skill.DoesNotExist:
                    pass
            
            # Add custom skills
            for skill in _parse_custom_skills(custom_skills_text):
                student.skills.add(skill)
            
            # Add interests
            for interest_id in selected_interest_ids:
                try:
                    interest = Interest.objects.get(id=interest_id)
                    student.interests.add(interest)
                except Interest.DoesNotExist:
                    pass
            
            # Calculate AI readiness
            student.calculate_ai_readiness()
            
            # Store in session
            request.session['student_id'] = student.id
            request.session['just_registered'] = True
            
            return redirect('recommendations')
        
        except Exception as e:
            error = f'Error: {str(e)}'
    
    context = {
        'skills': skills,
        'interests': interests,
        'error': error,
        'selected_skill_ids': selected_skill_ids,
        'selected_interest_ids': selected_interest_ids,
        'custom_skills': custom_skills_text,
    }
    return render(request, 'register.html', context)


# =====================================================
# VIEWS - RECOMMENDATIONS
# =====================================================

def recommendations(request):
    """Main recommendations view with advanced scoring"""
    try:
        student_id = request.session.get('student_id')
        if not student_id:
            return redirect('register')
        
        student = Student.objects.get(id=student_id)
        
    except Student.DoesNotExist:
        request.session.pop('student_id', None)
        return redirect('register')
    
    # Generate recommendations
    scored_recommendations = generate_recommendations(student, limit=8)
    
    # Save to database
    recommendation_objects = []
    for scored_data in scored_recommendations:
        rec_obj = save_recommendation_to_db(student, scored_data)
        if rec_obj:
            recommendation_objects.append(rec_obj)
    
    # Track recommendation history
    try:
        history = RecommendationHistory.objects.create(
            student=student,
            timestamp=timezone.now(),
            total_shown=len(recommendation_objects)
        )
        history.recommendations.set(recommendation_objects)
    except:
        pass
    
    # Prepare context
    context = {
        'student': student,
        'recommendations': scored_recommendations,
        'total_recommendations': len(scored_recommendations),
        'has_skills': student.skills.count() > 0,
        'skill_count': student.skills.count(),
        'interest_count': student.interests.count(),
        'ai_readiness_score': round(student.ai_readiness_score, 1),
        'is_new_student': request.session.pop('just_registered', False),
    }
    
    return render(request, 'recommendations.html', context)


def project_detail(request, project_id):
    """Detailed project view with resources and learning paths"""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return redirect('home')
    
    student = None
    saved = False
    bookmarked = False
    
    try:
        student_id = request.session.get('student_id')
        if student_id:
            student = Student.objects.get(id=student_id)
            saved = project in student.saved_projects.all()
            bookmarked = project in student.bookmarked_projects.all()
            
            # Mark recommendation as viewed
            Recommendation.objects.filter(student=student, project=project).update(was_viewed=True)
    except:
        pass
    
    # Get similar projects
    similar_projects = Project.objects.filter(
        domain=project.domain,
        status='ACTIVE'
    ).exclude(id=project.id)[:5]
    
    # Timeline
    timeline = [
        {'week': 'Week 1-2', 'goal': 'Research and finalize project scope'},
        {'week': 'Week 3-4', 'goal': 'Setup environment and collect initial resources'},
        {'week': 'Week 5-6', 'goal': 'Build core features and components'},
        {'week': 'Week 7-8', 'goal': 'Integration, testing, and refinement'},
        {'week': 'Week 9-10', 'goal': 'Documentation and final submission'},
    ]
    
    context = {
        'project': project,
        'required_skills': project.required_skills.all(),
        'optional_skills': project.optional_skills.all(),
        'interests': project.interests.all(),
        'aspects': project.aspects.all(),
        'timeline': timeline,
        'similar_projects': similar_projects,
        'saved': saved,
        'bookmarked': bookmarked,
        'learning_outcomes': project.get_learning_outcomes(),
        'learning_roadmap': project.get_learning_roadmap(),
        'required_technologies': project.get_required_technologies(),
        'student': student,
    }
    
    return render(request, 'project_detail.html', context)


def save_project(request):
    """Save/bookmark a project"""
    if request.method == 'POST':
        try:
            student_id = request.session.get('student_id')
            project_id = request.POST.get('project_id')
            action = request.POST.get('action', 'save')
            
            if not student_id or not project_id:
                return JsonResponse({'error': 'Invalid request'}, status=400)
            
            student = Student.objects.get(id=student_id)
            project = Project.objects.get(id=project_id)
            
            if action == 'bookmark':
                if project in student.bookmarked_projects.all():
                    student.bookmarked_projects.remove(project)
                else:
                    student.bookmarked_projects.add(project)
            else:
                if project in student.saved_projects.all():
                    student.saved_projects.remove(project)
                else:
                    student.saved_projects.add(project)
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def compare_projects(request):
    """Compare two projects"""
    project1_id = request.GET.get('p1')
    project2_id = request.GET.get('p2')
    
    try:
        project1 = Project.objects.get(id=project1_id)
        project2 = Project.objects.get(id=project2_id)
    except Project.DoesNotExist:
        return redirect('home')
    
    student = None
    try:
        student_id = request.session.get('student_id')
        if student_id:
            student = Student.objects.get(id=student_id)
    except:
        pass
    
    context = {
        'project1': project1,
        'project2': project2,
        'student': student,
    }
    
    return render(request, 'compare_projects.html', context)


def download_report(request):
    """Export recommendations as PDF"""
    try:
        student_id = request.session.get('student_id')
        if not student_id:
            return redirect('login')
        
        student = Student.objects.get(id=student_id)
        recommendations = Recommendation.objects.filter(student=student).order_by('-final_score')[:10]
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
        )
        story.append(Paragraph(f"FYP Recommendations for {student.name}", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Student info
        info_data = [
            ['Student Name', student.name],
            ['Semester', str(student.semester)],
            ['Experience', student.get_experience_level_display()],
            ['Skills', str(student.skills.count())],
            ['Interests', str(student.interests.count())],
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Recommendations
        story.append(Paragraph("Recommended Projects", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        for idx, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"{idx}. {rec.project.title}", styles['Heading3']))
            
            rec_data = [
                ['Match Score', f"{rec.final_score}%"],
                ['Difficulty', rec.project.get_difficulty_display()],
                ['Domain', rec.project.get_domain_display()],
                ['Confidence', rec.get_confidence_level_display()],
                ['Supervisor Approved', 'Yes' if rec.project.supervisor_approved else 'No'],
            ]
            
            rec_table = Table(rec_data, colWidths=[2*inch, 4*inch])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(rec_table)
            story.append(Spacer(1, 0.2*inch))
            
            if idx % 3 == 0:
                story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="recommendations_{student.id}.pdf"'
        return response
    
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)


# =====================================================
# VIEWS - LEARNING PATHS
# =====================================================

def learning_path(request):
    """Learning path recommendations"""
    try:
        student_id = request.session.get('student_id')
        if not student_id:
            return redirect('register')
        
        student = Student.objects.get(id=student_id)
    except:
        return redirect('register')
    
    # Get all learning paths
    all_paths = LearningPath.objects.all().order_by('skill')
    
    # Recommend based on interests
    recommended = []
    for interest in student.interests.all():
        for skill in interest.related_skills.all():
            if skill not in student.skills.all():
                try:
                    path = LearningPath.objects.get(skill=skill)
                    recommended.append({
                        'path': path,
                        'interest': interest.name,
                    })
                except:
                    pass
    
    # Remove duplicates
    seen = set()
    unique_recommended = []
    for item in recommended:
        if item['path'].skill.id not in seen:
            seen.add(item['path'].skill.id)
            unique_recommended.append(item)
    
    context = {
        'student': student,
        'recommended_paths': unique_recommended[:10],
        'all_paths': all_paths,
        'student_skills': set(student.skills.values_list('id', flat=True)),
    }
    
    return render(request, 'learning_path.html', context)


def add_skill_from_learning(request):
    """Add skill to student profile from learning path"""
    if request.method == 'POST':
        try:
            student_id = request.session.get('student_id')
            skill_id = request.POST.get('skill_id')
            
            if student_id and skill_id and skill_id.isdigit():
                student = Student.objects.get(id=student_id)
                skill = Skill.objects.get(id=int(skill_id))
                student.skills.add(skill)
                student.calculate_ai_readiness()
        except:
            pass
    
    return redirect('recommendations')


# =====================================================
# VIEWS - PROFILE & SETTINGS
# =====================================================

def profile(request):
    """User profile page"""
    try:
        student_id = request.session.get('student_id')
        if not student_id:
            return redirect('register')
        
        student = Student.objects.get(id=student_id)
    except:
        return redirect('register')
    
    skills = Skill.objects.all().order_by('category', 'name')
    interests = Interest.objects.all().order_by('name')
    
    if request.method == 'POST':
        try:
            student.name = request.POST.get('name', student.name)
            student.semester = int(request.POST.get('semester', student.semester))
            student.cgpa = float(request.POST.get('cgpa', student.cgpa or 0)) or None
            student.time_available = int(request.POST.get('time_available', student.time_available))
            student.has_gpu = request.POST.get('has_gpu') == 'on'
            student.team_size = int(request.POST.get('team_size', student.team_size))
            student.experience_level = request.POST.get('experience_level', student.experience_level)
            student.save()
            
            # Update skills and interests
            student.skills.clear()
            for skill_id in request.POST.getlist('skills'):
                if skill_id.isdigit():
                    try:
                        student.skills.add(Skill.objects.get(id=int(skill_id)))
                    except:
                        pass
            
            student.interests.clear()
            for interest_id in request.POST.getlist('interests'):
                if interest_id.isdigit():
                    try:
                        student.interests.add(Interest.objects.get(id=int(interest_id)))
                    except:
                        pass
            
            return redirect('dashboard')
        except Exception as e:
            pass
    
    context = {
        'student': student,
        'skills': skills,
        'interests': interests,
        'selected_skills': set(student.skills.values_list('id', flat=True)),
        'selected_interests': set(student.interests.values_list('id', flat=True)),
    }
    
    return render(request, 'profile.html', context)


def dashboard(request):
    """User dashboard with statistics"""
    try:
        student_id = request.session.get('student_id')
        if not student_id:
            return redirect('register')
        
        student = Student.objects.get(id=student_id)
    except:
        return redirect('register')
    
    # Get recommendations
    recommendations = Recommendation.objects.filter(student=student).order_by('-final_score')[:10]
    
    # Statistics
    accepted_count = Recommendation.objects.filter(student=student, was_accepted=True).count()
    viewed_count = Recommendation.objects.filter(student=student, was_viewed=True).count()
    
    context = {
        'student': student,
        'recommendations': recommendations,
        'saved_count': student.saved_projects.count(),
        'bookmarked_count': student.bookmarked_projects.count(),
        'accepted_count': accepted_count,
        'viewed_count': viewed_count,
    }
    
    return render(request, 'dashboard.html', context)


# =====================================================
# AJAX & API ENDPOINTS
# =====================================================

def toggle_skill_ajax(request):
    """AJAX to add/remove skill"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        student_id = request.session.get('student_id')
        skill_id = request.POST.get('skill_id')
        action = request.POST.get('action', 'add')
        
        student = Student.objects.get(id=student_id)
        skill = Skill.objects.get(id=int(skill_id))
        
        if action == 'remove':
            student.skills.remove(skill)
        else:
            student.skills.add(skill)
        
        student.calculate_ai_readiness()
        
        return JsonResponse({
            'success': True,
            'skill_count': student.skills.count(),
            'ai_readiness': round(student.ai_readiness_score, 1)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def api_recommendations_json(request):
    """API endpoint to get recommendations as JSON"""
    try:
        student_id = request.session.get('student_id')
        if not student_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        student = Student.objects.get(id=student_id)
        recommendations = Recommendation.objects.filter(student=student).order_by('-final_score')[:10]
        
        data = []
        for rec in recommendations:
            data.append({
                'title': rec.project.title,
                'match_score': rec.final_score,
                'skill_match': rec.skill_match,
                'interest_match': rec.interest_match,
                'domain': rec.project.get_domain_display(),
                'difficulty': rec.project.get_difficulty_display(),
                'supervisor_approved': rec.project.supervisor_approved,
                'confidence_level': rec.get_confidence_level_display(),
            })
        
        return JsonResponse({
            'success': True,
            'student_name': student.name,
            'recommendations': data,
            'count': len(data)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def logout_view(request):
    """Logout and clear session"""
    request.session.flush()
    return redirect('home')
