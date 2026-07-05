import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recommender.settings')
django.setup()

from projects.models import Skill, Interest, Project, Aspect

print("🚀 SETTING UP DATABASE WITH 100+ SKILLS AND 500+ PROJECTS")
print("=" * 60)

# Clear existing data
Aspect.objects.all().delete()
Skill.objects.all().delete()
Interest.objects.all().delete()
Project.objects.all().delete()
print("🔄 Cleared existing data")

# ============================================
# CREATE 100+ SKILLS
# ============================================
print("\n📚 Creating 100+ skills...")

skills_data = {
    'Programming Languages': [
        'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Go', 'Rust', 'Ruby', 'PHP', 'Swift',
        'Kotlin', 'TypeScript', 'Scala', 'R', 'MATLAB', 'Perl', 'Lua', 'Dart', 'HTML', 'CSS',
        'SQL', 'NoSQL', 'GraphQL', 'Bash', 'PowerShell'
    ],
    'Frameworks & Libraries': [
        'React', 'Angular', 'Vue.js', 'Django', 'Flask', 'FastAPI', 'Spring Boot', 'Express.js',
        'Node.js', 'Next.js', 'Nuxt.js', 'Svelte', 'jQuery', 'Bootstrap', 'Tailwind CSS',
        'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn', 'Pandas', 'NumPy', 'Matplotlib',
        'OpenCV', 'NLTK', 'spaCy', 'Transformers', 'HuggingFace', 'LangChain'
    ],
    'Mobile Development': [
        'Flutter', 'React Native', 'Android', 'iOS', 'Xamarin', 'Ionic', 'Cordova', 'SwiftUI'
    ],
    'Database': [
        'PostgreSQL', 'MySQL', 'SQLite', 'MongoDB', 'Redis', 'Cassandra', 'Elasticsearch', 'Firebase'
    ],
    'DevOps & Cloud': [
        'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Terraform', 'Ansible', 'Jenkins',
        'GitHub Actions', 'GitLab CI', 'CircleCI', 'Prometheus', 'Grafana', 'ELK Stack'
    ],
    'Blockchain': [
        'Solidity', 'Web3', 'Ethereum', 'Smart Contracts', 'Hyperledger', 'Bitcoin', 'Rust'
    ],
    'Game Development': [
        'Unity', 'Unreal Engine', 'Godot', 'CryEngine', 'Phaser', 'Pygame'
    ],
    'Cybersecurity': [
        'Cryptography', 'Network Security', 'Penetration Testing', 'OWASP', 'Nmap', 'Wireshark',
        'Metasploit', 'Burp Suite'
    ],
    'Data Science & AI': [
        'Machine Learning', 'Deep Learning', 'Computer Vision', 'NLP', 'Reinforcement Learning',
        'LLM', 'RAG', 'LangGraph', 'CrewAI', 'AutoGPT', 'Vector Database', 'ChromaDB'
    ],
    'IoT & Hardware': [
        'Arduino', 'Raspberry Pi', 'ESP8266', 'ESP32', 'Sensors', 'MQTT', 'Zigbee', 'LoRa'
    ]
}

skills_count = 0
for category, skill_list in skills_data.items():
    for skill_name in skill_list:
        skill, created = Skill.objects.get_or_create(name=skill_name, defaults={'category': category})
        if created:
            skills_count += 1
            print(f"  ✅ Added: {skill_name} ({category})")

print(f"\n✅ Total skills created: {skills_count}")

# ============================================
# CREATE INTERESTS
# ============================================
print("\n🎯 Creating interests...")

interests_list = [
    'Web Development', 'Artificial Intelligence', 'Data Science', 'Machine Learning',
    'Deep Learning', 'Mobile App Development', 'Game Development', 'Cybersecurity',
    'Blockchain', 'Cloud Computing', 'DevOps', 'Internet of Things', 'Augmented Reality',
    'Virtual Reality', 'Quantum Computing', 'Bioinformatics', 'FinTech', 'EdTech',
    'Healthcare', 'E-commerce', 'Social Media', 'Automation', 'Robotics'
]

interests_count = 0
for interest_name in interests_list:
    interest, created = Interest.objects.get_or_create(name=interest_name)
    if created:
        interests_count += 1
        print(f"  ✅ Added interest: {interest_name}")

print(f"\n✅ Total interests created: {interests_count}")

# ============================================
# CREATE ASPECTS
# ============================================
print("\n🧩 Creating project aspects...")

aspect_names = [
    'Frontend', 'Backend', 'Database', 'AI/ML', 'Deployment', 'Security',
    'Mobile', 'Cloud', 'Networking', 'Analytics', 'Hardware', 'UI/UX'
]

aspects = []
for name in aspect_names:
    aspect, created = Aspect.objects.get_or_create(name=name, defaults={'description': f'{name} work area', 'emoji': '📌'})
    aspects.append(aspect)
    if created:
        print(f"  ✅ Added aspect: {name}")

# ============================================
# CREATE 520 PROJECTS
# ============================================
print("\n📁 Creating 520 project ideas...")

all_interests = list(Interest.objects.all())
all_skills = list(Skill.objects.all())
all_aspects = list(Aspect.objects.all())

project_topics = {
    'AI': [
        'Chatbot', 'Image Classifier', 'Speech Analyzer', 'Text Summarizer', 'Recommendation Engine',
        'Anomaly Detector', 'Question Answering System', 'Medical Assistant', 'Customer Service Bot',
        'Sales Forecaster', 'Fraud Detector', 'Sentiment Analyzer', 'Essay Grader',
        'Voice Translator', 'Disease Predictor'
    ],
    'ML': [
        'Credit Scorer', 'Churn Predictor', 'Forecasting Model', 'Clustering Hub',
        'Regression Studio', 'Classifier Dashboard', 'Pattern Finder', 'Trend Analyzer'
    ],
    'DL': [
        'Vision System', 'Language Model', 'Object Detector', 'Speech Synthesizer',
        'Deep Predictor', 'GAN Artist', 'Style Transfer', 'Image Segmenter'
    ],
    'WEB': [
        'Marketplace', 'Social Network', 'Portfolio Site', 'Learning Platform', 'Booking System',
        'Job Portal', 'Blog Engine', 'Restaurant System', 'Community Hub', 'Service Dashboard'
    ],
    'DATA': [
        'Analytics Dashboard', 'Business Intelligence Tool', 'Data Pipeline', 'Report Generator',
        'Data Cleansing App', 'Visualization Studio', 'Survey Analyzer', 'Data Warehouse'
    ],
    'MOBILE': [
        'Fitness App', 'Food Delivery App', 'Event Planner', 'Budget Tracker', 'Chat App',
        'Travel Guide', 'Habit Tracker', 'Study Companion', 'Health Monitor', 'Marketplace App'
    ],
    'GAME': [
        'Platformer', 'Puzzle Quest', 'Racing Game', 'Strategy Simulator', 'Adventure Game',
        'Arcade Shooter', 'Card Battle', 'Trivia Game', 'Role Playing Game'
    ],
    'CYBER': [
        'Network Scanner', 'Password Vault', 'Penetration Tester', 'Encryption Tool',
        'Threat Detector', 'Firewall Manager', 'Security Dashboard', 'Privacy Monitor'
    ],
    'BLOCKCHAIN': [
        'Crypto Wallet', 'Smart Contract Auditor', 'Token Exchange', 'NFT Marketplace',
        'Supply Chain Tracker', 'Decentralized App', 'DAO Platform', 'Voting System'
    ],
    'CLOUD': [
        'Deployment Manager', 'Monitoring Dashboard', 'CI/CD Pipeline', 'Serverless Portal',
        'Cloud Cost Analyzer', 'Backup System', 'DevOps Assistant'
    ],
    'DEVOPS': [
        'Infrastructure Automator', 'Build Monitor', 'Release Tracker', 'Container Manager',
        'Log Aggregator', 'Pipeline Optimizer'
    ],
    'IOT': [
        'Smart Home Hub', 'Environmental Monitor', 'Smart Agriculture', 'Wearable Tracker',
        'IoT Dashboard', 'Sensor Network Controller'
    ]
}

project_suffixes = ['System', 'Platform', 'Assistant', 'Hub', 'Dashboard', 'Analyzer', 'Toolkit', 'Studio', 'Manager', 'Pro']

titles_used = set()
for idx in range(1, 521):
    domain = random.choice(list(project_topics.keys()))
    base_name = random.choice(project_topics[domain])
    suffix = random.choice(project_suffixes)
    title = f"{base_name} {suffix} {idx}"
    if title in titles_used:
        title = f"{title} Edition"
    titles_used.add(title)

    difficulty = random.choices([1, 2, 3, 4, 5], weights=[10, 22, 34, 24, 10], k=1)[0]
    if domain in ['WEB', 'MOBILE']:
        difficulty = random.choices([1, 2, 3, 4], weights=[18, 34, 30, 18], k=1)[0]
    elif domain in ['AI', 'ML', 'DL', 'DATA']:
        difficulty = random.choices([2, 3, 4, 5], weights=[12, 34, 34, 20], k=1)[0]
    elif domain in ['CYBER', 'BLOCKCHAIN', 'CLOUD', 'DEVOPS', 'IOT']:
        difficulty = random.choices([2, 3, 4], weights=[24, 44, 32], k=1)[0]

    estimated_hours = random.choice([80, 100, 120, 140, 160, 180, 200])
    search_query = title.replace(' ', '+')
    dataset_url = f'https://www.kaggle.com/datasets?search={search_query}'
    youtube_tutorial = f'https://www.youtube.com/results?search_query=learn+{search_query}'
    github_url = f'https://github.com/search?q={search_query}' if random.random() < 0.55 else ''
    supervisor_approved = idx <= 320 or random.random() < 0.35
    supervisor_recommendation_count = random.randint(5, 60)
    supervisor_approval_rate = round(random.uniform(0.55, 1.0), 2)
    popularity_score = random.randint(20, 100)

    project = Project.objects.create(
        title=title,
        short_description=f"A complete {title.lower()} idea designed for final year projects.",
        full_description=f"Detailed project idea for {title}. Includes dataset, open-source references, and suggested tools.",
        domain=domain,
        difficulty=difficulty,
        estimated_hours=estimated_hours,
        team_size_recommended=random.choice([1, 2, 3, 4]),
        dataset_url=dataset_url,
        github_url=github_url,
        youtube_tutorial=youtube_tutorial,
        supervisor_approved=supervisor_approved,
        supervisor_recommendation_count=supervisor_recommendation_count,
        supervisor_approval_rate=supervisor_approval_rate,
        popularity_score=popularity_score,
        status='ACTIVE'
    )

    project.interests.add(*random.sample(all_interests, min(3, len(all_interests))))
    project.required_skills.add(*random.sample(all_skills, min(4, len(all_skills))))
    project.aspects.add(*random.sample(all_aspects, min(4, len(all_aspects))))

    if idx % 50 == 0:
        print(f"  📁 Created {idx} projects...")

print(f"\n✅ Total projects created: {Project.objects.count()}")
print(f"✅ Total supervisor-approved projects: {Project.objects.filter(supervisor_approved=True).count()}")

print("\n" + "=" * 60)
print("🎉 DATABASE SETUP COMPLETE!")
print("=" * 60)
print(f"📚 Skills: {Skill.objects.count()}")
print(f"🎯 Interests: {Interest.objects.count()}")
print(f"📁 Projects: {Project.objects.count()}")
print(f"⭐ Supervisor approved projects: {Project.objects.filter(supervisor_approved=True).count()}")
print("\n✅ Run 'python manage.py runserver' to start the application")
