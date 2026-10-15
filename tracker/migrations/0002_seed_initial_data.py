from django.db import migrations


def seed_initial_data(apps, schema_editor):
    Project = apps.get_model('tracker', 'Project')
    Issue = apps.get_model('tracker', 'Issue')
    Comment = apps.get_model('tracker', 'Comment')

    # Seed Project 1
    p1, _ = Project.objects.update_or_create(
        id=1,
        defaults={
            'name': 'Core Platform',
            'description': 'Main web application, authentication system, and backend APIs.',
        }
    )

    # Seed Project 2
    p2, _ = Project.objects.update_or_create(
        id=2,
        defaults={
            'name': 'Mobile Application',
            'description': 'Cross-platform mobile client for iOS and Android devices.',
        }
    )

    # Seed Project 3
    p3, _ = Project.objects.update_or_create(
        id=3,
        defaults={
            'name': 'Cloud Infrastructure',
            'description': 'Kubernetes clusters, CI/CD pipelines, and cloud monitoring.',
        }
    )

    # Seed Issues for Project 1
    i1, _ = Issue.objects.update_or_create(
        id=1,
        defaults={
            'title': 'Implement user authentication with OAuth2',
            'description': 'Allow users to sign in via Google and GitHub OAuth providers.',
            'status': 'To Do',
            'project': p1,
        }
    )

    i2, _ = Issue.objects.update_or_create(
        id=2,
        defaults={
            'title': 'Add dark mode theme support',
            'description': 'Create CSS variables and toggle for high-contrast dark theme.',
            'status': 'To Do',
            'project': p1,
        }
    )

    i3, _ = Issue.objects.update_or_create(
        id=3,
        defaults={
            'title': 'Optimize database queries on project board',
            'description': 'Use select_related and prefetch_related to eliminate N+1 queries.',
            'status': 'In Progress',
            'project': p1,
        }
    )

    i4, _ = Issue.objects.update_or_create(
        id=4,
        defaults={
            'title': 'Write comprehensive API documentation',
            'description': 'Document all REST and HTMX endpoints with OpenAPI specs.',
            'status': 'In Progress',
            'project': p1,
        }
    )

    i5, _ = Issue.objects.update_or_create(
        id=5,
        defaults={
            'title': 'Setup project repository and Docker Compose',
            'description': 'Configure multi-container setup with Django, PostgreSQL, and health checks.',
            'status': 'Done',
            'project': p1,
        }
    )

    i6, _ = Issue.objects.update_or_create(
        id=6,
        defaults={
            'title': 'Configure PostgreSQL database schema',
            'description': 'Implement Project, Issue, and Comment models with foreign keys.',
            'status': 'Done',
            'project': p1,
        }
    )

    # Seed Issues for Project 2
    Issue.objects.update_or_create(
        id=7,
        defaults={
            'title': 'Implement offline mode caching',
            'description': 'Use local SQLite store for offline issue viewing and drafts.',
            'status': 'To Do',
            'project': p2,
        }
    )

    Issue.objects.update_or_create(
        id=8,
        defaults={
            'title': 'Push notifications for issue status changes',
            'description': 'Integrate Firebase Cloud Messaging for instant status updates.',
            'status': 'In Progress',
            'project': p2,
        }
    )

    Issue.objects.update_or_create(
        id=9,
        defaults={
            'title': 'Design splash screen and app icons',
            'description': 'Create vector assets matching the new design guidelines.',
            'status': 'Done',
            'project': p2,
        }
    )

    # Seed Comments
    Comment.objects.update_or_create(
        id=1,
        defaults={
            'issue': i1,
            'content': 'We should prioritize Google OAuth first as most users request it.',
        }
    )

    Comment.objects.update_or_create(
        id=2,
        defaults={
            'issue': i1,
            'content': 'Ensure PKCE is enabled for maximum security.',
        }
    )

    Comment.objects.update_or_create(
        id=3,
        defaults={
            'issue': i3,
            'content': 'Initial profiling shows 18 redundant queries on large boards.',
        }
    )


def rollback_initial_data(apps, schema_editor):
    Project = apps.get_model('tracker', 'Project')
    Project.objects.filter(id__in=[1, 2, 3]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_initial_data, rollback_initial_data),
    ]
