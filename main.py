import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Read PORT from environment variable, default to 10000
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting server on http://0.0.0.0:{port}")
    # Enable debug=True if you want auto reload
    app.run(host="0.0.0.0", port=port, debug=True)
