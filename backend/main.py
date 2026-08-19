import argparse

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="CodeQuery Backend Daemon")
    parser.add_argument("--port", type=int, default=8765, help="Port to run server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address")
    parser.add_argument(
        "--workspace", type=str, default=None, help="Initial workspace directory"
    )
    args = parser.parse_args()

    uvicorn.run("backend.app:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
