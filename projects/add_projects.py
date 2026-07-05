import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recommender.settings')
django.setup()

from projects.models import Skill, Interest, Project

print("🚀 ADDING 200+ PROJECTS")
print("="*40)

# Get existing skills and interests
all_skills = list(Skill.objects.all())
all_interests = list(Interest.objects.all())

if len(all_skills) == 0:
    print("❌ No skills found! Run setup first.")
    exit()

print(f"📚 Found {len(all_skills)} skills")
print(f"🎯 Found {len(all_interests)} interests")

# Project templates
project_titles = [
    "AI-Powered Chatbot", "E-Commerce Platform", "Face Recognition System",
    "Stock Price Predictor", "Fake News Detector", "Image Classifier",
    "Recommendation Engine", "Speech Recognition", "Object Detection System",
    "Text Summarizer", "Sentiment Analyzer", "Handwriting Recognition",
    "Anomaly Detection", "Question Answering System", "AI Code Reviewer",
    "Medical Diagnosis Assistant", "Sales Forecasting", "Customer Churn Analysis",
    "Heart Disease Prediction", "Credit Risk Analysis", "COVID-19 Dashboard",
    "Market Basket Analysis", "Customer Segmentation", "Employee Attrition",
    "Fitness Tracker App", "Food Delivery App", "Expense Manager",
    "News Reader App", "Music Player App", "To-Do List App",
    "Weather App", "E-commerce App", "Chat App", "Video Player App",
    "Network Scanner", "Password Manager", "Phishing Detector",
    "Vulnerability Scanner", "Encryption Tool", "Intrusion Detection",
    "Malware Classifier", "Keylogger Detector", "Voting System",
    "Cryptocurrency Wallet", "NFT Marketplace", "Supply Chain Tracker",
    "Smart Contract Auditor", "Crypto Price Tracker", "2D Platformer",
    "Puzzle Game", "Snake Game", "Space Shooter", "Card Game",
    "Racing Game", "Smart Home System", "Weather Station", "Smart Irrigation",
    "Air Quality Monitor", "Smart Parking", "Health Monitor", "Traffic Light",
    "Home Security System", "Portfolio Website", "Blog Platform", "Task Manager",
    "Learning Management System", "Job Portal", "Hotel Booking", "Real Estate Portal",
    "Discussion Forum", "Online Code Compiler", "URL Shortener", "News Aggregator",
    "Social Media Dashboard", "Hospital Management", "Library Management"
]

projects_created = 0
for title in project_titles:
    # Determine domain
    domain = 'WEB'
    if any(k in title for k in ['AI', 'Face', 'Stock', 'Fake', 'Image', 'Speech', 'Object', 'Chatbot', 'Recommendation']):
        domain = 'AI'
    elif any(k in title for k in ['Heart', 'Diabetes', 'Sales', 'Customer', 'Credit', 'Market', 'Segmentation']):
        domain = 'DATA'
    elif any(k in title for k in ['App', 'Mobile', 'Fitness', 'Food', 'Music', 'Weather', 'Chat', 'Video']):
        domain = 'MOBILE'
    elif any(k in title for k in ['Game', 'Platformer', 'Puzzle', 'Shooter', 'Racing']):
        domain = 'GAME'
    elif any(k in title for k in ['Scanner', 'Password', 'Phishing', 'Encryption', 'Intrusion', 'Malware']):
        domain = 'CYBER'
    elif any(k in title for k in ['Blockchain', 'Wallet', 'NFT', 'Voting', 'Crypto']):
        domain = 'BLOCKCHAIN'
    elif any(k in title for k in ['Smart', 'Weather', 'Air', 'Parking', 'Traffic', 'Security']):
        domain = 'IOT'
    
    # Create project
    proj, created = Project.objects.get_or_create(
        title=title,
        defaults={
            'short_description': f"A comprehensive {title.lower()} project for final year students",
            'domain': domain,
            'difficulty': random.randint(2, 5),
            'estimated_hours': random.randint(60, 200),
            'status': 'ACTIVE',
            'supervisor_approved': projects_created < 50
        }
    )
    
    if created:
        # Add random interests
        for interest in random.sample(all_interests, min(2, len(all_interests))):
            proj.interests.add(interest)
        
        # Add random skills
        for skill in random.sample(all_skills, min(3, len(all_skills))):
            proj.required_skills.add(skill)
        
        projects_created += 1
        if projects_created % 20 == 0:
            print(f"✅ Added {projects_created} projects...")

print(f"\n🎉 TOTAL PROJECTS ADDED: {projects_created}")
print(f"📊 Total in database: {Project.objects.count()}")