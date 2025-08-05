from django.test import TestCase
import pytest
from pytest import APIClient


def test_user_changes_password(user1):
    client = APIClient()
    client.force_authenticate(user = user1)
    