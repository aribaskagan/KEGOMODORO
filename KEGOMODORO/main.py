"""KEGOMODORO entry point."""

from kegomodoro.app import KegomodoroApp


def main() -> None:
    app = KegomodoroApp()
    app.run()


if __name__ == "__main__":
    main()
