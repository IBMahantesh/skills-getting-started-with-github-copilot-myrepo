"""Unit tests for activity signup functionality using the AAA (Arrange-Act-Assert) pattern."""

import pytest
from fastapi import HTTPException
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import signup_for_activity, unregister_from_activity, activities, get_activities


# ============================================================================
# Tests for get_activities() - Activity Retrieval
# ============================================================================

class TestGetActivities:
    """Test suite for retrieving all activities."""

    def test_get_activities_returns_all_activities(self):
        """Test that get_activities returns all activities in the database."""
        # Arrange - no setup needed, activities are pre-populated in conftest
        
        # Act
        result = get_activities()
        
        # Assert
        assert len(result) == 9
        assert "Chess Club" in result
        assert "Programming Class" in result
        assert "Gym Class" in result

    def test_get_activities_returns_correct_structure(self):
        """Test that each activity has the required fields."""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        result = get_activities()
        
        # Assert
        for activity_name, activity_data in result.items():
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys())
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_get_activities_returns_participants_as_list(self):
        """Test that participants are returned as a list."""
        # Arrange
        
        # Act
        result = get_activities()
        
        # Assert
        for activity_data in result.values():
            assert isinstance(activity_data["participants"], list)
            assert all(isinstance(email, str) for email in activity_data["participants"])


# ============================================================================
# Tests for signup_for_activity() - Signup Business Logic
# ============================================================================

class TestSignupForActivity:
    """Test suite for signing up a student for an activity."""

    def test_signup_successful_happy_path(self):
        """Test successful signup when all conditions are met."""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        result = signup_for_activity(activity_name, email)
        
        # Assert
        assert result["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count + 1

    def test_signup_with_multiple_available_spots(self):
        """Test signup works when multiple spots are available."""
        # Arrange
        activity_name = "Programming Class"
        email = "student@mergington.edu"
        available_spots = (
            activities[activity_name]["max_participants"] - 
            len(activities[activity_name]["participants"])
        )
        assert available_spots > 1  # Verify there are multiple spots
        
        # Act
        result = signup_for_activity(activity_name, email)
        
        # Assert
        assert "Signed up" in result["message"]
        assert email in activities[activity_name]["participants"]

    def test_signup_fails_activity_not_found(self):
        """Test that signup fails with 404 when activity doesn't exist."""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            signup_for_activity(activity_name, email)
        
        assert exc_info.value.status_code == 404
        assert "Activity not found" in exc_info.value.detail

    def test_signup_fails_already_signed_up(self):
        """Test that signup fails with 400 when student is already signed up."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            signup_for_activity(activity_name, email)
        
        assert exc_info.value.status_code == 400
        assert "already signed up" in exc_info.value.detail

    def test_signup_fails_activity_full(self):
        """Test that signup fails with 400 when activity is at capacity."""
        # Arrange
        activity_name = "Tennis Club"
        # Tennis Club has max 10 participants, currently has 1
        # Fill it up to capacity
        for i in range(9):
            email = f"filler{i}@mergington.edu"
            activities[activity_name]["participants"].append(email)
        
        # Verify activity is now full
        assert len(activities[activity_name]["participants"]) == 10
        
        # Act & Assert
        new_email = "overflow@mergington.edu"
        with pytest.raises(HTTPException) as exc_info:
            signup_for_activity(activity_name, new_email)
        
        assert exc_info.value.status_code == 400
        assert "full" in exc_info.value.detail

    def test_signup_preserves_existing_participants(self):
        """Test that signup doesn't remove existing participants."""
        # Arrange
        activity_name = "Drama Club"
        existing_participants = activities[activity_name]["participants"].copy()
        new_email = "newdramastu@mergington.edu"
        
        # Act
        signup_for_activity(activity_name, new_email)
        
        # Assert
        for participant in existing_participants:
            assert participant in activities[activity_name]["participants"]

    def test_signup_with_last_available_spot(self):
        """Test signup succeeds when signing up for the last available spot."""
        # Arrange
        activity_name = "Basketball Team"
        # Basketball Team has max 15, currently has 1, so 14 spots available
        # Fill it to have only 1 spot left
        for i in range(13):
            activities[activity_name]["participants"].append(f"filler{i}@mergington.edu")
        
        assert (len(activities[activity_name]["participants"]) == 
                activities[activity_name]["max_participants"] - 1)
        
        # Act
        last_email = "lastspotstudent@mergington.edu"
        result = signup_for_activity(activity_name, last_email)
        
        # Assert
        assert last_email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == activities[activity_name]["max_participants"]


# ============================================================================
# Tests for unregister_from_activity() - Unregister Business Logic
# ============================================================================

class TestUnregisterFromActivity:
    """Test suite for unregistering a student from an activity."""

    def test_unregister_successful_happy_path(self):
        """Test successful unregister when student is signed up."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        result = unregister_from_activity(activity_name, email)
        
        # Assert
        assert result["message"] == f"Unregistered {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1

    def test_unregister_removes_only_specified_student(self):
        """Test that unregister only removes the specified student."""
        # Arrange
        activity_name = "Drama Club"
        email_to_remove = "anna@mergington.edu"
        other_email = "james@mergington.edu"
        
        # Act
        unregister_from_activity(activity_name, email_to_remove)
        
        # Assert
        assert email_to_remove not in activities[activity_name]["participants"]
        assert other_email in activities[activity_name]["participants"]

    def test_unregister_fails_activity_not_found(self):
        """Test that unregister fails with 404 when activity doesn't exist."""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            unregister_from_activity(activity_name, email)
        
        assert exc_info.value.status_code == 404
        assert "Activity not found" in exc_info.value.detail

    def test_unregister_fails_student_not_signed_up(self):
        """Test that unregister fails with 400 when student isn't signed up."""
        # Arrange
        activity_name = "Chess Club"
        email = "notsignup@mergington.edu"  # Not signed up for Chess Club
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            unregister_from_activity(activity_name, email)
        
        assert exc_info.value.status_code == 400
        assert "not signed up" in exc_info.value.detail

    def test_unregister_frees_capacity(self):
        """Test that unregistering frees up capacity for others to join."""
        # Arrange
        activity_name = "Tennis Club"
        email_to_unregister = "jessica@mergington.edu"
        new_email = "newtennis@mergington.edu"
        
        # Fill activity to capacity
        for i in range(9):
            activities[activity_name]["participants"].append(f"filler{i}@mergington.edu")
        
        assert len(activities[activity_name]["participants"]) == 10
        
        # Act - unregister one student
        unregister_from_activity(activity_name, email_to_unregister)
        
        # Assert - new student can sign up
        assert len(activities[activity_name]["participants"]) == 9
        result = signup_for_activity(activity_name, new_email)
        assert "Signed up" in result["message"]
        assert new_email in activities[activity_name]["participants"]

    def test_unregister_with_single_participant(self):
        """Test unregister works when activity has only one participant."""
        # Arrange
        activity_name = "Art Studio"
        email = "lucy@mergington.edu"  # Only participant
        
        # Act
        result = unregister_from_activity(activity_name, email)
        
        # Assert
        assert len(activities[activity_name]["participants"]) == 0
        assert email not in activities[activity_name]["participants"]


# ============================================================================
# Integration-style Tests - Multiple Operations
# ============================================================================

class TestActivityWorkflows:
    """Test complex workflows combining multiple operations."""

    def test_signup_and_unregister_workflow(self):
        """Test signing up and then unregistering from an activity."""
        # Arrange
        activity_name = "Science Club"
        email = "scientist@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act - Sign up
        signup_result = signup_for_activity(activity_name, email)
        assert email in activities[activity_name]["participants"]
        
        # Act - Unregister
        unregister_result = unregister_from_activity(activity_name, email)
        
        # Assert
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count

    def test_multiple_signups_and_unregisters(self):
        """Test multiple students signing up and some unregistering."""
        # Arrange
        activity_name = "Programming Class"
        new_emails = ["new1@mergington.edu", "new2@mergington.edu", "new3@mergington.edu"]
        initial_count = len(activities[activity_name]["participants"])
        
        # Act - All sign up
        for email in new_emails:
            signup_for_activity(activity_name, email)
        
        # Assert all are enrolled
        assert len(activities[activity_name]["participants"]) == initial_count + 3
        
        # Act - Two unregister
        unregister_from_activity(activity_name, new_emails[0])
        unregister_from_activity(activity_name, new_emails[1])
        
        # Assert
        assert len(activities[activity_name]["participants"]) == initial_count + 1
        assert new_emails[0] not in activities[activity_name]["participants"]
        assert new_emails[1] not in activities[activity_name]["participants"]
        assert new_emails[2] in activities[activity_name]["participants"]

    def test_signup_after_capacity_freed(self):
        """Test full signup scenario: fill activity, unregister, then signup again."""
        # Arrange
        activity_name = "Gym Class"
        # Gym Class has max 30, currently has 2, so we need to add 28 more
        emails_to_add = [f"student{i}@mergington.edu" for i in range(28)]
        
        # Act - Fill to capacity
        for email in emails_to_add:
            signup_for_activity(activity_name, email)
        
        # Assert full
        assert len(activities[activity_name]["participants"]) == 30
        
        # Act - Try to add one more (should fail)
        with pytest.raises(HTTPException) as exc_info:
            signup_for_activity(activity_name, "overflow@mergington.edu")
        assert exc_info.value.status_code == 400
        
        # Act - Unregister one
        unregister_from_activity(activity_name, emails_to_add[0])
        
        # Assert - New signup succeeds
        new_signup = signup_for_activity(activity_name, "waitlist@mergington.edu")
        assert "Signed up" in new_signup["message"]
        assert "waitlist@mergington.edu" in activities[activity_name]["participants"]
