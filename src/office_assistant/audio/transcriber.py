from __future__ import annotations

from pathlib import Path

from office_assistant.config.schema import WhisperConfig
from office_assistant.models.meeting import SegmentInfo, Transcript


class WhisperTranscriber:
    def __init__(self, config: WhisperConfig):
        self.config = config
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            device = self.config.device
            if device == "auto":
                try:
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                except ImportError:
                    device = "cpu"

            self._model = WhisperModel(
                self.config.model_size,
                device=device,
                compute_type=self.config.compute_type,
            )
        return self._model

    def transcribe(self, audio_path: Path, language: str | None = None) -> Transcript:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        lang = language
        if lang is None and self.config.language != "auto":
            lang = self.config.language

        segments, info = self.model.transcribe(
            str(audio_path),
            beam_size=self.config.beam_size,
            vad_filter=self.config.vad_filter,
            language=lang,
        )

        full_text = ""
        segment_list = []
        for segment in segments:
            full_text += segment.text
            segment_list.append(
                SegmentInfo(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip(),
                )
            )

        return Transcript(
            text=full_text.strip(),
            segments=segment_list,
            language=info.language,
            duration=info.duration,
        )
