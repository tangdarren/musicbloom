"""Unit tests for catalog domain models."""

import pytest
from pydantic import ValidationError

from musicbloom.models.catalog import AudioSource, TrackArtwork


def test_audio_source_requires_url_or_local_path() -> None:
    with pytest.raises(ValidationError):
        AudioSource()


def test_track_artwork_requires_url_or_local_path() -> None:
    with pytest.raises(ValidationError):
        TrackArtwork()


def test_audio_source_accepts_local_path() -> None:
    source = AudioSource(local_path="/static/demo/audio/example.ogg")
    assert source.local_path == "/static/demo/audio/example.ogg"


def test_track_artwork_accepts_url() -> None:
    artwork = TrackArtwork(url="https://demo.musicbloom.local/artwork/example.png")
    assert artwork.url == "https://demo.musicbloom.local/artwork/example.png"
