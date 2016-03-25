from django.views.generic import ListView
from accounts.views import LoginRequiredMixin
from accounts.models import CustomUser
from notifications.models import Notification, UserNotification
from notifications.forms import NotificationForm
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


class NotificationsListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/list.html'
    form_class = NotificationForm

    def get_context_data(self, **kwargs):
        context = super(NotificationsListView, self).get_context_data(**kwargs)
        context['notifications'] = self.notifications
        context['form'] = self.form
        if self.request.user.is_admin:
            context['users'] = CustomUser.objects.all()
        return context

    def dispatch(self, request, *args, **kwargs):
        notifications = Notification.objects.all()

        self.notifications = list()

        for notification in notifications:
            if notification.is_shared(request.user) == False and request.user.is_admin == False:
                continue
            if notification.is_archived(request.user) == True:
                continue
            self.notifications.append(notification)

        self.form = NotificationForm()

        if request.user.is_admin:
            self.users = CustomUser.objects.all()
        else:
            self.users = None

        return super(NotificationsListView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        self.form = NotificationForm(request.POST)
        if self.form.is_valid():
            instances = self.form.save(commit=True)

        return redirect('notifications')


@login_required
def unread_notifications(request, methods=['GET']):
    unread_notifications = UserNotification.unread_notifications(request.user)
    return JsonResponse(unread_notifications)

@login_required
def read_notification(request, methods=['GET']):
    notification = get_object_or_404(Notification, pk=request.GET['pk'])
    read_user = request.user
    read_notification = UserNotification.objects.filter(user=read_user).filter(notification=notification)
    if not read_notification:
        user_notification = UserNotification(user=read_user, notification=notification)
        user_notification.save()
    return JsonResponse({'notification': notification.as_json(), 'result': 'success'})

@login_required
def archive_notification(request, methods=['GET']):
    notification = get_object_or_404(Notification, pk=request.GET['pk'])
    user_notification = UserNotification.objects.filter(user=request.user).filter(notification=notification).first()
    if not user_notification:
        user_notification = UserNotification(user=request.user, notification=notification, archived=True)

    user_notification.archived = True
    user_notification.save()
    return JsonResponse({'notification': notification.as_json(), 'result': 'success'})
