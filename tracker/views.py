from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from .models import Project, Issue, Comment
from .forms import IssueForm, CommentForm


def is_htmx(request):
    """
    Check if the request was sent by HTMX (or client-side enhancement)
    by inspecting the HX-Request header.
    """
    header_val = request.headers.get('HX-Request') or request.META.get('HTTP_HX_REQUEST')
    if header_val is not None:
        return str(header_val).strip().lower() in ('true', '1')
    return False


@require_GET
def project_list(request):
    """
    Renders a list of all projects with summary metrics.
    """
    projects = Project.objects.prefetch_related('issues').all()
    return render(request, 'tracker/project_list.html', {
        'projects': projects,
    })


@require_GET
def project_board(request, project_id):
    """
    Renders the Kanban issue board for a given project.
    Contains distinct sections for 'To Do', 'In Progress', and 'Done'.
    Fully functional with or without JavaScript.
    """
    project = get_object_or_404(Project, pk=project_id)
    issues = project.issues.all()

    todo_issues = [i for i in issues if i.status == Issue.STATUS_TODO]
    in_progress_issues = [i for i in issues if i.status == Issue.STATUS_IN_PROGRESS]
    done_issues = [i for i in issues if i.status == Issue.STATUS_DONE]

    form = IssueForm()

    return render(request, 'tracker/project_board.html', {
        'project': project,
        'todo_issues': todo_issues,
        'in_progress_issues': in_progress_issues,
        'done_issues': done_issues,
        'form': form,
    })


@require_POST
def create_issue(request, project_id):
    """
    Creates a new issue for a project.
    Standard form submission redirects (302) to the project board.
    """
    project = get_object_or_404(Project, pk=project_id)
    form = IssueForm(request.POST)
    if form.is_valid():
        issue = form.save(commit=False)
        issue.project = project
        issue.save()
        return redirect('tracker:project_board', project_id=project.id)

    # In case of validation error in standard mode, re-render board with errors
    issues = project.issues.all()
    todo_issues = [i for i in issues if i.status == Issue.STATUS_TODO]
    in_progress_issues = [i for i in issues if i.status == Issue.STATUS_IN_PROGRESS]
    done_issues = [i for i in issues if i.status == Issue.STATUS_DONE]

    return render(request, 'tracker/project_board.html', {
        'project': project,
        'todo_issues': todo_issues,
        'in_progress_issues': in_progress_issues,
        'done_issues': done_issues,
        'form': form,
    }, status=400)


@require_POST
def update_issue_status(request, issue_id):
    """
    Updates the status of an issue.
    - Standard Request: Returns 302 Redirect to project board.
    - Enhanced Request (HX-Request): Returns 200 OK with only the partial HTML for the updated issue card.
    """
    issue = get_object_or_404(Issue.objects.select_related('project'), pk=issue_id)
    new_status = request.POST.get('status')

    valid_statuses = [choice[0] for choice in Issue.STATUS_CHOICES]
    if new_status in valid_statuses:
        issue.status = new_status
        issue.save()

    if is_htmx(request):
        # Progressively enhanced response: partial fragment only, no <html> or <body>
        return render(request, 'tracker/partials/_issue_card.html', {
            'issue': issue,
            'project': issue.project,
        })

    # Standard SSR response: full page reload via 302 redirect
    return redirect('tracker:project_board', project_id=issue.project.id)


@require_GET
def issue_detail(request, issue_id):
    """
    Renders detail page for an issue including all comments and comment form.
    """
    issue = get_object_or_404(
        Issue.objects.select_related('project').prefetch_related('comments'),
        pk=issue_id
    )
    form = CommentForm()
    comments = issue.comments.all()

    return render(request, 'tracker/issue_detail.html', {
        'issue': issue,
        'project': issue.project,
        'comments': comments,
        'form': form,
    })


@require_POST
def add_comment(request, issue_id):
    """
    Adds a comment to an issue.
    - Standard Request: Returns 302 Redirect to issue detail page.
    - Enhanced Request (HX-Request): Returns 200 OK with only the partial HTML for the new comment.
    """
    issue = get_object_or_404(Issue, pk=issue_id)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.issue = issue
        comment.save()

        if is_htmx(request):
            # Progressively enhanced response: partial fragment only, no <html> or <body>
            return render(request, 'tracker/partials/_comment.html', {
                'comment': comment,
            })

        # Standard SSR response: redirect to issue detail
        return redirect('tracker:issue_detail', issue_id=issue.id)

    if is_htmx(request):
        return HttpResponseBadRequest("Invalid comment data")

    comments = issue.comments.all()
    return render(request, 'tracker/issue_detail.html', {
        'issue': issue,
        'project': issue.project,
        'comments': comments,
        'form': form,
    }, status=400)


@require_GET
def health_check(request):
    """
    Healthcheck endpoint for Docker container monitoring.
    """
    return JsonResponse({'status': 'ok'})
