import os
import tempfile
import pytest
from werkzeug.security import generate_password_hash
from app_factory import create_app, db, User, Books


@pytest.fixture
def client():
    # creates a temporary DB file path for each test run
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd) # closes the OS-level file descriptor; SQLite will open it itself

    app = create_app({
        "TESTING": True,             # enables Flask testing mode
        "WTF_CSRF_ENABLED": False,   # disable CSRF for form posts in tests
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_path,
    })

    # safety check that ensures tests never touch the real database
    assert "users.db" not in app.config["SQLALCHEMY_DATABASE_URI"]

    with app.app_context():
        db.drop_all()
        db.create_all()

        # creates an admin user
        admin = User(
            name="Admin",
            email="admin@test.com",
            password=generate_password_hash("adminpass"),
            is_admin=True,
        )

        # creates a user
        user = User(
            name="User",
            email="user@test.com",
            password=generate_password_hash("userpass"),
            is_admin=False,
        )

        db.session.add_all([admin, user])
        db.session.commit()

        # adds books to the user
        books = [
            Books(user_id=user.id, title="The Shining", author="Stephen King", genre="Horror",
                  reading_status="Completed"),
            Books(user_id=user.id, title="Harry Potter", author="J. K. Rowling", genre="Fantasy",
                  reading_status="Reading"),
        ]

        db.session.add_all(books)
        db.session.commit()


    # provides the Flask test client to the test
    with app.test_client() as client:
        yield client

    # closes DB connections and deletes temp files
    with app.app_context():
        db.session.remove()
        db.engine.dispose()

    os.unlink(db_path)

# helper to log a user in through the real /login route
def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password},
                       follow_redirects=True,)