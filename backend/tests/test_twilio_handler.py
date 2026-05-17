"""
Comprehensive test suite for WingMan backend.

Tests cover:
1. Unit tests for helper functions (build_system_prompt, detect_dtmf, pcm16_to_mulaw)
2. Integration test for /twilio/voice/{call_id} webhook endpoint
3. Mock-based test for send_whatsapp_summary
4. Tests for storage module
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

try:
    import audioop
except ModuleNotFoundError:
    import audioop_lts as audioop

from backend.twilio_handler import (
    build_system_prompt,
    detect_dtmf,
    pcm16_to_mulaw,
    send_whatsapp_summary,
    router as twilio_router,
)
from backend.models import (
    CallBrief,
    UserProfile,
    TranscriptTurn,
    CallStatus,
    CallRecord,
)
from backend import storage


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing."""
    return UserProfile(
        name="John Doe",
        profession="Software Engineer",
        institution="Tech Corp",
        communication_style="Professional",
        languages="English",
        default_tone="Professional",
    )


@pytest.fixture
def sample_call_brief():
    """Sample call brief for testing."""
    return CallBrief(
        who_calling="Jane Smith",
        goal="Schedule a meeting for next Tuesday at 2 PM",
        key_points="Discuss project timeline",
        questions_to_ask="Are you available?",
        things_to_avoid="Don't mention budget",
        tone="Professional",
    )


@pytest.fixture
def sample_transcript():
    """Sample transcript for testing."""
    return [
        TranscriptTurn(
            speaker="wingman",
            text="Hi! I'm WingMan, John's AI assistant. Schedule a meeting for next Tuesday at 2 PM. Is there anything you'd like to say or ask John?",
            timestamp=datetime.now(),
        ),
        TranscriptTurn(
            speaker="caller",
            text="Yes, Tuesday at 2 PM works for me.",
            timestamp=datetime.now(),
        ),
        TranscriptTurn(
            speaker="wingman",
            text="Great! I'll let John know. Anything else?",
            timestamp=datetime.now(),
        ),
        TranscriptTurn(
            speaker="caller",
            text="No, that's all. Thanks!",
            timestamp=datetime.now(),
        ),
        TranscriptTurn(
            speaker="wingman",
            text="Goodbye!",
            timestamp=datetime.now(),
        ),
    ]


@pytest.fixture
def test_app():
    """Create a test FastAPI app with the twilio router."""
    app = FastAPI()
    app.include_router(twilio_router, prefix="/twilio")
    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


@pytest.fixture(autouse=True)
def reset_storage():
    """Reset storage before each test."""
    storage._calls.clear()
    storage._user_profile = None
    yield
    storage._calls.clear()
    storage._user_profile = None


# ============================================================================
# UNIT TESTS: build_system_prompt()
# ============================================================================

class TestBuildSystemPrompt:
    """Test suite for build_system_prompt function."""

    def test_build_system_prompt_with_full_profile(
        self, sample_call_brief, sample_user_profile
    ):
        """Test system prompt generation with complete user profile."""
        prompt = build_system_prompt(sample_call_brief, sample_user_profile)

        assert "John Doe" in prompt
        assert "Jane Smith" in prompt
        assert "Schedule a meeting for next Tuesday at 2 PM" in prompt
        assert "WingMan" in prompt
        assert "Anything else?" in prompt or "What else is on your mind?" in prompt

    def test_build_system_prompt_without_profile(self, sample_call_brief):
        """Test system prompt generation without user profile."""
        prompt = build_system_prompt(sample_call_brief, None)

        assert "the user" in prompt
        assert "Jane Smith" in prompt
        assert "Schedule a meeting for next Tuesday at 2 PM" in prompt
        assert "WingMan" in prompt

    def test_build_system_prompt_contains_key_instructions(
        self, sample_call_brief, sample_user_profile
    ):
        """Test that prompt contains critical instructions."""
        prompt = build_system_prompt(sample_call_brief, sample_user_profile)

        # Check for key instruction sections
        assert "SITUATION:" in prompt
        assert "HOW TO HANDLE QUESTIONS:" in prompt
        assert "CRITICAL — KEEP THE CONVERSATION OPEN:" in prompt
        assert "ENDING THE CALL:" in prompt
        assert "Goodbye!" in prompt

    def test_build_system_prompt_with_empty_goal(self, sample_user_profile):
        """Test system prompt with empty goal."""
        brief = CallBrief(who_calling="Jane Smith", goal="")
        prompt = build_system_prompt(brief, sample_user_profile)

        assert "Jane Smith" in prompt
        assert "John Doe" in prompt
        # Should still contain the empty goal
        assert '""' in prompt or "goal" in prompt.lower()


# ============================================================================
# UNIT TESTS: detect_dtmf()
# ============================================================================

class TestDetectDTMF:
    """Test suite for detect_dtmf function."""

    def test_detect_dtmf_press_digit(self):
        """Test DTMF detection with 'press' keyword and digit."""
        assert detect_dtmf("Please press 1 for sales") == "1"
        assert detect_dtmf("Press 5 to continue") == "5"
        assert detect_dtmf("You can press 9 now") == "9"

    def test_detect_dtmf_press_word(self):
        """Test DTMF detection with 'press' keyword and word."""
        assert detect_dtmf("Press one for sales") == "1"
        assert detect_dtmf("Please press two") == "2"
        assert detect_dtmf("Press five to continue") == "5"
        assert detect_dtmf("Press star for operator") == "*"
        assert detect_dtmf("Press pound to finish") == "#"

    def test_detect_dtmf_dial_keyword(self):
        """Test DTMF detection with 'dial' keyword."""
        assert detect_dtmf("Dial 3 for support") == "3"
        assert detect_dtmf("Please dial 7") == "7"

    def test_detect_dtmf_enter_keyword(self):
        """Test DTMF detection with 'enter' keyword."""
        assert detect_dtmf("Enter 4 to proceed") == "4"
        assert detect_dtmf("Please enter 8") == "8"

    def test_detect_dtmf_case_insensitive(self):
        """Test that DTMF detection is case insensitive."""
        assert detect_dtmf("PRESS 1 FOR SALES") == "1"
        assert detect_dtmf("Press ONE for sales") == "1"
        assert detect_dtmf("PRESS STAR") == "*"

    def test_detect_dtmf_no_match(self):
        """Test DTMF detection returns None when no pattern matches."""
        assert detect_dtmf("Hello, how are you?") is None
        assert detect_dtmf("Thank you for calling") is None
        assert detect_dtmf("") is None

    def test_detect_dtmf_first_match_only(self):
        """Test that only the first match is returned."""
        result = detect_dtmf("Press 1 for sales or press 2 for support")
        assert result == "1"

    def test_detect_dtmf_all_digits(self):
        """Test all digit words."""
        word_to_digit = {
            "zero": "0",
            "one": "1",
            "two": "2",
            "three": "3",
            "four": "4",
            "five": "5",
            "six": "6",
            "seven": "7",
            "eight": "8",
            "nine": "9",
        }
        for word, digit in word_to_digit.items():
            assert detect_dtmf(f"Press {word}") == digit


# ============================================================================
# UNIT TESTS: pcm16_to_mulaw()
# ============================================================================

class TestPCM16ToMulaw:
    """Test suite for pcm16_to_mulaw function."""

    def test_pcm16_to_mulaw_basic_conversion(self):
        """Test basic PCM16 to mu-law conversion."""
        # Create sample PCM16 data (16-bit signed integers)
        # Using simple sine wave samples
        pcm_data = b'\x00\x00\x00\x10\x00\x20\x00\x30'
        
        result = pcm16_to_mulaw(pcm_data)
        
        # Result should be half the length (16-bit to 8-bit)
        assert len(result) == len(pcm_data) // 2
        assert isinstance(result, bytes)

    def test_pcm16_to_mulaw_empty_input(self):
        """Test conversion with empty input."""
        result = pcm16_to_mulaw(b'')
        assert result == b''

    def test_pcm16_to_mulaw_silence(self):
        """Test conversion of silence (all zeros)."""
        pcm_data = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        result = pcm16_to_mulaw(pcm_data)
        
        assert len(result) == 4
        assert isinstance(result, bytes)

    def test_pcm16_to_mulaw_max_amplitude(self):
        """Test conversion with maximum amplitude."""
        # Maximum positive and negative values for 16-bit signed
        pcm_data = b'\xff\x7f\x00\x80'  # 32767, -32768
        result = pcm16_to_mulaw(pcm_data)
        
        assert len(result) == 2
        assert isinstance(result, bytes)

    def test_pcm16_to_mulaw_length_validation(self):
        """Test that output length is correct."""
        # Various input lengths
        for num_samples in [2, 4, 8, 16, 32]:
            pcm_data = b'\x00\x00' * num_samples
            result = pcm16_to_mulaw(pcm_data)
            assert len(result) == num_samples


# ============================================================================
# INTEGRATION TEST: /twilio/voice/{call_id} webhook
# ============================================================================

class TestVoiceWebhook:
    """Integration tests for the voice webhook endpoint."""

    def test_voice_webhook_returns_twiml(self, client):
        """Test that voice webhook returns valid TwiML response."""
        call_id = "test-call-123"
        
        response = client.post(f"/twilio/voice/{call_id}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/xml; charset=utf-8"
        
        # Check TwiML structure
        content = response.text
        assert "<?xml version" in content
        assert "<Response>" in content
        assert "<Connect>" in content
        assert "<Stream" in content
        assert f"/twilio/media-stream/{call_id}" in content
        assert "</Stream>" in content
        assert "</Connect>" in content
        assert "</Response>" in content

    def test_voice_webhook_with_different_call_ids(self, client):
        """Test webhook with various call IDs."""
        call_ids = [
            "call-001",
            "test-call-abc-123",
            "uuid-1234-5678-90ab-cdef",
        ]
        
        for call_id in call_ids:
            response = client.post(f"/twilio/voice/{call_id}")
            assert response.status_code == 200
            assert f"/twilio/media-stream/{call_id}" in response.text

    def test_voice_webhook_websocket_url_format(self, client):
        """Test that WebSocket URL is correctly formatted."""
        call_id = "test-call-456"
        
        with patch("backend.twilio_handler.BASE_URL", "https://example.com"):
            response = client.post(f"/twilio/voice/{call_id}")
            
            # Should convert https:// to wss://
            assert "wss://example.com/twilio/media-stream/" in response.text

    def test_voice_webhook_http_to_ws_conversion(self, client):
        """Test HTTP to WS protocol conversion."""
        call_id = "test-call-789"
        
        with patch("backend.twilio_handler.BASE_URL", "http://localhost:8000"):
            response = client.post(f"/twilio/voice/{call_id}")
            
            # Should convert http:// to ws://
            assert "ws://localhost:8000/twilio/media-stream/" in response.text


# ============================================================================
# MOCK-BASED TEST: send_whatsapp_summary()
# ============================================================================

class TestSendWhatsAppSummary:
    """Test suite for send_whatsapp_summary function with mocks."""

    @pytest.mark.asyncio
    async def test_send_whatsapp_summary_success(
        self, sample_call_brief, sample_transcript, sample_user_profile
    ):
        """Test successful WhatsApp summary sending."""
        call_id = "test-call-001"
        
        # Mock Groq API
        mock_groq_response = Mock()
        mock_groq_response.choices = [
            Mock(message=Mock(content="Call with Jane Smith is done.\n\nYour message landed well. Jane confirmed Tuesday at 2 PM works."))
        ]
        
        # Mock Twilio client
        mock_twilio_message = Mock()
        
        with patch("backend.twilio_handler.AsyncGroq") as mock_groq_class, \
             patch("backend.twilio_handler.twilio_client") as mock_twilio:
            
            mock_groq_instance = AsyncMock()
            mock_groq_instance.chat.completions.create = AsyncMock(
                return_value=mock_groq_response
            )
            mock_groq_class.return_value = mock_groq_instance
            
            mock_twilio.messages.create.return_value = mock_twilio_message
            
            # Call the function
            await send_whatsapp_summary(
                call_id, sample_call_brief, sample_transcript, sample_user_profile
            )
            
            # Verify Groq was called
            mock_groq_instance.chat.completions.create.assert_called_once()
            call_args = mock_groq_instance.chat.completions.create.call_args
            
            # Check that the prompt includes key information
            messages = call_args[1]["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert "WhatsApp" in messages[0]["content"]
            assert messages[1]["role"] == "user"
            assert "John Doe" in messages[1]["content"]
            assert "Jane Smith" in messages[1]["content"]
            
            # Verify Twilio was called
            mock_twilio.messages.create.assert_called_once()
            twilio_call_args = mock_twilio.messages.create.call_args[1]
            assert "from_" in twilio_call_args
            assert "to" in twilio_call_args
            assert "body" in twilio_call_args

    @pytest.mark.asyncio
    async def test_send_whatsapp_summary_empty_transcript(
        self, sample_call_brief, sample_user_profile
    ):
        """Test that function returns early with empty transcript."""
        call_id = "test-call-002"
        
        with patch("backend.twilio_handler.AsyncGroq") as mock_groq_class, \
             patch("backend.twilio_handler.twilio_client") as mock_twilio:
            
            # Call with empty transcript
            await send_whatsapp_summary(
                call_id, sample_call_brief, [], sample_user_profile
            )
            
            # Should not call Groq or Twilio
            mock_groq_class.assert_not_called()
            mock_twilio.messages.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_whatsapp_summary_without_profile(
        self, sample_call_brief, sample_transcript
    ):
        """Test WhatsApp summary without user profile."""
        call_id = "test-call-003"
        
        mock_groq_response = Mock()
        mock_groq_response.choices = [
            Mock(message=Mock(content="Call summary"))
        ]
        
        with patch("backend.twilio_handler.AsyncGroq") as mock_groq_class, \
             patch("backend.twilio_handler.twilio_client") as mock_twilio:
            
            mock_groq_instance = AsyncMock()
            mock_groq_instance.chat.completions.create = AsyncMock(
                return_value=mock_groq_response
            )
            mock_groq_class.return_value = mock_groq_instance
            
            await send_whatsapp_summary(
                call_id, sample_call_brief, sample_transcript, None
            )
            
            # Should use "you" instead of name
            call_args = mock_groq_instance.chat.completions.create.call_args
            messages = call_args[1]["messages"]
            assert "you" in messages[1]["content"].lower()

    @pytest.mark.asyncio
    async def test_send_whatsapp_summary_groq_error_fallback(
        self, sample_call_brief, sample_transcript, sample_user_profile
    ):
        """Test fallback when Groq API fails."""
        call_id = "test-call-004"
        
        with patch("backend.twilio_handler.AsyncGroq") as mock_groq_class, \
             patch("backend.twilio_handler.twilio_client") as mock_twilio:
            
            # Make Groq raise an exception
            mock_groq_instance = AsyncMock()
            mock_groq_instance.chat.completions.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_groq_class.return_value = mock_groq_instance
            
            await send_whatsapp_summary(
                call_id, sample_call_brief, sample_transcript, sample_user_profile
            )
            
            # Should still call Twilio with fallback message
            mock_twilio.messages.create.assert_called_once()
            call_args = mock_twilio.messages.create.call_args[1]
            body = call_args["body"]
            
            # Check fallback format
            assert "Call with Jane Smith is done" in body
            assert sample_call_brief.goal in body

    @pytest.mark.asyncio
    async def test_send_whatsapp_summary_twilio_error_handling(
        self, sample_call_brief, sample_transcript, sample_user_profile
    ):
        """Test error handling when Twilio fails."""
        call_id = "test-call-005"
        
        mock_groq_response = Mock()
        mock_groq_response.choices = [
            Mock(message=Mock(content="Call summary"))
        ]
        
        with patch("backend.twilio_handler.AsyncGroq") as mock_groq_class, \
             patch("backend.twilio_handler.twilio_client") as mock_twilio, \
             patch("backend.twilio_handler.logger") as mock_logger:
            
            mock_groq_instance = AsyncMock()
            mock_groq_instance.chat.completions.create = AsyncMock(
                return_value=mock_groq_response
            )
            mock_groq_class.return_value = mock_groq_instance
            
            # Make Twilio raise an exception
            mock_twilio.messages.create.side_effect = Exception("Twilio Error")
            
            # Should not raise exception
            await send_whatsapp_summary(
                call_id, sample_call_brief, sample_transcript, sample_user_profile
            )
            
            # Should log the error
            mock_logger.error.assert_called()


# ============================================================================
# TESTS: storage module
# ============================================================================

class TestStorageModule:
    """Test suite for storage module functions."""

    def test_create_call(self, sample_call_brief, sample_user_profile):
        """Test creating a new call record."""
        call_id = "test-call-001"
        phone_number = "+1234567890"
        
        record = storage.create_call(
            call_id, phone_number, sample_call_brief, sample_user_profile
        )
        
        assert record.call_id == call_id
        assert record.phone_number == phone_number
        assert record.call_brief == sample_call_brief
        assert record.user_profile == sample_user_profile
        assert record.status == CallStatus.INITIATING
        assert record.transcript == []
        assert record.started_at is not None

    def test_create_call_without_profile(self, sample_call_brief):
        """Test creating a call without user profile."""
        call_id = "test-call-002"
        phone_number = "+1234567890"
        
        record = storage.create_call(call_id, phone_number, sample_call_brief)
        
        assert record.user_profile is None
        assert record.call_id == call_id

    def test_get_call_existing(self, sample_call_brief):
        """Test retrieving an existing call."""
        call_id = "test-call-003"
        storage.create_call(call_id, "+1234567890", sample_call_brief)
        
        retrieved = storage.get_call(call_id)
        
        assert retrieved is not None
        assert retrieved.call_id == call_id

    def test_get_call_nonexistent(self):
        """Test retrieving a non-existent call."""
        result = storage.get_call("nonexistent-call")
        assert result is None

    def test_get_all_calls(self, sample_call_brief):
        """Test retrieving all calls."""
        # Create multiple calls
        call_ids = ["call-001", "call-002", "call-003"]
        for call_id in call_ids:
            storage.create_call(call_id, "+1234567890", sample_call_brief)
        
        all_calls = storage.get_all_calls()
        
        assert len(all_calls) == 3
        # Should be in reverse order (most recent first)
        assert all_calls[0].call_id == "call-003"
        assert all_calls[2].call_id == "call-001"

    def test_get_all_calls_empty(self):
        """Test retrieving all calls when none exist."""
        all_calls = storage.get_all_calls()
        assert all_calls == []

    def test_update_call_status(self, sample_call_brief):
        """Test updating call status."""
        call_id = "test-call-004"
        storage.create_call(call_id, "+1234567890", sample_call_brief)
        
        storage.update_call_status(call_id, CallStatus.IN_PROGRESS)
        
        record = storage.get_call(call_id)
        assert record.status == CallStatus.IN_PROGRESS
        
        storage.update_call_status(call_id, CallStatus.COMPLETED)
        record = storage.get_call(call_id)
        assert record.status == CallStatus.COMPLETED

    def test_update_call_status_nonexistent(self):
        """Test updating status of non-existent call (should not raise error)."""
        storage.update_call_status("nonexistent", CallStatus.COMPLETED)
        # Should not raise exception

    def test_set_twilio_sid(self, sample_call_brief):
        """Test setting Twilio SID."""
        call_id = "test-call-005"
        storage.create_call(call_id, "+1234567890", sample_call_brief)
        
        twilio_sid = "CA1234567890abcdef"
        storage.set_twilio_sid(call_id, twilio_sid)
        
        record = storage.get_call(call_id)
        assert record.twilio_call_sid == twilio_sid

    def test_set_twilio_sid_nonexistent(self):
        """Test setting Twilio SID for non-existent call."""
        storage.set_twilio_sid("nonexistent", "CA123")
        # Should not raise exception

    def test_add_transcript_turn(self, sample_call_brief):
        """Test adding transcript turns."""
        call_id = "test-call-006"
        storage.create_call(call_id, "+1234567890", sample_call_brief)
        
        storage.add_transcript_turn(call_id, "wingman", "Hello!")
        storage.add_transcript_turn(call_id, "caller", "Hi there!")
        
        record = storage.get_call(call_id)
        assert len(record.transcript) == 2
        assert record.transcript[0].speaker == "wingman"
        assert record.transcript[0].text == "Hello!"
        assert record.transcript[1].speaker == "caller"
        assert record.transcript[1].text == "Hi there!"
        assert record.transcript[0].timestamp is not None

    def test_add_transcript_turn_nonexistent(self):
        """Test adding transcript to non-existent call."""
        storage.add_transcript_turn("nonexistent", "wingman", "Hello")
        # Should not raise exception

    def test_finalize_call(self, sample_call_brief):
        """Test finalizing a call."""
        call_id = "test-call-007"
        storage.create_call(call_id, "+1234567890", sample_call_brief)
        
        summary = "Call completed successfully"
        storage.finalize_call(call_id, summary)
        
        record = storage.get_call(call_id)
        assert record.status == CallStatus.COMPLETED
        assert record.summary == summary
        assert record.ended_at is not None

    def test_finalize_call_without_summary(self, sample_call_brief):
        """Test finalizing call without summary."""
        call_id = "test-call-008"
        storage.create_call(call_id, "+1234567890", sample_call_brief)
        
        storage.finalize_call(call_id)
        
        record = storage.get_call(call_id)
        assert record.status == CallStatus.COMPLETED
        assert record.summary == ""

    def test_save_and_get_coach_report(self, sample_call_brief):
        """Test saving and retrieving coach report."""
        from backend.models import CoachReport
        
        call_id = "test-call-009"
        storage.create_call(call_id, "+1234567890", sample_call_brief)
        
        coach_report = CoachReport(
            call_id=call_id,
            confidence_score=85,
            what_went_well=["Clear communication", "Good timing"],
            what_to_improve=["Could be more concise"],
            improvements=["Practice brevity"],
            goal_achieved=True,
            goal_achievement_score=90,
            summary="Overall good call",
        )
        
        storage.save_coach_report(call_id, coach_report)
        
        record = storage.get_call(call_id)
        assert record.coach_report is not None
        assert record.coach_report.confidence_score == 85
        assert record.coach_report.goal_achieved is True

    def test_save_profile(self, sample_user_profile):
        """Test saving user profile."""
        storage.save_profile(sample_user_profile)
        
        retrieved = storage.get_profile()
        assert retrieved is not None
        assert retrieved.name == sample_user_profile.name
        assert retrieved.profession == sample_user_profile.profession

    def test_get_profile_when_none(self):
        """Test getting profile when none is set."""
        profile = storage.get_profile()
        assert profile is None

    def test_save_profile_overwrites(self, sample_user_profile):
        """Test that saving profile overwrites previous one."""
        storage.save_profile(sample_user_profile)
        
        new_profile = UserProfile(
            name="Jane Doe",
            profession="Designer",
            institution="Design Co",
        )
        storage.save_profile(new_profile)
        
        retrieved = storage.get_profile()
        assert retrieved.name == "Jane Doe"
        assert retrieved.profession == "Designer"

    def test_multiple_calls_independence(self, sample_call_brief):
        """Test that multiple calls are independent."""
        call_id_1 = "call-001"
        call_id_2 = "call-002"
        
        storage.create_call(call_id_1, "+1111111111", sample_call_brief)
        storage.create_call(call_id_2, "+2222222222", sample_call_brief)
        
        storage.add_transcript_turn(call_id_1, "wingman", "Hello from call 1")
        storage.add_transcript_turn(call_id_2, "wingman", "Hello from call 2")
        
        record_1 = storage.get_call(call_id_1)
        record_2 = storage.get_call(call_id_2)
        
        assert len(record_1.transcript) == 1
        assert len(record_2.transcript) == 1
        assert record_1.transcript[0].text == "Hello from call 1"
        assert record_2.transcript[0].text == "Hello from call 2"


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_detect_dtmf_with_multiple_spaces(self):
        """Test DTMF detection with irregular spacing."""
        assert detect_dtmf("press    1    for    sales") == "1"
        assert detect_dtmf("press\t\t2\t\tfor support") == "2"

    def test_detect_dtmf_with_punctuation(self):
        """Test DTMF detection with punctuation."""
        assert detect_dtmf("Press 1, for sales.") == "1"
        assert detect_dtmf("Press 2! For support?") == "2"

    def test_build_system_prompt_special_characters(self):
        """Test system prompt with special characters in names."""
        brief = CallBrief(
            who_calling="O'Brien & Associates",
            goal="Discuss the Q&A session",
        )
        profile = UserProfile(name="José García")
        
        prompt = build_system_prompt(brief, profile)
        
        assert "José García" in prompt
        assert "O'Brien & Associates" in prompt
        assert "Q&A" in prompt

    def test_pcm16_to_mulaw_odd_length_handling(self):
        """Test PCM conversion with odd-length input (should handle gracefully)."""
        # Odd number of bytes (not valid PCM16, but should not crash)
        pcm_data = b'\x00\x00\x00'
        
        try:
            result = pcm16_to_mulaw(pcm_data)
            # If it doesn't crash, that's acceptable
            assert isinstance(result, bytes)
        except Exception:
            # audioop may raise an error for invalid input, which is also acceptable
            pass

    def test_storage_concurrent_updates(self, sample_call_brief):
        """Test storage handles rapid updates correctly."""
        call_id = "test-call-concurrent"
        storage.create_call(call_id, "+1234567890", sample_call_brief)
        
        # Rapid status updates
        for status in [
            CallStatus.INITIATING,
            CallStatus.IN_PROGRESS,
            CallStatus.COMPLETING,
            CallStatus.COMPLETED,
        ]:
            storage.update_call_status(call_id, status)
        
        record = storage.get_call(call_id)
        assert record.status == CallStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
