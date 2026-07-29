"""Deterministic demo catalog seed data."""

from musicbloom.models.catalog import (
    AccentTheme,
    Album,
    Artist,
    AudioSource,
    Track,
    TrackArtwork,
    TrackMood,
)


def _theme(primary: str, secondary: str, background: str) -> AccentTheme:
    return AccentTheme(
        primary=primary,
        secondary=secondary,
        background=background,
    )


DEMO_ARTISTS: tuple[Artist, ...] = (
    Artist(id="artist-petal-pine", name="Petal & Pine", genre="acoustic garden"),
    Artist(id="artist-luna-sprout", name="Luna Sprout", genre="indie bloom"),
    Artist(id="artist-terrarium-trio", name="The Terrarium Trio", genre="folk moss"),
    Artist(
        id="artist-bloombud-ensemble",
        name="BloomBud Ensemble",
        genre="chiptune petals",
    ),
    Artist(
        id="artist-nightshade-nectar",
        name="Nightshade Nectar",
        genre="ambient dusk",
    ),
    Artist(id="artist-raindrop-rondo", name="Raindrop Rondo", genre="classical rain"),
    Artist(id="artist-verdant-vale", name="Verdant Vale", genre="brass garden"),
)

DEMO_ALBUMS: tuple[Album, ...] = (
    Album(
        id="album-greenhouse-echoes",
        title="Greenhouse Echoes",
        artist_id="artist-petal-pine",
        artist_name="Petal & Pine",
        artwork=TrackArtwork(
            local_path="/static/demo/artwork/greenhouse-echoes.png",
        ),
        genre="acoustic garden",
    ),
    Album(
        id="album-cloud-garden",
        title="Cloud Garden",
        artist_id="artist-luna-sprout",
        artist_name="Luna Sprout",
        artwork=TrackArtwork(
            local_path="/static/demo/artwork/cloud-garden.png",
        ),
        genre="indie bloom",
    ),
    Album(
        id="album-understory",
        title="Understory",
        artist_id="artist-terrarium-trio",
        artist_name="The Terrarium Trio",
        artwork=TrackArtwork(
            url="https://demo.musicbloom.local/artwork/understory.png",
        ),
        genre="folk moss",
    ),
    Album(
        id="album-playground-petals",
        title="Playground Petals",
        artist_id="artist-bloombud-ensemble",
        artist_name="BloomBud Ensemble",
        artwork=TrackArtwork(
            local_path="/static/demo/artwork/playground-petals.png",
        ),
        genre="chiptune petals",
    ),
    Album(
        id="album-moonlit-mulch",
        title="Moonlit Mulch",
        artist_id="artist-nightshade-nectar",
        artist_name="Nightshade Nectar",
        artwork=TrackArtwork(
            local_path="/static/demo/artwork/moonlit-mulch.png",
        ),
        genre="ambient dusk",
    ),
    Album(
        id="album-april-showers",
        title="April Showers Suite",
        artist_id="artist-raindrop-rondo",
        artist_name="Raindrop Rondo",
        artwork=TrackArtwork(
            url="https://demo.musicbloom.local/artwork/april-showers.png",
        ),
        genre="classical rain",
    ),
    Album(
        id="album-botanical-beats",
        title="Botanical Beats",
        artist_id="artist-verdant-vale",
        artist_name="Verdant Vale",
        artwork=TrackArtwork(
            local_path="/static/demo/artwork/botanical-beats.png",
        ),
        genre="brass garden",
    ),
)

DEMO_TRACKS: tuple[Track, ...] = (
    Track(
        id="demo-track-001",
        title="Morning Dew Waltz",
        artist_id="artist-petal-pine",
        artist_name="Petal & Pine",
        album_id="album-greenhouse-echoes",
        album_title="Greenhouse Echoes",
        duration_ms=184_000,
        artwork=TrackArtwork(
            local_path="/static/demo/artwork/morning-dew-waltz.png",
        ),
        audio=AudioSource(
            local_path="/static/demo/audio/morning-dew-waltz.wav",
        ),
        mood=TrackMood.CALM,
        genre="acoustic garden",
        accent_theme=_theme("#7BC47F", "#F4E1A1", "#F7FBF4"),
        playable_in_demo_mode=True,
    ),
    Track(
        id="demo-track-002",
        title="Sunbeam Carousel",
        artist_id="artist-luna-sprout",
        artist_name="Luna Sprout",
        album_id="album-cloud-garden",
        album_title="Cloud Garden",
        duration_ms=210_500,
        artwork=TrackArtwork(
            url="https://demo.musicbloom.local/artwork/sunbeam-carousel.png",
        ),
        audio=AudioSource(
            url="https://demo.musicbloom.local/audio/sunbeam-carousel.ogg",
        ),
        mood=TrackMood.PLAYFUL,
        genre="indie bloom",
        accent_theme=_theme("#FFB347", "#FFE29A", "#FFF8EE"),
        playable_in_demo_mode=True,
    ),
    Track(
        id="demo-track-003",
        title="Mossy Footsteps",
        artist_id="artist-terrarium-trio",
        artist_name="The Terrarium Trio",
        album_id="album-understory",
        album_title="Understory",
        duration_ms=245_000,
        artwork=TrackArtwork(
            url="https://demo.musicbloom.local/artwork/mossy-footsteps.png",
        ),
        audio=AudioSource(
            local_path="/static/demo/audio/mossy-footsteps.wav",
        ),
        mood=TrackMood.COZY,
        genre="folk moss",
        accent_theme=_theme("#6B8F71", "#C8D5B9", "#F1F5EF"),
        playable_in_demo_mode=True,
    ),
    Track(
        id="demo-track-004",
        title="Bubblegum Breeze",
        artist_id="artist-bloombud-ensemble",
        artist_name="BloomBud Ensemble",
        album_id="album-playground-petals",
        album_title="Playground Petals",
        duration_ms=198_000,
        artwork=TrackArtwork(
            local_path="/static/demo/artwork/bubblegum-breeze.png",
        ),
        audio=AudioSource(
            local_path="/static/demo/audio/bubblegum-breeze.wav",
        ),
        mood=TrackMood.ENERGETIC,
        genre="chiptune petals",
        accent_theme=_theme("#FF6B9D", "#FFD166", "#FFF0F6"),
        playable_in_demo_mode=True,
    ),
    Track(
        id="demo-track-005",
        title="Starlit Sprinkler",
        artist_id="artist-nightshade-nectar",
        artist_name="Nightshade Nectar",
        album_id="album-moonlit-mulch",
        album_title="Moonlit Mulch",
        duration_ms=267_000,
        artwork=TrackArtwork(
            local_path="/static/demo/artwork/starlit-sprinkler.png",
        ),
        audio=AudioSource(
            local_path="/static/demo/audio/starlit-sprinkler.wav",
        ),
        mood=TrackMood.DREAMY,
        genre="ambient dusk",
        accent_theme=_theme("#6C63FF", "#B8B5FF", "#F0EFFF"),
        playable_in_demo_mode=True,
    ),
    Track(
        id="demo-track-006",
        title="Puddle Reflections",
        artist_id="artist-raindrop-rondo",
        artist_name="Raindrop Rondo",
        album_id="album-april-showers",
        album_title="April Showers Suite",
        duration_ms=223_000,
        artwork=TrackArtwork(
            url="https://demo.musicbloom.local/artwork/puddle-reflections.png",
        ),
        audio=AudioSource(
            url="https://demo.musicbloom.local/audio/puddle-reflections.ogg",
        ),
        mood=TrackMood.CALM,
        genre="classical rain",
        accent_theme=_theme("#4DA6FF", "#A8D8FF", "#EEF7FF"),
        playable_in_demo_mode=True,
    ),
    Track(
        id="demo-track-007",
        title="Fern Fanfare",
        artist_id="artist-verdant-vale",
        artist_name="Verdant Vale",
        album_id="album-botanical-beats",
        album_title="Botanical Beats",
        duration_ms=156_000,
        artwork=TrackArtwork(
            local_path="/static/demo/artwork/fern-fanfare.png",
        ),
        audio=AudioSource(
            local_path="/static/demo/audio/fern-fanfare.wav",
        ),
        mood=TrackMood.ENERGETIC,
        genre="brass garden",
        accent_theme=_theme("#2E8B57", "#F9C74F", "#F4FFF7"),
        playable_in_demo_mode=True,
    ),
    Track(
        id="demo-track-008",
        title="Glasshouse Ghostlight",
        artist_id="artist-nightshade-nectar",
        artist_name="Nightshade Nectar",
        album_id="album-moonlit-mulch",
        album_title="Moonlit Mulch",
        duration_ms=301_000,
        artwork=TrackArtwork(
            local_path="/static/demo/artwork/glasshouse-ghostlight.png",
        ),
        audio=AudioSource(
            url="https://demo.musicbloom.local/audio/glasshouse-ghostlight-preview.ogg",
        ),
        mood=TrackMood.MYSTERIOUS,
        genre="ambient dusk",
        accent_theme=_theme("#3D348B", "#7678ED", "#ECEAFF"),
        playable_in_demo_mode=False,
    ),
)
