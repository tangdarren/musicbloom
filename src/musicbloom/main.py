"""Entry point for running the MusicBloom API with uvicorn."""

import uvicorn


def main() -> None:
    """Start the development server."""
    uvicorn.run(
        "musicbloom.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
