from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404

from .forms import CommentForm
from .models import Comment
from documents.models import Report


class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = CommentForm(request.POST)

        if form.is_valid():
            report = get_object_or_404(Report, id=form.cleaned_data['report_id'])
            
            # Check if the current user is the creator of the report
            if request.user != report.created_by:
                return JsonResponse({'status': 'error', 'message': 'You are not allowed to comment on this report.'}, status=403)

            comment = form.save(commit=False)
            comment.created_by = request.user
            comment.report = report
            comment.save()
            return JsonResponse({
                'status': 'success',
                'comment': {
                    'id': comment.id,
                    'text': comment.text,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'created_by': comment.created_by.username,  # Return username instead of user object
                    'approved': comment.approved,
                }
            })

        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


class CommentDeleteView(LoginRequiredMixin, View):
    def post(self, request, comment_id, *args, **kwargs):
        comment = get_object_or_404(Comment, id=comment_id)
        if request.user != comment.created_by:
            return JsonResponse(
                {
                    'status': 'error',
                    'message': 'You are not allowed to delete this comment.'
                },
                status=403
            )
        comment.delete()
        return JsonResponse({'status': 'success'})
