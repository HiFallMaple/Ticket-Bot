import random
import socket
import multiprocessing
import webview
import uvicorn
from server import app


def get_unused_port():
    """Get an unused port."""
    while True:
        port = random.randint(1024, 65535)  # Port range is generally between 1024 and 65535
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Try to bind the port to ensure it is not in use
            sock.bind(("localhost", port))
            sock.close()
            return port
        except OSError:
            pass  # If the port is in use, continue to try the next one


def start_uvicorn_server(port):
    """Start the FastAPI server."""
    uvicorn.run(app, host="localhost", port=port)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    port = get_unused_port()  # Get an unused port
    # start_uvicorn_server(port)
    # Start Uvicorn server in a separate process
    uvicorn_process = multiprocessing.Process(target=start_uvicorn_server, args=(port,))
    uvicorn_process.start()

    # Create a webview window
    webview.create_window(
        "Ticket Bot",
        f"http://localhost:{port}/",
        resizable=True,
        width=1200,
        height=800,
    )

    webview.start(gui='edgechromium')  # Start the webview

    # Terminate the Uvicorn server process after webview is closed
    uvicorn_process.terminate()
    uvicorn_process.join()
