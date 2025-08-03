def main():
    """Run the application using uvicorn."""
    import uvicorn

    from solar_analyzer.config import settings
    from solar_analyzer.main import app

    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    main()
