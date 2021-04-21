import os

from api_service import create_app

config_mode = os.environ.get('APP_MODE')
app = create_app(config_mode=config_mode)


if __name__ == "__main__":
    app.run()