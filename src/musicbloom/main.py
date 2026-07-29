"""Entry point for running the MusicBloom API with uvicorn."""

import uvicorn

from musicbloom.dependencies import get_settings


def main() -> None:
    """Start the development server."""
    settings = get_settings()
    uvicorn.run(
        "musicbloom.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
