
from django.test.client import Client
from django.test import TestCase
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import User, Group, Permission
from spacescout_admin.models import QueuedSpace
from spacescout_admin.views import edit_space
from spacescout_admin.forms import QueueForm
from spacescout_admin.utils import *
import json
import oauth2

class SingleSpaceTest(TestCase):
    before_queued_space = None
    consumer = oauth2.Consumer(key=settings.SS_WEB_OAUTH_KEY, secret=settings.SS_WEB_OAUTH_SECRET)
    c = oauth2.Client(consumer)    
    manager_group = None
    user = None

    def setUp(self):
        # Create a managers group
        self.managers_group = Group.objects.create(name="managers")
        # Create a user
        self.user = User.objects.create_user(username='user', password='pass', email='user@uw.edu')
  
        # Initialize a spot that has different manager than user
        before_json = '{"manager": ["managers"], "capacity": 12, "location": {"floor": "2nd floor", "latitude": 47.652956, "room_number": 207, "longitude": -122.316343, "building_name": "Fishery Sciences (FSH)"}}'
        self.before_queued_space = {
            "changed": "delete",
            "id": 1,
            "json": before_json,
            "errors": "{}",
            "space_etag": "x34C%6v9b&n9x234c48V 5rb-n-[a",
            "q_etag": None,
            "status": "updated",
            "approved_by": None,
        }
        before_form = QueueForm(self.before_queued_space)
        self.assertEqual(before_form.is_valid(), True, "Makes sure the form is valid")
        before_space = before_form.save(commit=False)
        before_space.space_last_modified = "2013-05-08T20:25:09.490751+00:00"
        before_space.modified_by = self.user
        before_space.space_id = 1
        before_space.save()
        q_etag = before_space.q_etag
   
    def test_delete_manager(self):
        # add the user to the managers group, so the user become a manager of the space
        self.user.groups.add(self.managers_group)
        # check if the user is a manager of the space and has the right to publish
        is_manager = edit_space._is_manager(self.user, self.managers_group)
        can_publish = False
        # let the user try deleting a space   
        is_deleted = edit_space._is_deleted(self.before_queued_space, is_manager, can_publish, self.user, self.before_queued_space, self.c)
        self.assertEqual(is_deleted, False, "Delete failed at is a manager, and cannot publish")

    def test_delete_manager_can_publish(self):
        # add the user to the managers group, so the user become a manager of the space
        self.user.groups.add(self.managers_group)
        # check if the user is a manager of the space and has the right to publish
        is_manager = edit_space._is_manager(self.user, self.managers_group)
        can_publish = True
        # let the user try deleting a space
        is_deleted = edit_space._is_deleted(self.before_queued_space, is_manager, can_publish, self.user, self.before_queued_space, self.c)
        self.assertEqual(is_deleted, True, "Delete failed at is a manager, and can publish")

    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

    def test_delete_can_publish(self):
        # check if the user is a manager of the space and has the right to publish
        is_manager = edit_space._is_manager(self.user, self.managers_group)
        can_publish = True
        is_deleted = edit_space._is_deleted(self.before_queued_space, is_manager, can_publish, self.user, self.before_queued_space, self.c)
        self.assertEqual(is_deleted, False, "Delete failed at is not a manager, and can publish")


    def test_delete_general_user(self):
        # check if the user is a manager of the space and has the right to publish
        is_manager = edit_space._is_manager(self.user, self.managers_group)
        can_publish = False
        # let the user try deleting a space
        is_deleted = edit_space._is_deleted(self.before_queued_space, is_manager, can_publish, self.user, self.before_queued_space, self.c)
        self.assertEqual(is_deleted, False, "Delete failed at is not a manager, and cannot publish")
   
    def tearDown(self):
        # Delete the managers group and the user
        managers = Group.objects.get(name="managers")
        managers.delete()
        u = User.objects.get(username='user')
        u.delete()
























       
