from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Skill, Interest, Student, Project, Recommendation

# ============================================
# HOME PAGE
# ============================================
def home(request):
    context = {
        'total_projects': Project.objects.filter(status='ACTIVE').count(),
        'total_skills': Skill.objects.count(),
        'total_interests': Interest.objects.count(),
        'approved_projects': Project.objects.filter(supervisor_approved=True).count(),
        'popular_projects': Project.objects.filter(status='ACTIVE')[:6],
    }
    return render(request, 'home.html', context)

# ============================================
# STUDENT REGISTRATION - ONLY 22 SKILLS
# ============================================
def register(request):
    # Clear any existing session data
    request.session.flush()
    
    # ONLY 22 SKILLS
    skill_names = [
        'Python', 'Java', 'JavaScript', 'C++', 'HTML', 'CSS',
        'React', 'Django', 'Flask', 'Node.js', 'TensorFlow', 'PyTorch',
        'OpenCV', 'Machine Learning', 'Deep Learning', 'SQL',
        'MongoDB', 'Docker', 'AWS', 'Git', 'C#', 'PHP'
    ]
    
    # Get or create these skills
    for name in skill_names:
        Skill.objects.get_or_create(name=name)
    
    # Only show these 22 skills
    skills = Skill.objects.filter(name__in=skill_names).order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        roll_number = request.POST.get('roll_number')
        semester = request.POST.get('semester')
        time_available = request.POST.get('time_available', 6)
        has_gpu = request.POST.get('has_gpu') == 'on'
        experience_level = request.POST.get('experience_level', 'beginner')
        selected_skills = request.POST.getlist('skills')
        selected_interests = request.POST.getlist('interests')
        custom_skills = request.POST.get('custom_skills', '')
        
        # Check if student exists by email
        student, created = Student.objects.get_or_create(
            email=email,
            defaults={
                'name': name,
                'roll_number': roll_number,
                'semester': semester,
                'time_available': int(time_available),
                'has_gpu': has_gpu,
                'experience_level': experience_level
            }
        )
        
        if not created:
            student.name = name
            student.roll_number = roll_number
            student.semester = semester
            student.time_available = int(time_available)
            student.has_gpu = has_gpu
            student.experience_level = experience_level
            student.save()
            student.skills.clear()
            student.interests.clear()
        
        # Add selected skills
        for skill_id in selected_skills:
            if skill_id.isdigit():
                student.skills.add(Skill.objects.get(id=int(skill_id)))
        
        # Add custom skills
        if custom_skills:
            for skill_name in custom_skills.split(','):
                skill_name = skill_name.strip()
                if skill_name:
                    skill, _ = Skill.objects.get_or_create(name=skill_name)
                    student.skills.add(skill)
        
        # Add interests
        for interest_id in selected_interests:
            if interest_id.isdigit():
                student.interests.add(Interest.objects.get(id=int(interest_id)))
        
        request.session['student_id'] = student.id
        return redirect('recommendations')
    
    return render(request, 'register.html', {
        'skills': skills,
        'interests': Interest.objects.all().order_by('name')
    })

# ============================================
# PROJECT RECOMMENDATIONS
# ============================================
def recommendations(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('register')
    
    student = Student.objects.get(id=student_id)
    student_skills = set(student.skills.values_list('name', flat=True))
    student_interests = set(student.interests.values_list('name', flat=True))
    
    # If beginner with no skills, redirect to learning path
    if student.experience_level == 'beginner' and len(student_skills) == 0:
        return redirect('learning_path')
    
    all_projects = Project.objects.filter(status='ACTIVE')
    results = []
    
    for project in all_projects:
        project_skills = set(project.required_skills.values_list('name', flat=True))
        project_interests = set(project.interests.values_list('name', flat=True))
        
        common_skills = list(student_skills & project_skills)
        missing_skills = list(project_skills - student_skills)
        
        skill_match_count = len(common_skills)
        total_skills = len(project_skills)
        skill_match_pct = round((skill_match_count / total_skills * 100) if total_skills > 0 else 0, 1)
        
        interest_match_count = len(student_interests & project_interests)
        total_interests = len(project_interests)
        interest_match_pct = round((interest_match_count / total_interests * 100) if total_interests > 0 else 0, 1)
        
        exp_level_value = {'beginner': 1, 'intermediate': 3, 'advanced': 5}.get(student.experience_level, 3)
        difficulty_match = max(0, min(100, 100 - abs(exp_level_value - project.difficulty) * 20))
        
        match_score = round(
            skill_match_pct * 0.5 +
            interest_match_pct * 0.3 +
            difficulty_match * 0.2, 1
        )
        
        if project.supervisor_approved:
            match_score = min(match_score + 10, 100)
        
        if project.estimated_hours:
            weeks_needed = project.estimated_hours / 40
            if weeks_needed > student.time_available * 4:
                match_score = match_score * 0.7
            elif weeks_needed > student.time_available * 2:
                match_score = match_score * 0.85
        
        if not student.has_gpu and any(s in ['TensorFlow', 'PyTorch', 'CUDA', 'Deep Learning'] for s in project_skills):
            match_score = match_score * 0.6
        
        match_score = round(match_score, 1)
        
        results.append({
            'project': project,
            'match': match_score if common_skills else 0,
            'common': common_skills,
            'missing': missing_skills,
            'approved': project.supervisor_approved,
            'difficulty': project.get_difficulty_display(),
        })
    
    results.sort(key=lambda x: (-x['match'], -x['approved']))
    
    return render(request, 'recommendations.html', {
        'student': student,
        'projects': results[:10],
    })

# ============================================
# LEARNING PATH
# ============================================
def learning_path(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('register')
    
    student = Student.objects.get(id=student_id)
    all_skills = Skill.objects.all().order_by('name')
    student_interests = student.interests.all()
    
    interest_skill_map = {
        'Web Development': ['HTML', 'CSS', 'JavaScript', 'React', 'Node.js', 'Django', 'Flask'],
        'Artificial Intelligence': ['Python', 'Machine Learning', 'TensorFlow', 'PyTorch', 'Deep Learning'],
        'Data Science': ['Python', 'Pandas', 'NumPy', 'SQL', 'Matplotlib', 'Scikit-learn'],
        'Machine Learning': ['Python', 'Machine Learning', 'Scikit-learn', 'Pandas', 'NumPy'],
        'Deep Learning': ['Python', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Keras'],
        'Mobile App Development': ['Flutter', 'Dart', 'React Native', 'Kotlin', 'Swift'],
        'Game Development': ['Unity', 'C#', 'Unreal Engine', 'C++', 'Blender'],
        'Cybersecurity': ['Python', 'Networking', 'Cryptography', 'Security', 'Nmap'],
        'Blockchain': ['Python', 'Solidity', 'Web3', 'Smart Contracts', 'Ethereum'],
        'Cloud Computing': ['AWS', 'Docker', 'Kubernetes', 'Terraform', 'Linux'],
        'Internet of Things': ['Arduino', 'Raspberry Pi', 'Sensors', 'C++', 'Python'],
    }
    
    recommended_skills = []
    for interest in student_interests:
        if interest.name in interest_skill_map:
            for skill in interest_skill_map[interest.name]:
                try:
                    s = Skill.objects.get(name=skill)
                    if s not in student.skills.all():
                        recommended_skills.append({
                            'skill': s,
                            'interest': interest.name,
                            'weeks': 2,
                            'youtube_url': f'https://www.youtube.com/results?search_query=learn+{skill.replace(" ", "+")}',
                            'coursera_url': f'https://www.coursera.org/search?query={skill.replace(" ", "+")}'
                        })
                except:
                    pass
    
    seen = set()
    unique_skills = []
    for skill in recommended_skills:
        if skill['skill'].name not in seen:
            seen.add(skill['skill'].name)
            unique_skills.append(skill)
    
    return render(request, 'learning_path.html', {
        'student': student,
        'recommended_skills': unique_skills[:10],
        'all_skills': all_skills,
        'has_interests': student.interests.count() > 0,
    })

# ============================================
# ADD SKILL FROM LEARNING PATH
# ============================================
def add_skill_from_learning(request):
    if request.method == 'POST':
        student_id = request.session.get('student_id')
        skill_id = request.POST.get('skill_id')
        
        if student_id and skill_id and skill_id.isdigit():
            try:
                student = Student.objects.get(id=int(student_id))
                skill = Skill.objects.get(id=int(skill_id))
                student.skills.add(skill)
            except:
                pass
    
    return redirect('recommendations')

# ============================================
# PROJECT DETAIL
# ============================================
def project_detail(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
    except:
        return redirect('home')
    
    return render(request, 'project_detail.html', {
        'project': project,
        'required_skills': project.required_skills.all(),
        'interests': project.interests.all(),
    })

# ============================================
# DASHBOARD
# ============================================
def dashboard(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('register')
    
    student = Student.objects.get(id=student_id)
    recommendations = Recommendation.objects.filter(student=student).order_by('-match_score')[:5]
    
    return render(request, 'dashboard.html', {
        'student': student,
        'recommendations': recommendations,
        'skill_count': student.skills.count(),
        'interest_count': student.interests.count(),
        'total_projects': Project.objects.count(),
    })

# ============================================
# PROFILE
# ============================================
def profile(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('register')
    
    student = Student.objects.get(id=student_id)
    
    if request.method == 'POST':
        student.name = request.POST.get('name')
        student.roll_number = request.POST.get('roll_number')
        student.semester = request.POST.get('semester')
        student.time_available = request.POST.get('time_available', 6)
        student.has_gpu = request.POST.get('has_gpu') == 'on'
        student.experience_level = request.POST.get('experience_level', 'beginner')
        
        student.skills.clear()
        for skill_id in request.POST.getlist('skills'):
            if skill_id.isdigit():
                student.skills.add(Skill.objects.get(id=int(skill_id)))
        
        student.interests.clear()
        for interest_id in request.POST.getlist('interests'):
            if interest_id.isdigit():
                student.interests.add(Interest.objects.get(id=int(interest_id)))
        
        student.save()
        return redirect('dashboard')
    
    return render(request, 'profile.html', {
        'student': student,
        'skills': Skill.objects.all().order_by('name'),
        'interests': Interest.objects.all().order_by('name'),
        'student_skills': student.skills.values_list('id', flat=True),
        'student_interests': student.interests.values_list('id', flat=True),
    })

# ============================================
# BEGINNER SELECT INTERESTS
# ============================================
def beginner_select_interests(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('register')
    
    student = Student.objects.get(id=student_id)
    interests = Interest.objects.all().order_by('name')
    
    if request.method == 'POST':
        selected_interests = request.POST.getlist('interests')
        student.interests.clear()
        for interest_id in selected_interests:
            if interest_id.isdigit():
                student.interests.add(Interest.objects.get(id=int(interest_id)))
        student.save()
        return redirect('learning_path')
    
    return render(request, 'beginner_select.html', {
        'student': student,
        'interests': interests,
    })

# ============================================
# API - JSON RECOMMENDATIONS
# ============================================
def api_recommendations_json(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return JsonResponse({'error': 'No student found'}, status=400)
    
    try:
        student = Student.objects.get(id=int(student_id))
        recommendations = Recommendation.objects.filter(student=student).order_by('-match_score')[:10]
        
        data = []
        for rec in recommendations:
            data.append({
                'title': rec.project.title,
                'match_score': rec.match_score,
                'domain': rec.project.get_domain_display(),
                'dataset_url': rec.project.dataset_url,
                'difficulty': rec.project.get_difficulty_display(),
                'supervisor_approved': rec.project.supervisor_approved,
            })
        
        return JsonResponse({'recommendations': data, 'student_name': student.name})
    except:
        return JsonResponse({'error': 'Invalid request'}, status=400)