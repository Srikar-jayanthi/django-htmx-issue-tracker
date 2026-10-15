from django import forms
from .models import Issue, Comment


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['title', 'description', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Issue title...',
                'required': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Detailed description of the issue...',
                'rows': 3,
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Add a comment...',
                'rows': 3,
                'required': True,
            }),
        }
