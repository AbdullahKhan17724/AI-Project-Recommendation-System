from django.contrib import admin
from .models import Skill, Interest, Student, Project, Recommendation, LearningPath, Aspect

@admin.register(Aspect)
class AspectAdmin(admin.ModelAdmin):
    list_display = ['emoji', 'name', 'description']
    search_fields = ['name']

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    search_fields = ['name']
    list_filter = ['category']

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'roll_number', 'semester', 'experience_level', 'created_at']
    list_filter = ['semester', 'experience_level', 'department', 'has_gpu']
    search_fields = ['name', 'roll_number', 'email']
    filter_horizontal = ['skills', 'interests']
    readonly_fields = ['created_at']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'domain', 'difficulty', 'supervisor_approved', 'aspect_count', 'supervisor_confidence_score', 'status']
    list_filter = ['domain', 'difficulty', 'supervisor_approved', 'status', 'aspects']
    search_fields = ['title', 'short_description']
    filter_horizontal = ['required_skills', 'interests', 'aspects']
    list_editable = ['supervisor_approved']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'short_description', 'full_description')
        }),
        ('Categorization', {
            'fields': ('domain', 'interests', 'required_skills', 'aspects')
        }),
        ('Difficulty & Resources', {
            'fields': ('difficulty', 'estimated_hours', 'team_size_recommended')
        }),
        ('Links', {
            'fields': ('dataset_url', 'github_url', 'research_paper_url', 'youtube_tutorial'),
            'classes': ('collapse',)
        }),
        ('Supervisor Approval & Scoring', {
            'fields': ('supervisor_approved', 'supervisor_recommendation_count', 'supervisor_approval_rate'),
            'description': 'Track supervisor approval metrics for confidence scoring'
        }),
        ('Status', {
            'fields': ('status', 'popularity_score')
        }),
    )
    
    def aspect_count(self, obj):
        """Display aspect coverage count"""
        count = obj.aspect_coverage_count()
        return f"📊 {count}/5"
    aspect_count.short_description = "Aspect Coverage"
    
    def supervisor_confidence_score(self, obj):
        """Display supervisor confidence score"""
        score = obj.calculate_supervisor_confidence_score()
        if score >= 80:
            color_code = '✅'
        elif score >= 60:
            color_code = '⚠️'
        else:
            color_code = '❌'
        return f"{color_code} {score}%"
    supervisor_confidence_score.short_description = "Supervisor Confidence"

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['student', 'project', 'final_score', 'match_score', 'aspect_coverage_score', 'supervisor_confidence_score', 'was_accepted']
    list_filter = ['was_accepted', 'recommended_at', 'project__domain']
    search_fields = ['student__name', 'project__title']
    readonly_fields = ['recommended_at', 'final_score']
    fieldsets = (
        ('Recommendation', {
            'fields': ('student', 'project')
        }),
        ('Matching Scores', {
            'fields': ('match_score', 'skill_match', 'interest_match', 'difficulty_match')
        }),
        ('Enhanced Scoring', {
            'fields': ('aspect_coverage_score', 'supervisor_confidence_score', 'final_score'),
            'description': 'New metrics for improved recommendations'
        }),
        ('Meta', {
            'fields': ('recommended_at', 'was_accepted')
        }),
    )

@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ['skill', 'prerequisite', 'estimated_weeks']