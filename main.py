import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000)) # Get port from env variable, default to 5000
    app.run(host="0.0.0.0", port=port)