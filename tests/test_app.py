import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivities:
    """Test cases for the activities endpoint"""

    def test_get_activities(self):
        """Test fetching all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activity_structure(self):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignup:
    """Test cases for the signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@example.com"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@example.com" in data["message"]

    def test_signup_duplicate(self):
        """Test that duplicate signups are rejected"""
        email = "duplicate@example.com"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_invalid_activity(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@example.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_updates_participant_list(self):
        """Test that signup updates the participant list"""
        email = "newstudent@example.com"
        
        # Get initial participant count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Drama Club"]["participants"])
        
        # Sign up
        client.post(f"/activities/Drama Club/signup?email={email}")
        
        # Check updated participant count
        response2 = client.get("/activities")
        new_count = len(response2.json()["Drama Club"]["participants"])
        
        assert new_count == initial_count + 1
        assert email in response2.json()["Drama Club"]["participants"]


class TestRemoveParticipant:
    """Test cases for the remove participant endpoint"""

    def test_remove_success(self):
        """Test successful removal from an activity"""
        # First add a participant
        email = "remove-test@example.com"
        client.post(f"/activities/Art Club/signup?email={email}")
        
        # Then remove them
        response = client.post(
            f"/activities/Art Club/remove?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Removed" in data["message"]

    def test_remove_nonexistent_participant(self):
        """Test removing a participant who is not signed up"""
        response = client.post(
            "/activities/Soccer/remove?email=notamember@example.com"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_remove_invalid_activity(self):
        """Test removing from non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/remove?email=test@example.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_updates_participant_list(self):
        """Test that removal updates the participant list"""
        email = "removeme@example.com"
        
        # Sign up
        client.post(f"/activities/Basketball/signup?email={email}")
        
        # Verify they're added
        response1 = client.get("/activities")
        assert email in response1.json()["Basketball"]["participants"]
        
        # Remove them
        client.post(f"/activities/Basketball/remove?email={email}")
        
        # Verify they're removed
        response2 = client.get("/activities")
        assert email not in response2.json()["Basketball"]["participants"]


class TestRootEndpoint:
    """Test cases for the root endpoint"""

    def test_root_redirect(self):
        """Test that root redirects to static HTML"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
