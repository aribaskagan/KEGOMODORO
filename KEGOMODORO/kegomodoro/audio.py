"""Safe audio loading and playback service for KEGOMODORO."""

import logging
from pathlib import Path
from typing import Optional

from kegomodoro.paths import get_resource_path
from kegomodoro.timer import SoundRole

logger = logging.getLogger(__name__)


class SoundService:
    """Manages audio initialization and playback with graceful fallback."""

    def __init__(self, audio_dir: Optional[Path] = None, enable_audio: bool = True):
        self.enabled = enable_audio
        self.available = False
        self.sounds: dict[SoundRole, object] = {}

        if not self.enabled:
            return

        if audio_dir is None:
            audio_dir = get_resource_path("dependencies/audios")
        self.audio_dir = audio_dir

        self._init_mixer()

    def _init_mixer(self) -> None:
        try:
            import pygame

            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.available = True
            self._load_sounds()
        except Exception as e:
            self.available = False
            logger.warning(f"Audio device/mixer unavailable: {e}")

    def _load_sounds(self) -> None:
        if not self.available:
            return

        import pygame

        sound_files = {
            SoundRole.SHORT_BREAK: "short_break.mp3",
            SoundRole.LONG_BREAK: "long_break.mp3",
            SoundRole.WORK: "work.mp3",
            SoundRole.NEW_WORK: "new_work.mp3",
        }

        for role, filename in sound_files.items():
            path = self.audio_dir / filename
            if path.is_file():
                try:
                    sound = pygame.mixer.Sound(str(path))
                    if role == SoundRole.SHORT_BREAK:
                        sound.set_volume(0.5)
                    self.sounds[role] = sound
                except Exception as e:
                    logger.warning(f"Could not load audio file {path}: {e}")
            else:
                logger.warning(f"Audio asset missing: {path}")

    def play(self, role: SoundRole) -> None:
        """Play sound for the specified role safely."""
        if not self.available or not self.enabled or role == SoundRole.NONE:
            return

        sound = self.sounds.get(role)
        if sound is not None:
            try:
                sound.play()
            except Exception as e:
                logger.warning(f"Failed to play sound for {role}: {e}")
