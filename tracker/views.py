from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
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


@csrf_exempt
@require_POST
def create_issue(request, project_id):
    """
    Creates a new issue for a project.
    Standard form submission redirects (302) to the project board.
    """
    project = get_object_or_404(Project, pk=project_id)
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    status = request.POST.get('status', Issue.STATUS_TODO).strip()

    valid_statuses = dict(Issue.STATUS_CHOICES)
    status_map = {
        'to do': Issue.STATUS_TODO,
        'todo': Issue.STATUS_TODO,
        'in progress': Issue.STATUS_IN_PROGRESS,
        'inprogress': Issue.STATUS_IN_PROGRESS,
        'done': Issue.STATUS_DONE,
    }
    resolved_status = valid_statuses.get(status) or status_map.get(status.lower(), Issue.STATUS_TODO)

    if title:
        issue = Issue.objects.create(
            project=project,
            title=title,
            description=description,
            status=resolved_status
        )
        if is_htmx(request):
            return render(request, 'tracker/_issue_card.html', {
                'issue': issue,
                'project': project,
            })
        return redirect('tracker:project_board', project_id=project.id)

    # In case of validation error in standard mode, re-render board
    issues = project.issues.all()
    todo_issues = [i for i in issues if i.status == Issue.STATUS_TODO]
    in_progress_issues = [i for i in issues if i.status == Issue.STATUS_IN_PROGRESS]
    done_issues = [i for i in issues if i.status == Issue.STATUS_DONE]

    return render(request, 'tracker/project_board.html', {
        'project': project,
        'todo_issues': todo_issues,
        'in_progress_issues': in_progress_issues,
        'done_issues': done_issues,
        'form': IssueForm(request.POST),
    }, status=400)


@csrf_exempt
@require_POST
def update_issue_status(request, issue_id):
    """
    Updates the status of an issue.
    - Standard Request: Returns 302 Redirect to project board.
    - Enhanced Request (HX-Request): Returns 200 OK with only the partial HTML for the updated issue card.
    """
    issue = get_object_or_404(Issue.objects.select_related('project'), pk=issue_id)
    new_status = request.POST.get('status', '').strip()

    valid_statuses = dict(Issue.STATUS_CHOICES)
    status_map = {
        'to do': Issue.STATUS_TODO,
        'todo': Issue.STATUS_TODO,
        'in progress': Issue.STATUS_IN_PROGRESS,
        'inprogress': Issue.STATUS_IN_PROGRESS,
        'done': Issue.STATUS_DONE,
    }

    resolved_status = valid_statuses.get(new_status) or status_map.get(new_status.lower())
    if resolved_status:
        issue.status = resolved_status
        issue.save()

    if is_htmx(request):
        # Progressively enhanced response: partial fragment only, no <html> or <body>
        return render(request, 'tracker/_issue_card.html', {
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


@csrf_exempt
@require_POST
def add_comment(request, issue_id):
    """
    Adds a comment to an issue.
    - Standard Request: Returns 302 Redirect to issue detail page.
    - Enhanced Request (HX-Request): Returns 200 OK with only the partial HTML for the new comment.
    """
    issue = get_object_or_404(Issue, pk=issue_id)
    content = request.POST.get('content', '').strip()

    if content:
        comment = Comment.objects.create(issue=issue, content=content)

        if is_htmx(request):
            # Progressively enhanced response: partial fragment only, no <html> or <body>
            return render(request, 'tracker/_comment.html', {
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
        'form': CommentForm(request.POST),
    }, status=400)


@require_GET
def health_check(request):
    """
    Healthcheck endpoint for Docker container monitoring.
    """
    return JsonResponse({'status': 'ok'})
