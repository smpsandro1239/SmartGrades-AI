"""Entry point for SmartGrades-AI."""

from database.database import initialize_database
from interface.dashboard import Dashboard


def main() -> None:
    initialize_database()
    app = Dashboard()
    app.mainloop()


if __name__ == "__main__":
    main()
