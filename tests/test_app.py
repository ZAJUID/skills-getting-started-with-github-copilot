"""
Comprehensive tests for Mergington High School Activity Management System API

All tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and client state
- Act: Call the endpoint/function being tested
- Assert: Verify response status, content, and side effects
"""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index_html(self, client):
        """
        Arrange: client is ready
        Act: GET /
        Assert: response should redirect to /static/index.html
        """
        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities_returns_dict_with_all_activities(self, client):
        """
        Arrange: client is ready
        Act: GET /activities
        Assert: response should include all 9 activities with correct structure
        """
        # Arrange
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Basketball Club",
            "Art Club",
            "Drama Club",
            "Science Olympiad",
            "Debate Team"
        ]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        assert all(activity in data for activity in expected_activities)

    def test_activity_has_required_fields(self, client):
        """
        Arrange: client is ready
        Act: GET /activities and check first activity
        Assert: each activity should have description, schedule, max_participants, participants
        """
        # Act
        response = client.get("/activities")
        data = response.json()

        # Arrange & Assert
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_have_initial_participants(self, client):
        """
        Arrange: client is ready
        Act: GET /activities
        Assert: each activity should have at least 2 initial participants
        """
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_data in data.items():
            assert len(activity_data["participants"]) >= 2


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_valid_student_returns_200_and_adds_email(self, client):
        """
        Arrange: get initial participant count for Chess Club
        Act: POST /activities/Chess Club/signup with new email
        Assert: response should be 200 and email should be added to participants
        """
        # Arrange
        activity_name = "Chess Club"
        test_email = "test.student@mergington.edu"

        # Get initial participants
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {test_email} for {activity_name}"

        # Verify email was added
        activities_after = client.get("/activities").json()
        assert test_email in activities_after[activity_name]["participants"]
        assert len(activities_after[activity_name]["participants"]) == initial_count + 1

    def test_signup_duplicate_email_returns_400(self, client):
        """
        Arrange: Chess Club already has michael@mergington.edu
        Act: POST /activities/Chess Club/signup with duplicate email
        Assert: response should be 400 with appropriate error message
        """
        # Arrange
        activity_name = "Chess Club"
        duplicate_email = "michael@mergington.edu"  # Already in Chess Club

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": duplicate_email}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_invalid_activity_returns_404(self, client):
        """
        Arrange: "Nonexistent Activity" does not exist
        Act: POST /activities/Nonexistent Activity/signup with valid email
        Assert: response should be 404 with activity not found error
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        test_email = "test.student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_multiple_different_students_all_succeed(self, client):
        """
        Arrange: Programming Class with fresh signup attempts
        Act: POST /activities/Programming Class/signup for 3 different students
        Assert: all 3 should succeed and appear in participants list
        """
        # Arrange
        activity_name = "Programming Class"
        test_emails = [
            "alice@mergington.edu",
            "bob@mergington.edu",
            "charlie@mergington.edu"
        ]

        # Act & Assert
        for email in test_emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Verify all were added
        activities = client.get("/activities").json()
        for email in test_emails:
            assert email in activities[activity_name]["participants"]


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_enrolled_student_returns_200_and_removes_email(self, client):
        """
        Arrange: Get initial participants for an activity
        Act: POST /activities/{activity_name}/unregister with enrolled email
        Assert: response should be 200 and email should be removed from participants
        """
        # Arrange
        activity_name = "Chess Club"
        enrolled_email = "michael@mergington.edu"  # Already in Chess Club

        # Get initial count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": enrolled_email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {enrolled_email} from {activity_name}"

        # Verify email was removed
        activities_after = client.get("/activities").json()
        assert enrolled_email not in activities_after[activity_name]["participants"]
        assert len(activities_after[activity_name]["participants"]) == initial_count - 1

    def test_unregister_not_enrolled_student_returns_400(self, client):
        """
        Arrange: nonexistent.student@mergington.edu is not in any activity
        Act: POST /activities/Chess Club/unregister with non-enrolled email
        Assert: response should be 400 with appropriate error message
        """
        # Arrange
        activity_name = "Chess Club"
        not_enrolled_email = "nonexistent.student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": not_enrolled_email}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_invalid_activity_returns_404(self, client):
        """
        Arrange: "Fake Activity" does not exist
        Act: POST /activities/Fake Activity/unregister with any email
        Assert: response should be 404 with activity not found error
        """
        # Arrange
        activity_name = "Fake Activity"
        test_email = "test.student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_then_signup_again_succeeds(self, client):
        """
        Arrange: Get an enrolled student from Art Club
        Act: Unregister, then immediately signup again
        Assert: both operations should succeed and final state should show student enrolled
        """
        # Arrange
        activity_name = "Art Club"
        test_email = "isabella@mergington.edu"  # Already in Art Club

        # Act - Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )
        assert unregister_response.status_code == 200

        # Assert - Email should be removed
        activities_after_unregister = client.get("/activities").json()
        assert test_email not in activities_after_unregister[activity_name]["participants"]

        # Act - Signup again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )
        assert signup_response.status_code == 200

        # Assert - Email should be back in participants
        activities_after_signup = client.get("/activities").json()
        assert test_email in activities_after_signup[activity_name]["participants"]

    def test_unregister_multiple_students_independently(self, client):
        """
        Arrange: Add 3 test students to an activity, then unregister them one by one
        Act: Signup 3 students, then unregister each
        Assert: each unregister should succeed and only that student should be removed
        """
        # Arrange
        activity_name = "Debate Team"
        test_emails = [
            "test1@mergington.edu",
            "test2@mergington.edu",
            "test3@mergington.edu"
        ]

        # Sign up all three
        for email in test_emails:
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )

        # Act & Assert - Unregister each one
        for i, email in enumerate(test_emails):
            response = client.post(
                f"/activities/{activity_name}/unregister",
                params={"email": email}
            )
            assert response.status_code == 200

            # Verify only that email was removed, others remain
            activities = client.get("/activities").json()
            remaining_test_emails = test_emails[i+1:]
            for other_email in remaining_test_emails:
                assert other_email in activities[activity_name]["participants"]
            assert email not in activities[activity_name]["participants"]


class TestIntegrationScenarios:
    """Integration tests combining multiple operations"""

    def test_full_signup_workflow_for_single_student(self, client):
        """
        Arrange: New student wanting to join multiple activities
        Act: Signup for 3 different activities
        Assert: student should appear in all 3 activity participant lists
        """
        # Arrange
        test_email = "new.student@mergington.edu"
        activities_to_join = [
            "Chess Club",
            "Programming Class",
            "Art Club"
        ]

        # Act - Signup for all three
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": test_email}
            )
            assert response.status_code == 200

        # Assert - Student should be in all activities
        all_activities = client.get("/activities").json()
        for activity in activities_to_join:
            assert test_email in all_activities[activity]["participants"]

    def test_multiple_students_signup_and_unregister_same_activity(self, client):
        """
        Arrange: Multiple students with various signup/unregister patterns
        Act: Student A signs up, B signs up, A unregisters, C signs up, B unregisters
        Assert: final state should only have C
        """
        # Arrange
        activity_name = "Science Olympiad"
        student_a = "student.a@mergington.edu"
        student_b = "student.b@mergington.edu"
        student_c = "student.c@mergington.edu"

        # Get initial participants
        initial = client.get("/activities").json()[activity_name]["participants"].copy()

        # Act & Assert sequence
        # A signs up
        assert client.post(f"/activities/{activity_name}/signup", params={"email": student_a}).status_code == 200
        # B signs up
        assert client.post(f"/activities/{activity_name}/signup", params={"email": student_b}).status_code == 200
        # A unregisters
        assert client.post(f"/activities/{activity_name}/unregister", params={"email": student_a}).status_code == 200
        # C signs up
        assert client.post(f"/activities/{activity_name}/signup", params={"email": student_c}).status_code == 200
        # B unregisters
        assert client.post(f"/activities/{activity_name}/unregister", params={"email": student_b}).status_code == 200

        # Assert final state
        final = client.get("/activities").json()[activity_name]["participants"]
        assert student_a not in final
        assert student_b not in final
        assert student_c in final
        # Initial students should still be there
        for email in initial:
            assert email in final
