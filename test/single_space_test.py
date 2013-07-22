
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


class SingleSpaceTest(TestCase):
    def setUp(self):
         c = Client()

        # Create a user
        self.user = User.objects.create_user(username='user', password='pass', email='user@uw.edu')

        # Create a group that is the manager of the space
        test_group = Group.objects.create(name="test")

        # Initialize a space that has different manager than user
        before_json = '{"manager": ["test"], "capacity": 12, "location": {"floor": "2nd floor", "latitude": 47.652956, "room_number": 207, "longitude": -122.316343, "building_name": "Fishery Sciences (FSH)"}}'
        before_queued_space = {
            "q_id": 1,
            "change": "delete",
            "json": before_json,
            "errors": "{}",
            "space_etag": "x34C%6v9b&n9x234c48V 5rb-n-[a",
            "q_etag": None,
            "status": "updated",
            "approved_by": None,
        }
        before_form = QueueForm(before_queued_space)
        self.assertEqual(before_form.is_valid(), True, "Makes sure the form is valid")
        before_space = before_form.save(commit=False)
        before_space.space_last_modified = "2013-05-08T20:25:09.490751+00:00"
        before_space.modified_by = self.user
        before_space.space_id = 1
        before_space.save()
        q_etag = before_space.q_etag
        
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
       
    def test_delete(self):
        # Delete: user is not a manager, does not have the right to publish    --> fail
                # user is not a manager, has the right to pulish               --> fail
                # user is a manager, dose not have the right to publish        --> fail
                # user is a manager, has the right to publish                  --> success
        _test_delete_help(False, False, self.user, before_queued_space, before_queued_space.q_id, c)
        _test_delete_help(False, True, self.user, before_queued_space, before_queued_space.q_id, c)
        _test_delete_help(True, False, self.user, before_queued_space, before_queued_space.q_id, c) 
        _test_delete_help(True, True, self.user, before_queued_space, before_queued_space.q_id, c)
    
    def _test_delete_help(is_manager, can_publish, user, space_datum, space_id, c):
        c.login(username=user.username, password=user.password)
        is_deleted = edit_space._is_deleted(space_datum, is_manager, can_publish, user, space_id, c)
        c.logout()
        message = ""
        if is_manager and can_publish:
            message = "Is a manager, and can publish"
            self.assertEqual(is_deleted, True, message)
        elif is_manager and not can_publish:
            message = "Is a manager, and cannot publish"
            self.assertEqual(is_deleted, False, message)
        elif can_publish and not is_manager:
            message = "Is not a manager, and can publish"
            self.assertEqual(is_deleted, False, message)
        else:
            message = "Is not a manager, and cannot publish"
            self.assertEqual(is_deleted, False, message)
               
