"""
Unit tests for UserDAO operations.
"""

import pytest
from app.models.user import User


class TestUserDAO:
    """Test suite for user persistence and retrieval."""

    def test_get_by_username(self, user_dao):
        admin = user_dao.get_by_username("admin")
        assert admin is not None
        assert admin.username == "admin"
        assert admin.is_admin is True

        staff = user_dao.get_by_username("staff")
        assert staff is not None
        assert staff.username == "staff"
        assert staff.is_staff is True

        non_existent = user_dao.get_by_username("doesnotexist")
        assert non_existent is None

    def test_get_by_id(self, user_dao):
        user = user_dao.get_by_id(1)
        assert user is not None
        assert user.user_id == 1

        user_none = user_dao.get_by_id(99999)
        assert user_none is None

    def test_create_and_list_users(self, user_dao):
        new_id = user_dao.create_user("prof_smith", "$2b$12$fakepasswordhash", "STAFF")
        assert new_id > 0

        created = user_dao.get_by_id(new_id)
        assert created is not None
        assert created.username == "prof_smith"
        assert created.role == "STAFF"

        all_users = user_dao.list_users()
        assert len(all_users) >= 3
        usernames = [u.username for u in all_users]
        assert "prof_smith" in usernames
