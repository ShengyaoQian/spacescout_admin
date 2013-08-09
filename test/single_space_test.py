
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
    
    def setUp(self):
        # Create a managers group
        self.managers_group = Group.objects.create(name="managers")
        # Create a user
        self.user = User.objects.create_user(username='user', password='pass', email='user@example.com')

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
        self.before_space = before_form.save(commit=False)
        self.before_space.space_last_modified = "2013-05-08T20:25:09.490751+00:00"
        self.before_space.modified_by = self.user
        self.before_space.space_id = 1
        self.before_space.save()
        q_etag = self.before_space.q_etag
        consumer = oauth2.Consumer(key=settings.SS_WEB_OAUTH_KEY, secret=settings.SS_WEB_OAUTH_SECRET)
        self.c = oauth2.Client(consumer)    
    
    def _delete_helper(self, can_publish, is_manager):
        # construct the error message
        manager_str = "a manager"
        permission_str = "permission to delete"
        if not is_manager:
            manager_str = "not " + manager_str
        if not can_publish:
            permission_str = "no " + permission_str
        message = "Delete failed at is " + manager_str + " and has " + permission_str 
        # try deleting the space
        is_deleted = edit_space._is_deleted(self.before_queued_space, is_manager, can_publish, self.user, self.before_queued_space, self.c)
        self.assertEqual(is_deleted, is_manager and can_publish, message)

    def test_delete_main(self):
        # test: has no permission to delete and is not a manager of the space --> fail
        can_publish = False
        is_manager = edit_space._is_manager(self.user, self.managers_group)
        self._delete_helper(can_publish, is_manager)

        # test: has permission to delete, but is not a manager of the space --> fail
        can_publush = True
        self._delete_helper(can_publish, is_manager)

        # test: has permission to delete and is a manager of the space ---> success
        # add the user to the managers group, so the user become a manager of the space
        self.user.groups.add(self.managers_group)
        # check if the user is a manager of the space and has the right to publish
        is_manager = edit_space._is_manager(self.user, self.managers_group)
        self._delete_helper(can_publish, is_manager)

        # test: has no permisson to delete, but is a manager of the space --> fail
        can_publish = False
        self._delete_helper(can_publish, is_manager)

    def _approve_helper(self, is_manager, can_approve, before_status):
        # construct the error message
        manager_str = "a manager"
        permission_str = "permission to approve"
        should_be_approved = True
        if not is_manager:
            manager_str = "not " + manager_str
            should_be_approved = False
        if not can_approve:
            permission_str = "no " + permission_str
            should_be_approved = False
        message = "Approve failed at is " + manager_str + " and has " + permission_str 
       
        after_space = self.before_space
        # try approving the space
        if is_manager:
            after_space = edit_space._is_approved(self.before_queued_space, can_approve, self.before_space, self.user)
        self.assertEqual(after_space.status ==  before_status, not should_be_approved, message)
        # set space status back to its initial status
        self.before_space.status = before_status
 
    def test_approve_main(self):
        self.before_queued_space["changed"] = "approved"
        before_status = self.before_space.status

        # test: has no permission to approve and is not a manager of the space --> fail
        can_approve = False
        is_manager = edit_space._is_manager(self.user, self.managers_group)
        self._approve_helper(is_manager, can_approve, before_status)

        #test: has permission to approve, but is a manager of the space --> fail
        can_approve = True
        self._approve_helper(is_manager, can_approve, before_status)

        # test: has permission to approve and is a manager of the space --> success
        # add the user to the managers group, so the user become a manager of the space
        self.user.groups.add(self.managers_group)
        # check if the user is a manager of the space and has the right to publish
        is_manager = edit_space._is_manager(self.user, self.managers_group)
        self._approve_helper(is_manager, can_approve, before_status)

        # test: has no permission to approve, but is a manager of the space --> fail
        can_approve = False
        self._approve_helper(is_manager, can_approve, before_status)

    def tearDown(self):
        # Delete the managers group and the user
        managers = Group.objects.get(name="managers")
        managers.delete()
        u = User.objects.get(username='user')
        u.delete()       
