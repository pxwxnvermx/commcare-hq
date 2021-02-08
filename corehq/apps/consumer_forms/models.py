import uuid
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from corehq.form_processor.interfaces.dbaccessors import CaseAccessors


class ConsumerForm(models.Model):
    domain = models.CharField(max_length=126, null=False, db_index=True)
    slug = models.CharField(max_length=126, null=False, db_index=True)

    class Meta:
        unique_together = ('domain', 'slug')


class AuthenticatedLink(models.Model):
    link_id = models.UUIDField(unique=True, db_index=True, default=uuid.uuid4)
    domain = models.CharField(max_length=126, null=False, db_index=True)
    case_ids = JSONField(default=list, help_text=_('List of cases this link is allowed to access.'))
    created_on = models.DateTimeField(auto_now=True)
    expires_on = models.DateTimeField(null=True, blank=True)
    allows_submission = models.BooleanField(default=False, help_text=_('If the link allows data submission'))
    submitting_user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        help_text=_('For links that allow data submission, the user to be used to submit data.'),
    )
    is_visited = models.BooleanField(default=False)
    visited_on = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)
    used_on = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        return not self.is_used and self.expires_on is None or self.expires_on > datetime.utcnow()

    def get_data(self):
        return [
            c.to_json() for c in CaseAccessors(self.domain).get_cases(self.case_ids)
        ]
