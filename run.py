import os

from api_service import create_app


app = create_app()


if __name__ == "__main__":
    app.run()