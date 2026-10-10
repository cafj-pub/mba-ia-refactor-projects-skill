from src.app import create_app
from src.config.settings import Settings

settings = Settings()
app = create_app(settings)

if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
