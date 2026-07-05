from django.core.management.base import BaseCommand
from projects.models import Aspect

class Command(BaseCommand):
    help = 'Initialize project aspects (Frontend, Backend, Database, AI/ML, Deployment)'

    def handle(self, *args, **options):
        aspects = [
            {
                'name': 'Frontend',
                'description': 'User interface and client-side development',
                'emoji': '🎨'
            },
            {
                'name': 'Backend',
                'description': 'Server-side logic and APIs',
                'emoji': '⚙️'
            },
            {
                'name': 'Database',
                'description': 'Data storage and management',
                'emoji': '🗄️'
            },
            {
                'name': 'AI/ML',
                'description': 'Artificial Intelligence and Machine Learning',
                'emoji': '🤖'
            },
            {
                'name': 'Deployment',
                'description': 'DevOps, cloud deployment, and infrastructure',
                'emoji': '🚀'
            },
            {
                'name': 'Mobile',
                'description': 'Mobile application development',
                'emoji': '📱'
            },
            {
                'name': 'Security',
                'description': 'Security, encryption, and authentication',
                'emoji': '🔒'
            },
            {
                'name': 'Testing',
                'description': 'Testing, QA, and debugging',
                'emoji': '✅'
            },
        ]
        
        created_count = 0
        for aspect_data in aspects:
            aspect, created = Aspect.objects.get_or_create(
                name=aspect_data['name'],
                defaults={
                    'description': aspect_data['description'],
                    'emoji': aspect_data['emoji']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Created: {aspect.emoji} {aspect.name}'))
            else:
                self.stdout.write(f'⏭️  Already exists: {aspect.emoji} {aspect.name}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Total aspects initialized: {created_count}'))
