"""Entry point for SmartGrades-AI."""

from interface.dashboard import Dashboard


def main() -> None:
    app = Dashboard()
    app.mainloop()


if __name__ == "__main__":
    main()
