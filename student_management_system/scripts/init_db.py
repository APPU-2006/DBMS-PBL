import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.extensions import db


def main():
    app = create_app()
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            db.create_all()
        except SQLAlchemyError as error:
            app.logger.error("Could not initialize MySQL database: %s", error.__class__.__name__)
            print(
                "Database initialization failed. Start MySQL and verify DATABASE_URL in .env."
            )
            raise SystemExit(1) from error
        print("Database connection verified; missing tables were created.")
        print("Existing tables and records were not dropped or cleared.")


if __name__ == "__main__":
    main()
