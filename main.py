import random
import socket
import webview
import uvicorn
from threading import Thread, Event
from server import app


def get_unused_port():
    """Get an unused port."""
    while True:
        port = random.randint(
            1024, 65535
        )  # Port range is generally between 1024 and 65535
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Try to bind the port to ensure it is not in use
            sock.bind(("localhost", port))
            sock.close()
            return port
        except OSError:
            pass  # If the port is in use, continue to try the next one


if __name__ == "__main__":
    stop_event = Event()  # Create a stop event
    port = get_unused_port()  # Get an unused port
    # port = 8000
    config = uvicorn.Config(app, host="localhost", port=port, lifespan="on")
    server = uvicorn.Server(config)

    # Start Uvicorn server in a separate thread
    uvicorn_thread = Thread(target=server.run)
    uvicorn_thread.start()

    # Create a webview window
    webview.create_window(
        "Ticket Bot",
        f"http://localhost:{port}/",
        resizable=True,
        width=1200,
        height=900,
    )

    webview.start()  # Start the webview window

    server.should_exit = True
    uvicorn_thread.join()  # Wait for the Uvicorn thread to finish
