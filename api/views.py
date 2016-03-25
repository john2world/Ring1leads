from rest_framework import generics
from api.serializers import ProgramSerializer
from program_manager.models import Program


class ProgramListView(generics.ListAPIView):
    serializer_class = ProgramSerializer

    def get_queryset(self):
        qs = Program.objects.all()

        if self.request.user and not self.request.user.is_anonymous():
            qs = qs.filter(user=self.request.user)

        name_filter = self.request.query_params.get('nameFilter', None)
        if name_filter:
            qs = qs.filter(name__icontains=name_filter)

        status_filter = self.request.query_params.get('statusFilter', None)
        if status_filter == 'active':
            qs = qs.exclude(status__in=('ARCH',))
        elif status_filter:
            qs = qs.filter(status=status_filter)

        return qs


class ProgramRetrieveView(generics.RetrieveAPIView):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
