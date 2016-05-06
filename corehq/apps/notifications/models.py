import datetime

from django.contrib.auth.models import User
from django.db import models


class Notification(models.Model):
    types = (
        ('info', 'Product Notification'),
        ('alert', 'Maintenance Notification'),
    )
    content = models.CharField(max_length=140)
    url = models.URLField()
    type = models.CharField(max_length=10, choices=types)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    users_read = models.ManyToManyField(User)
    is_active = models.BooleanField(default=False)
    activated = models.DateTimeField(db_index=True, null=True, blank=True)

    class Meta:
        ordering = ["-activated"]

    @classmethod
    def get_by_user(cls, user, limit=10):
        notes = cls.objects.filter(is_active=True)[:limit]
        read_notifications = cls.objects.filter(users_read=user)

        def _fmt_note(note_idx):
            index = note_idx[0]
            note = note_idx[1]

            note_dict = {
                'id': note.id,
                'url': note.url,
                'date': '{dt:%B} {dt.day}'.format(dt=note.activated),
                'content': note.content,
                'type': note.type,
                'isRead': (index > 4 or note in read_notifications),
            }
            return note_dict

        return map(_fmt_note, enumerate(notes))

    def mark_as_read(self, user):
        self.users_read.add(user)

    def activate(self):
        self.is_active = True
        self.activated = datetime.datetime.now()
        self.save()

    def deactivate(self):
        self.is_active = False
        self.activated = None
        self.save()
