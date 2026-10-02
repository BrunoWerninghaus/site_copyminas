import os

from dotenv import load_dotenv

from src.copyminas import create_app

load_dotenv()

app = create_app()


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))

    app.run(host=host, port=port, debug=debug)
