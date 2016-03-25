from django import forms
from notifications.models import Notification


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['subject', 'text', 'sharedwith']
        labels = {
            'subject': 'Subject',
            'text': 'Text',
            'sharedwith': 'Shared with'
        }