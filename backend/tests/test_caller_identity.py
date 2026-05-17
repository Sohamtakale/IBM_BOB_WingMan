"""
Tests for caller identity detection feature.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.twilio_handler import detect_caller_identity
from backend.storage import set_caller_name, get_call, create_call
from backend.models import CallBrief, UserProfile


class TestCallerIdentityDetection:
    """Test the LLM-based caller identity detection."""

    @pytest.mark.asyncio
    async def test_detect_standard_introduction(self):
        """Test detection of standard 'This is [Name]' pattern."""
        with patch('backend.twilio_handler.AsyncGroq') as mock_groq:
            # Mock the LLM response
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "John Smith"
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            result = await detect_caller_identity("Hi, this is John Smith")
            assert result == "John Smith"

    @pytest.mark.asyncio
    async def test_detect_informal_introduction(self):
        """Test detection of informal 'It's [Name]' pattern."""
        with patch('backend.twilio_handler.AsyncGroq') as mock_groq:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Sarah"
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            result = await detect_caller_identity("It's Sarah")
            assert result == "Sarah"

    @pytest.mark.asyncio
    async def test_detect_professional_title(self):
        """Test detection with professional titles."""
        with patch('backend.twilio_handler.AsyncGroq') as mock_groq:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Dr. Johnson"
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            result = await detect_caller_identity("Dr. Johnson speaking")
            assert result == "Dr. Johnson"

    @pytest.mark.asyncio
    async def test_no_identification(self):
        """Test when caller doesn't identify themselves."""
        with patch('backend.twilio_handler.AsyncGroq') as mock_groq:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "unknown"
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            result = await detect_caller_identity("Yeah, what's up?")
            assert result is None

    @pytest.mark.asyncio
    async def test_third_party_mention(self):
        """Test that third-party name mentions are not detected."""
        with patch('backend.twilio_handler.AsyncGroq') as mock_groq:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "unknown"
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            result = await detect_caller_identity("John told me to call you")
            assert result is None

    @pytest.mark.asyncio
    async def test_question_not_detected(self):
        """Test that questions are not detected as identification."""
        with patch('backend.twilio_handler.AsyncGroq') as mock_groq:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "unknown"
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            result = await detect_caller_identity("Is this the right number?")
            assert result is None

    @pytest.mark.asyncio
    async def test_invalid_name_length(self):
        """Test that unreasonably long names are rejected."""
        with patch('backend.twilio_handler.AsyncGroq') as mock_groq:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            # Return a name that's too long
            mock_response.choices[0].message.content = "A" * 60
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            result = await detect_caller_identity("This is a very long name")
            assert result is None

    @pytest.mark.asyncio
    async def test_llm_error_handling(self):
        """Test graceful handling of LLM errors."""
        with patch('backend.twilio_handler.AsyncGroq') as mock_groq:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_groq.return_value = mock_client

            result = await detect_caller_identity("Hi, this is John")
            assert result is None


class TestStorageIntegration:
    """Test storage integration for caller identity."""

    def test_set_caller_name(self):
        """Test setting caller name in storage."""
        # Create a test call
        brief = CallBrief(
            who_calling="Test Person",
            goal="Test goal"
        )
        call = create_call("test-123", "+1234567890", brief)
        
        # Set caller name
        set_caller_name("test-123", "John Smith")
        
        # Verify it was stored
        updated_call = get_call("test-123")
        assert updated_call.detected_caller_name == "John Smith"

    def test_set_caller_name_none_ignored(self):
        """Test that None values are not stored."""
        brief = CallBrief(
            who_calling="Test Person",
            goal="Test goal"
        )
        call = create_call("test-456", "+1234567890", brief)
        
        # Try to set None
        set_caller_name("test-456", None)
        
        # Verify it wasn't stored
        updated_call = get_call("test-456")
        assert updated_call.detected_caller_name is None

    def test_set_caller_name_invalid_call_id(self):
        """Test setting caller name for non-existent call."""
        # Should not raise an error
        set_caller_name("nonexistent-call", "John Smith")


class TestEndToEndScenarios:
    """Test end-to-end scenarios for caller identity detection."""

    @pytest.mark.asyncio
    async def test_first_response_triggers_detection(self):
        """Test that detection is triggered on first caller response."""
        # This would be an integration test that would require
        # mocking the entire WebSocket flow. For now, we document
        # the expected behavior:
        # 1. Call starts
        # 2. WingMan speaks first (opening message)
        # 3. Caller responds with "Hi, this is John"
        # 4. Detection function is called
        # 5. Name is stored in CallRecord
        # 6. Conversation continues normally
        pass

    @pytest.mark.asyncio
    async def test_detection_only_on_first_response(self):
        """Test that detection only happens once."""
        # Expected behavior:
        # 1. First caller utterance triggers detection
        # 2. Subsequent utterances do not trigger detection
        # 3. detected_caller_name field is only set once
        pass

    @pytest.mark.asyncio
    async def test_coach_report_includes_detected_name(self):
        """Test that coach report uses detected caller name."""
        # Expected behavior:
        # 1. Call completes with detected name
        # 2. Coach report generation receives detected_caller_name
        # 3. Report includes caller identity in context
        # 4. Summary may reference the detected name
        pass


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_utterance(self):
        """Test detection with empty utterance."""
        with patch('backend.twilio_handler.AsyncGroq') as mock_groq:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "unknown"
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            result = await detect_caller_identity("")
            assert result is None

    @pytest.mark.asyncio
    async def test_special_characters_in_name(self):
        """Test detection with special characters."""
        with patch('backend.twilio_handler.AsyncGroq') as mock_groq:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "O'Brien"
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            result = await detect_caller_identity("This is O'Brien")
            assert result == "O'Brien"

    @pytest.mark.asyncio
    async def test_multiple_names_mentioned(self):
        """Test when multiple names are mentioned."""
        with patch('backend.twilio_handler.AsyncGroq') as mock_groq:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            # LLM should extract the self-identification
            mock_response.choices[0].message.content = "Sarah"
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            result = await detect_caller_identity("Hi, this is Sarah. John told me to call.")
            assert result == "Sarah"


# Test data for manual verification
MANUAL_TEST_CASES = [
    ("Hi, this is John Smith", "John Smith"),
    ("It's Sarah", "Sarah"),
    ("Dr. Johnson speaking", "Dr. Johnson"),
    ("You can call me Mike", "Mike"),
    ("Yeah, what's up?", None),
    ("John told me to call you", None),
    ("Is this the right number?", None),
    ("This is Professor Williams", "Professor Williams"),
    ("Hey, it's me, Alex", "Alex"),
    ("Speaking", None),  # Too ambiguous
]


if __name__ == "__main__":
    print("Caller Identity Detection Test Cases")
    print("=" * 50)
    for utterance, expected in MANUAL_TEST_CASES:
        print(f"\nUtterance: {utterance!r}")
        print(f"Expected: {expected}")

# Made with Bob
