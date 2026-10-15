from django.test import TestCase, Client
from django.urls import reverse
from django.db import connection
from tracker.models import Project, Issue, Comment


class DatabaseSchemaTests(TestCase):
    """
    Contract 2: Verify PostgreSQL/ORM schema for tracker_project, tracker_issue, tracker_comment.
    """
    def test_database_tables_exist(self):
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)
            self.assertIn('tracker_project', tables)
            self.assertIn('tracker_issue', tables)
            self.assertIn('tracker_comment', tables)

    def test_table_columns_and_foreign_keys(self):
        with connection.cursor() as cursor:
            project_cols = [col.name for col in connection.introspection.get_table_description(cursor, 'tracker_project')]
            self.assertIn('id', project_cols)
            self.assertIn('name', project_cols)
            self.assertIn('description', project_cols)

            issue_cols = [col.name for col in connection.introspection.get_table_description(cursor, 'tracker_issue')]
            self.assertIn('id', issue_cols)
            self.assertIn('title', issue_cols)
            self.assertIn('description', issue_cols)
            self.assertIn('status', issue_cols)
            self.assertIn('project_id', issue_cols)

            comment_cols = [col.name for col in connection.introspection.get_table_description(cursor, 'tracker_comment')]
            self.assertIn('id', comment_cols)
            self.assertIn('content', comment_cols)
            self.assertIn('issue_id', comment_cols)


class IssueTrackerStandardTests(TestCase):
    """
    Contract 3, 4, 5, 6: Tests for standard SSR requests (No-JavaScript).
    """
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(
            name='Test Project',
            description='Test Project Description'
        )
        self.issue_todo = Issue.objects.create(
            title='Implement Login Feature',
            description='Login with email and password',
            status=Issue.STATUS_TODO,
            project=self.project
        )
        self.issue_in_progress = Issue.objects.create(
            title='Refactor Database Queries',
            description='Improve query performance',
            status=Issue.STATUS_IN_PROGRESS,
            project=self.project
        )
        self.issue_done = Issue.objects.create(
            title='Initial Deployment',
            description='Deploy to production environment',
            status=Issue.STATUS_DONE,
            project=self.project
        )

    def test_project_board_standard_response(self):
        """
        Contract 3: GET /projects/{project_id}/ returns full HTML document (200 OK)
        with distinct sections for 'To Do', 'In Progress', and 'Done', containing issue titles.
        """
        response = self.client.get(f'/projects/{self.project.id}/')
        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Verify full HTML document
        self.assertIn('<html', content.lower())
        self.assertIn('<body', content.lower())

        # Verify distinct status sections exist
        self.assertIn('To Do', content)
        self.assertIn('In Progress', content)
        self.assertIn('Done', content)

        # Verify issue titles are rendered under their respective sections
        self.assertIn('Implement Login Feature', content)
        self.assertIn('Refactor Database Queries', content)
        self.assertIn('Initial Deployment', content)

    def test_create_issue_standard_post(self):
        """
        Contract 4: POST /projects/{project_id}/issues/create/
        Standard POST returns 302 redirect to board page and creates row in DB.
        """
        initial_count = Issue.objects.filter(project=self.project).count()

        form_data = {
            'title': 'New Test Task',
            'description': 'Description of the new task',
            'status': 'To Do',
        }
        response = self.client.post(
            f'/projects/{self.project.id}/issues/create/',
            form_data
        )

        # Expect 302 redirect to project board
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/projects/{self.project.id}/')

        # Verify DB state
        self.assertEqual(Issue.objects.filter(project=self.project).count(), initial_count + 1)
        new_issue = Issue.objects.get(title='New Test Task', project=self.project)
        self.assertEqual(new_issue.status, 'To Do')
        self.assertEqual(new_issue.description, 'Description of the new task')

    def test_update_status_standard_post(self):
        """
        Contract 5: POST /issues/{issue_id}/update-status/
        Standard POST returns 302 redirect back to board and updates issue status.
        """
        self.assertEqual(self.issue_todo.status, 'To Do')

        response = self.client.post(
            f'/issues/{self.issue_todo.id}/update-status/',
            {'status': 'Done'}
        )

        # Expect 302 redirect to project board
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/projects/{self.project.id}/')

        # Verify DB updated
        self.issue_todo.refresh_from_db()
        self.assertEqual(self.issue_todo.status, 'Done')

    def test_add_comment_standard_post(self):
        """
        Contract 6: POST /issues/{issue_id}/comments/add/
        Standard POST returns 302 redirect to issue detail and creates comment.
        """
        initial_comment_count = Comment.objects.filter(issue=self.issue_todo).count()

        response = self.client.post(
            f'/issues/{self.issue_todo.id}/comments/add/',
            {'content': 'This is a standard SSR comment.'}
        )

        # Expect 302 redirect to issue detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/issues/{self.issue_todo.id}/')

        # Verify DB state
        self.assertEqual(Comment.objects.filter(issue=self.issue_todo).count(), initial_comment_count + 1)
        created_comment = Comment.objects.filter(issue=self.issue_todo).latest('created_at')
        self.assertEqual(created_comment.content, 'This is a standard SSR comment.')


class IssueTrackerEnhancedTests(TestCase):
    """
    Contract 7, 8, 9, 10: Tests for HTMX enhanced requests (simulated with HTTP_HX_REQUEST='true').
    """
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(
            name='Enhanced Project',
            description='Testing HTMX Progressive Enhancement'
        )
        self.issue = Issue.objects.create(
            title='Interactive Status Card',
            description='Test status swapping without full reload',
            status=Issue.STATUS_TODO,
            project=self.project
        )

    def test_update_status_htmx(self):
        """
        Contract 7 & 10: POST /issues/{issue_id}/update-status/ with HX-Request header
        returns status 200 OK, HTML fragment only (no <html> or <body>), and updates DB.
        """
        response = self.client.post(
            f'/issues/{self.issue.id}/update-status/',
            {'status': 'Done'},
            HTTP_HX_REQUEST='true'
        )

        # Status 200 OK
        self.assertEqual(response.status_code, 200)

        # Partial fragment only, NOT a full document
        self.assertNotContains(response, '<html')
        self.assertNotContains(response, '<body')
        self.assertNotContains(response, '</html>')
        self.assertNotContains(response, '</body>')

        # Verify card content and updated status
        content = response.content.decode('utf-8')
        self.assertIn('Interactive Status Card', content)
        self.assertIn('Done', content)

        # Verify DB updated
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.status, 'Done')

    def test_update_status_alias_htmx(self):
        """
        Tests the /issues/{issue_id}/status/ alias with HX-Request header.
        """
        response = self.client.post(
            f'/issues/{self.issue.id}/status/',
            {'status': 'In Progress'},
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<html')
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.status, 'In Progress')

    def test_add_comment_htmx(self):
        """
        Contract 8 & 10: POST /issues/{issue_id}/comments/add/ with HX-Request header
        returns status 200 OK, HTML fragment only, and creates comment in DB.
        """
        initial_count = Comment.objects.filter(issue=self.issue).count()

        response = self.client.post(
            f'/issues/{self.issue.id}/comments/add/',
            {'content': 'Dynamic comment posted via HTMX partial swap.'},
            HTTP_HX_REQUEST='true'
        )

        # Status 200 OK
        self.assertEqual(response.status_code, 200)

        # Verify response is HTML fragment
        self.assertNotContains(response, '<html')
        self.assertNotContains(response, '<body')

        content = response.content.decode('utf-8')
        self.assertIn('Dynamic comment posted via HTMX partial swap.', content)

        # Verify DB state
        self.assertEqual(Comment.objects.filter(issue=self.issue).count(), initial_count + 1)
        comment = Comment.objects.filter(issue=self.issue).latest('created_at')
        self.assertEqual(comment.content, 'Dynamic comment posted via HTMX partial swap.')

    def test_differentiate_standard_and_enhanced_requests(self):
        """
        Contract 9: Django view differentiates between standard and HTMX requests.
        Hitting same status update endpoint twice:
        Request 1 (No Header): 302 Redirect
        Request 2 (With Header): 200 OK with HTML fragment
        """
        endpoint = f'/issues/{self.issue.id}/update-status/'

        # Request 1 (No Header): Standard SSR request -> 302 Redirect
        res1 = self.client.post(endpoint, {'status': 'In Progress'})
        self.assertEqual(res1.status_code, 302)

        # Request 2 (With Header): HTMX enhanced request -> 200 OK fragment
        res2 = self.client.post(endpoint, {'status': 'Done'}, HTTP_HX_REQUEST='true')
        self.assertEqual(res2.status_code, 200)
        self.assertNotContains(res2, '<html')
        self.assertNotContains(res2, '<body>')


class HealthCheckAndGeneralViewTests(TestCase):
    """
    Test health check and listing views.
    """
    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_project_list_view(self):
        Project.objects.create(name='P1', description='Desc 1')
        response = self.client.get('/projects/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('P1', response.content.decode('utf-8'))
