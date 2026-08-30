"""Unit tests for kegomodoro.audio."""

from unittest.mock import MagicMock

from kegomodoro.audio import SoundService
from kegomodoro.timer import SoundRole


def test_audio_disabled():
    service = SoundService(enable_audio=False)
    assert service.enabled is False
    assert service.available is False
    # Playing should be a no-op and never raise
    service.play(SoundRole.SHORT_BREAK)


def test_audio_mixer_failure(monkeypatch):
    import sys

    # Simulate pygame mixer error
    fake_pygame = MagicMock()
    fake_pygame.mixer.init.side_effect = RuntimeError("No audio device available")
    fake_pygame.mixer.get_init.return_value = False
    monkeypatch.setitem(sys.modules, "pygame", fake_pygame)

    service = SoundService(enable_audio=True)
    assert service.available is False
    # Should not raise
    service.play(SoundRole.WORK)


def test_audio_successful_mock(monkeypatch, tmp_path):
    import sys

    fake_sound = MagicMock()
    fake_pygame = MagicMock()
    fake_pygame.mixer.get_init.return_value = True
    fake_pygame.mixer.Sound.return_value = fake_sound
    monkeypatch.setitem(sys.modules, "pygame", fake_pygame)

    # Create dummy audio files
    audio_dir = tmp_path / "audios"
    audio_dir.mkdir()
    (audio_dir / "short_break.mp3").write_bytes(b"dummy")
    (audio_dir / "long_break.mp3").write_bytes(b"dummy")
    (audio_dir / "work.mp3").write_bytes(b"dummy")
    (audio_dir / "new_work.mp3").write_bytes(b"dummy")

    service = SoundService(audio_dir=audio_dir, enable_audio=True)
    assert service.available is True
    assert len(service.sounds) == 4

    service.play(SoundRole.SHORT_BREAK)
    fake_sound.play.assert_called_once()
