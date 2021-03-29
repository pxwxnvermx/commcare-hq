from collections import namedtuple
from datetime import datetime

from django.contrib.postgres.fields import ArrayField
from django.db import models

import architect
from oauth2_provider.models import AbstractApplication

from corehq.util.markup import mark_up_urls
from corehq.util.quickcache import quickcache

PageInfoContext = namedtuple('PageInfoContext', 'title url')


class GaTracker(namedtuple('GaTracking', 'category action label')):
    """
    Info for tracking clicks using Google Analytics
    see https://developers.google.com/analytics/devguides/collection/analyticsjs/events
    """
    def __new__(cls, category, action, label=None):
        return super(GaTracker, cls).__new__(cls, category, action, label)


class MaintenanceAlert(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=False)

    text = models.TextField()
    domains = ArrayField(models.CharField(max_length=126), null=True)

    class Meta(object):
        app_label = 'hqwebapp'

    @property
    def html(self):
        return mark_up_urls(self.text)

    def __repr__(self):
        return "MaintenanceAlert(text='{}', active='{}', domains='{}')".format(
            self.text, self.active, ", ".join(self.domains) if self.domains else "All Domains")

    def save(self, *args, **kwargs):
        MaintenanceAlert.get_latest_alert.clear(MaintenanceAlert)
        super(MaintenanceAlert, self).save(*args, **kwargs)

    @classmethod
    @quickcache([], timeout=60 * 60)
    def get_latest_alert(cls):
        active_alerts = cls.objects.filter(active=True).order_by('-modified')
        if active_alerts:
            return active_alerts[0]
        else:
            return ''


class UserAgent(models.Model):
    MAX_LENGTH = 255

    value = models.CharField(max_length=MAX_LENGTH, db_index=True)


class UserAccessLogManager(models.Manager):
    def create(self, **obj_data):
        user_agent = obj_data.pop('user_agent', '')
        if user_agent:
            user_agent = user_agent[:UserAgent.MAX_LENGTH]
            agent_ref, _ = UserAgent.objects.get_or_create(value=user_agent)
            obj_data['user_agent'] = agent_ref

        return super().create(**obj_data)


@architect.install('partition', type='range', subtype='date', constraint='month', column='timestamp')
class UserAccessLog(models.Model):
    TYPE_LOGIN = 'login'
    TYPE_LOGOUT = 'logout'
    TYPE_FAILURE = 'failure'

    ACTIONS = (
        (TYPE_LOGIN, 'Login'),
        (TYPE_LOGOUT, 'Logout'),
        (TYPE_FAILURE, 'Login Failure')
    )

    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=255, db_index=True)
    action = models.CharField(max_length=20, choices=ACTIONS)
    ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.ForeignKey(UserAgent, null=True, on_delete=models.PROTECT)
    path = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(default=datetime.utcnow)

    objects = UserAccessLogManager()

    def __str__(self):
        return f'{self.timestamp}: {self.user_id} - {self.action}'


class HQOAuthApplication(AbstractApplication):
    pkce_required = models.BooleanField(default=True)
    smart_on_fhir_compatible = models.BooleanField(
        default=False
    )  # Whether this application will request tokens with SMART scopes. See hqwebapp.oauth_scopes.HQScopes
