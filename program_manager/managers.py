from django.db.models import Q

from polymorphic.manager import PolymorphicManager, PolymorphicQuerySet


class ProgramQuerySet(PolymorphicQuerySet):
    def for_user(self, user):
        """ Convenient method for future. Programs will be part of an
            organization. Users can be part of multiple organizations.
        """
        return self.filter(user=user)

    def with_reports(self):
        return self.filter(
            Q(qualityscorereport__isnull=False))


class BaseProgramManager(PolymorphicManager):
    queryset_class = ProgramQuerySet


ProgramManager = BaseProgramManager.from_queryset(ProgramQuerySet)
