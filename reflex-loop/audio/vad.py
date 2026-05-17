# audio/vad.py
import sys
import os
import audioop
import math

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

class VoiceActivityDetector:
    def __init__(self, mode=None):
        self.mode = mode if mode is not None else config.VAD_MODE
        self.sample_rate = config.SAMPLE_RATE
        # Initialize fallback check
        self.fallback_active = False
        self.vad = None

        # 1. Try to load WebRTCVAD (Standard)
        try:
            import webrtcvad
            self.vad = webrtcvad.Vad()
            self.vad.set_mode(self.mode)
            print("[VAD] Loaded WebRTCVAD successfully.")
        except ImportError:
            # 2. Try WebRTCVAD Wheels (Windows fix)
            try:
                import webrtcvad_wheels as webrtcvad
                self.vad = webrtcvad.Vad()
                self.vad.set_mode(self.mode)
                print("[VAD] Loaded WebRTCVAD (Wheels) successfully.")
            except ImportError:
                # 3. Enable Energy Fallback
                self.fallback_active = True
                print("[VAD] Warning: WebRTCVAD not found. Switched to Energy VAD Fallback.")

    def is_speech(self, frame_bytes):
        """
        Returns True if the frame contains speech.
        Uses WebRTCVAD if available, otherwise Energy Threshold.
        """
        # Try WebRTCVAD first if valid
        if not self.fallback_active and self.vad:
            try:
                return self.vad.is_speech(frame_bytes, self.sample_rate)
            except Exception:
                # If specific frame fails (e.g. wrong size), fallback for this frame
                pass
        
        # --- ENERGY FALLBACK ---
        # Calculate RMS (Root Mean Square) energy of the audio frame
        try:
            # width=2 for 16-bit audio
            rms = audioop.rms(frame_bytes, 2) 
            
            # Simple thresholding
            # Silence is usually < 200. Speech can be > 300-500.
            threshold = getattr(config, 'VAD_THRESHOLD_ENERGY', 300)
            
            return rms > threshold
        except Exception as e:
            # If audioop fails (rare), return False to be safe
            return False

if __name__ == "__main__":
    print("Initializing VAD...")
    vad = VoiceActivityDetector()
    
    # Test Silent Frame
    # Calculate frame size: (Sample Rate * Duration / 1000) * 2 bytes/sample
    frame_size = int(config.SAMPLE_RATE * config.FRAME_DURATION_MS / 1000) * 2
    dummy_frame = b'\x00' * frame_size
    
    print(f"Fallback Active: {vad.fallback_active}")
    print(f"Is silent frame speech? {vad.is_speech(dummy_frame)}")
