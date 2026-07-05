from django.db import models
from django.db.models import Q, F
from django.utils import timezone
import json

class Aspect(models.Model):
    """Project development aspects (Frontend, Backend, Database, AI/ML, Deployment, etc.)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    emoji = models.CharField(max_length=10, default='📌')
    icon_class = models.CharField(max_length=50, default='fas fa-project-diagram')
    
    def __str__(self):
        return f"{self.emoji} {self.name}"
    
    class Meta:
        verbose_name_plural = "Aspects"
        ordering = ['name']

class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('programming', '💻 Programming Language'),
        ('frontend', '🎨 Frontend'),
        ('backend', '⚙️ Backend'),
        ('database', '📊 Database'),
        ('ai_ml', '🤖 AI/Machine Learning'),
        ('devops', '🚀 DevOps'),
        ('cloud', '☁️ Cloud'),
        ('data', '📈 Data Science'),
        ('security', '🔒 Security'),
        ('tools', '🛠️ Tools & Frameworks'),
        ('soft', '💡 Soft Skills'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='tools')
    proficiency_level = models.IntegerField(default=1, help_text="1=Beginner, 2=Intermediate, 3=Advanced, 4=Expert")
    is_trending = models.BooleanField(default=False)
    popularity_score = models.IntegerField(default=0)
    icon_class = models.CharField(max_length=50, default='fas fa-code')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-popularity_score', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_trending']),
        ]

class Interest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    emoji = models.CharField(max_length=10, default='💡')
    icon_class = models.CharField(max_length=50, default='fas fa-heart')
    related_skills = models.ManyToManyField(Skill, blank=True, help_text="Skills typically related to this interest")
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Student(models.Model):
    EXPERIENCE_CHOICES = [
        ('beginner', '🌟 Beginner - No coding experience'),
        ('intermediate', '📚 Intermediate - Know basics'),
        ('advanced', '🚀 Advanced - Ready for complex projects'),
    ]
    
    SEMESTER_CHOICES = [(i, f'{i}th Semester') for i in range(1, 9)]
    
    DEPARTMENT_CHOICES = [
        ('Computer Science', 'Computer Science'),
        ('Software Engineering', 'Software Engineering'),
        ('Electrical', 'Electrical Engineering'),
        ('Business', 'Business / Management'),
        ('Mechanical', 'Mechanical Engineering'),
        ('Other', 'Other / Interdisciplinary'),
    ]
    
    TIME_CHOICES = [
        (3, '3 months (Short)'),
        (6, '6 months (Medium)'),
        (9, '9 months (Long)'),
        (12, '12 months (Full semester)'),
    ]
    
    # Personal Info
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    roll_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    semester = models.IntegerField(choices=SEMESTER_CHOICES, default=1)
    cgpa = models.FloatField(null=True, blank=True, help_text="CGPA score (0-4.0)")
    
    # Academic Info
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, default='Computer Science')
    
    # Skills & Interests
    skills = models.ManyToManyField(Skill, blank=True, related_name='students')
    interests = models.ManyToManyField(Interest, blank=True, related_name='students')
    saved_projects = models.ManyToManyField('Project', blank=True, related_name='saved_by_students')
    bookmarked_projects = models.ManyToManyField('Project', blank=True, related_name='bookmarked_by_students', help_text="Favorite projects")
    
    # Constraints
    time_available = models.IntegerField(choices=TIME_CHOICES, default=12, help_text="Months available for project")
    has_gpu = models.BooleanField(default=False, help_text="Student has GPU access")
    team_size = models.IntegerField(default=1, help_text="Team members (1-5)")
    
    # Level
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='beginner')
    
    # Advanced Profile Data
    ai_readiness_score = models.FloatField(default=0.0, help_text="AI/ML project readiness (0-100)")
    learning_preference = models.CharField(
        max_length=20,
        choices=[('visual', 'Visual'), ('hands-on', 'Hands-on'), ('theoretical', 'Theoretical'), ('mixed', 'Mixed')],
        default='mixed'
    )
    past_project_ids = models.TextField(default='[]', help_text="JSON array of past project IDs")
    preference_tags = models.TextField(default='[]', help_text="JSON array of preference tags")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_recommendation_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        if self.roll_number:
            return f"{self.name} ({self.roll_number})"
        return self.name
    
    def skill_count(self):
        return self.skills.count()
    
    def interest_count(self):
        return self.interests.count()
    
    def get_past_projects(self):
        """Parse past project IDs from JSON"""
        try:
            return json.loads(self.past_project_ids)
        except:
            return []
    
    def get_preference_tags(self):
        """Parse preference tags from JSON"""
        try:
            return json.loads(self.preference_tags)
        except:
            return []
    
    def calculate_ai_readiness(self):
        """Calculate AI/ML project readiness score"""
        ai_skills = {'Python', 'TensorFlow', 'PyTorch', 'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision'}
        student_skills = {s.name for s in self.skills.all()}
        
        skill_match = len(student_skills & ai_skills) / len(ai_skills) * 40
        semester_factor = min(self.semester / 8 * 30, 30)
        experience_factor = {'beginner': 10, 'intermediate': 20, 'advanced': 30}.get(self.experience_level, 0)
        
        self.ai_readiness_score = round(skill_match + semester_factor + experience_factor, 1)
        self.save()
        return self.ai_readiness_score
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['semester']),
            models.Index(fields=['experience_level']),
        ]

class Project(models.Model):
    DOMAIN_CHOICES = [
        ('AI', '🤖 Artificial Intelligence'),
        ('ML', '📊 Machine Learning'),
        ('DL', '🧠 Deep Learning'),
        ('WEB', '🌐 Web Development'),
        ('DATA', '📈 Data Science'),
        ('MOBILE', '📱 Mobile Development'),
        ('CYBER', '🔒 Cybersecurity'),
        ('BLOCKCHAIN', '⛓️ Blockchain'),
        ('IOT', '🏠 Internet of Things'),
        ('GAME', '🎮 Game Development'),
        ('CLOUD', '☁️ Cloud Computing'),
        ('DEVOPS', '⚙️ DevOps'),
        ('FULLSTACK', '🚀 Full Stack'),
        ('DESKTOP', '🖥️ Desktop'),
    ]
    
    DIFFICULTY_CHOICES = [
        (1, '🟢 Very Easy'),
        (2, '🟡 Easy'),
        (3, '🟠 Medium'),
        (4, '🔴 Hard'),
        (5, '⚫ Very Hard'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ARCHIVED', 'Archived'),
        ('TRENDING', 'Trending'),
    ]
    
    # Basic Info
    title = models.CharField(max_length=200, db_index=True)
    short_description = models.TextField()
    full_description = models.TextField(blank=True)
    overview = models.TextField(blank=True, help_text="High-level overview of the project")
    
    # Categorization
    domain = models.CharField(max_length=20, choices=DOMAIN_CHOICES, db_index=True)
    interests = models.ManyToManyField(Interest, blank=True, related_name='projects')
    required_skills = models.ManyToManyField(Skill, blank=True, related_name='required_in_projects')
    optional_skills = models.ManyToManyField(Skill, blank=True, related_name='optional_in_projects', help_text="Nice-to-have skills")
    aspects = models.ManyToManyField(Aspect, blank=True, related_name='projects', help_text="Project aspects: Frontend, Backend, Database, AI/ML, Deployment, etc.")
    
    # Difficulty & Feasibility
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=3)
    estimated_hours = models.IntegerField(null=True, blank=True, help_text="Total hours to complete")
    estimated_weeks = models.IntegerField(null=True, blank=True, help_text="Weeks to complete (calculated from hours)")
    team_size_recommended = models.IntegerField(default=1, help_text="Recommended team size (1-5)")
    min_semester = models.IntegerField(default=3, help_text="Minimum recommended semester")
    
    # Technologies & Requirements
    required_technologies = models.TextField(default='[]', help_text="JSON array of required technologies")
    learning_outcomes = models.TextField(default='[]', help_text="JSON array of learning outcomes")
    skill_gap_analysis = models.TextField(default='{}', help_text="JSON mapping of skills to learning time")
    learning_roadmap = models.TextField(default='[]', help_text="JSON array of learning steps")
    
    # Resources
    dataset_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    github_stars = models.IntegerField(default=0, help_text="GitHub stars count")
    research_paper_url = models.URLField(blank=True, null=True)
    youtube_tutorial = models.URLField(blank=True, null=True)
    documentation_url = models.URLField(blank=True, null=True)
    
    # Approval & Scoring
    supervisor_approved = models.BooleanField(default=False, db_index=True)
    supervisor_recommendation_count = models.IntegerField(default=0, help_text="How many times recommended by supervisors")
    supervisor_approval_rate = models.FloatField(default=0.0, help_text="Percentage of approvals (0.0-1.0)")
    popularity_score = models.IntegerField(default=0, db_index=True)
    success_probability = models.FloatField(default=0.5, help_text="Project success rate (0.0-1.0)")
    completion_rate = models.FloatField(default=0.0, help_text="Historical completion rate (0-100)")
    
    # Advanced Scoring
    trending_score = models.FloatField(default=0.0, help_text="Trending calculation")
    similarity_topics = models.TextField(default='[]', help_text="JSON array of similar project IDs")
    
    # Status & Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, blank=True, help_text="Creator/Source")
    
    def __str__(self):
        return self.title
    
    def get_required_skills_list(self):
        return list(self.required_skills.values_list('name', flat=True))
    
    def get_optional_skills_list(self):
        return list(self.optional_skills.values_list('name', flat=True))
    
    def get_interests_list(self):
        return list(self.interests.values_list('name', flat=True))
    
    def get_aspects_list(self):
        """Returns list of aspect names"""
        return list(self.aspects.values_list('name', flat=True))
    
    def get_required_technologies(self):
        """Parse required technologies from JSON"""
        try:
            return json.loads(self.required_technologies)
        except:
            return []
    
    def get_learning_outcomes(self):
        """Parse learning outcomes from JSON"""
        try:
            return json.loads(self.learning_outcomes)
        except:
            return []
    
    def get_learning_roadmap(self):
        """Parse learning roadmap from JSON"""
        try:
            return json.loads(self.learning_roadmap)
        except:
            return []
    
    def get_skill_gap_analysis(self):
        """Parse skill gap analysis from JSON"""
        try:
            return json.loads(self.skill_gap_analysis)
        except:
            return {}
    
    def get_similar_projects(self):
        """Get similar project IDs"""
        try:
            return json.loads(self.similarity_topics)
        except:
            return []
    
    def aspect_coverage_count(self):
        """Returns number of aspects covered"""
        return self.aspects.count()
    
    def has_full_aspect_coverage(self, required_count=4):
        """Check if project covers required number of aspects"""
        return self.aspect_coverage_count() >= required_count
    
    def calculate_supervisor_confidence_score(self):
        """Calculate supervisor approval confidence (0-100)"""
        approval_rate_score = self.supervisor_approval_rate * 100  # 0-100
        recommendation_score = min(self.supervisor_recommendation_count * 10, 50)  # Max 50 points
        base_score = (approval_rate_score * 0.6) + (recommendation_score * 0.4)
        return round(min(base_score, 100), 1)

    def requires_gpu(self):
        """Check if project requires GPU"""
        gpu_keywords = {
            'tensorflow', 'pytorch', 'cuda', 'deep learning', 'computer vision',
            'nlp', 'vision', 'gpu', 'transformers', 'llm', 'huggingface', 'keras'
        }
        project_terms = {skill.name.lower() for skill in self.required_skills.all()}
        project_terms.update({tech.lower() for tech in self.get_required_technologies()})
        
        if self.domain in {'AI', 'DL', 'ML'}:
            return True
        return bool(project_terms & gpu_keywords)
    
    def calculate_trending_score(self):
        """Calculate trending score based on recent recommendations"""
        from datetime import timedelta
        recent_date = timezone.now() - timedelta(days=30)
        recent_recommendations = Recommendation.objects.filter(
            project=self,
            recommended_at__gte=recent_date
        ).count()
        
        self.trending_score = round(
            (self.popularity_score * 0.4) +
            (recent_recommendations * 0.6),
            1
        )
        self.save()
        return self.trending_score
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['status']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['supervisor_approved']),
            models.Index(fields=['min_semester']),
        ]

class Recommendation(models.Model):
    CONFIDENCE_LEVELS = [
        ('low', '🔴 Low Confidence'),
        ('medium', '🟡 Medium Confidence'),
        ('high', '🟢 High Confidence'),
        ('very_high', '✅ Very High Confidence'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='recommendations')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='recommendations')
    
    # Scoring Metrics
    match_score = models.FloatField(help_text="Overall match score (0-100)")
    skill_match = models.FloatField(help_text="Skill matching score (0-100)")
    interest_match = models.FloatField(help_text="Interest matching score (0-100)")
    difficulty_match = models.FloatField(help_text="Difficulty suitability (0-100)")
    time_feasibility = models.FloatField(default=100.0, help_text="Time availability match (0-100)")
    gpu_factor = models.FloatField(default=1.0, help_text="GPU requirement factor")
    
    # Advanced Scores
    aspect_coverage_score = models.FloatField(default=0.0, help_text="Score based on aspect coverage (0-100)")
    supervisor_confidence_score = models.FloatField(default=0.0, help_text="Supervisor approval confidence (0-100)")
    final_score = models.FloatField(default=0.0, help_text="Final combined recommendation score (0-100)")
    confidence_level = models.CharField(max_length=20, choices=CONFIDENCE_LEVELS, default='medium')
    
    # Additional Info
    skill_gaps = models.TextField(default='[]', help_text="JSON array of missing skills")
    suggested_learning_path = models.TextField(default='[]', help_text="JSON array of learning steps")
    match_reasons = models.TextField(default='[]', help_text="JSON array of why this project was recommended")
    
    # Tracking
    recommended_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    was_accepted = models.BooleanField(default=False)
    was_viewed = models.BooleanField(default=False)
    feedback_score = models.IntegerField(null=True, blank=True, help_text="User feedback rating (1-5)")
    
    class Meta:
        unique_together = ['student', 'project']
        ordering = ['-final_score', '-recommended_at']
        indexes = [
            models.Index(fields=['student', '-final_score']),
            models.Index(fields=['project', '-final_score']),
            models.Index(fields=['confidence_level']),
        ]
    
    def __str__(self):
        return f"{self.student.name} → {self.project.title} ({self.final_score}%)"
    
    def get_skill_gaps(self):
        """Parse skill gaps from JSON"""
        try:
            return json.loads(self.skill_gaps)
        except:
            return []
    
    def get_suggested_learning_path(self):
        """Parse suggested learning path from JSON"""
        try:
            return json.loads(self.suggested_learning_path)
        except:
            return []
    
    def get_match_reasons(self):
        """Parse match reasons from JSON"""
        try:
            return json.loads(self.match_reasons)
        except:
            return []
    
    def calculate_final_score(self):
        """
        Calculate final recommendation score with advanced weighting:
        - Match Score: 25% (skill + interest combined)
        - Difficulty Match: 15% (difficulty suitability)
        - Time Feasibility: 10% (time available)
        - Aspect Coverage: 20% (project comprehensiveness)
        - Supervisor Confidence: 30% (proven project quality)
        """
        self.final_score = round(
            (self.match_score * 0.25) +
            (self.difficulty_match * 0.15) +
            (self.time_feasibility * 0.10) +
            (self.aspect_coverage_score * 0.20) +
            (self.supervisor_confidence_score * 0.30) * 
            self.gpu_factor,
            1
        )
        
        # Determine confidence level
        if self.final_score >= 85:
            self.confidence_level = 'very_high'
        elif self.final_score >= 70:
            self.confidence_level = 'high'
        elif self.final_score >= 50:
            self.confidence_level = 'medium'
        else:
            self.confidence_level = 'low'
        
        return self.final_score


class ProjectComparison(models.Model):
    """Track project comparisons for analytics"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='comparisons')
    project1 = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='compared_as_first')
    project2 = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='compared_as_second')
    winner_project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='wins')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']


class RecommendationHistory(models.Model):
    """Track recommendation history for each student"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='recommendation_history')
    recommendations = models.ManyToManyField(Recommendation, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    filters_applied = models.TextField(default='{}', help_text="JSON of filters used")
    total_shown = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-timestamp']
    
    def get_filters(self):
        """Parse filters from JSON"""
        try:
            return json.loads(self.filters_applied)
        except:
            return {}


class ProjectAnalytics(models.Model):
    """Track project performance and analytics"""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='analytics')
    total_recommendations = models.IntegerField(default=0)
    total_views = models.IntegerField(default=0)
    acceptance_rate = models.FloatField(default=0.0, help_text="Percentage of students who accepted recommendation (0-100)")
    average_feedback_score = models.FloatField(default=0.0)
    trending_rank = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Project Analytics"
    
    def __str__(self):
        return f"Analytics for {self.project.title}"
    
    def update_acceptance_rate(self):
        """Calculate acceptance rate from recommendations"""
        total = self.project.recommendations.count()
        if total == 0:
            self.acceptance_rate = 0.0
        else:
            accepted = self.project.recommendations.filter(was_accepted=True).count()
            self.acceptance_rate = round((accepted / total) * 100, 1)
        self.save()


class LearningPath(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='learning_paths')
    prerequisite = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependent_skills')
    estimated_weeks = models.IntegerField(default=2)
    difficulty_level = models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')], default=1)
    youtube_url = models.URLField(blank=True, null=True)
    udemy_url = models.URLField(blank=True, null=True)
    coursera_url = models.URLField(blank=True, null=True)
    documentation_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['skill']
    
    def __str__(self):
        return f"Learn {self.skill.name}"