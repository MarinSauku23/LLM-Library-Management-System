from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean
from dotenv import load_dotenv
import os

load_dotenv()



class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # One user can have multiple books
    books: Mapped[list["Books"]] = relationship("Books", back_populates="user", cascade="all, delete-orphan")


class Books(db.Model):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"), nullable=False)
    author: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    genre: Mapped[str] = mapped_column(String(100), nullable=False)
    reading_status: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="books")



def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI", "sqlite:///users.db")

    if test_config:
        app.config.update(test_config)

    Bootstrap5(app)
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "blueprint.login"

    # register routes with the blueprint endpoint
    from routes import blueprint
    app.register_blueprint(blueprint)

    with app.app_context():
        db.create_all()

    # Assigns the admin
    # with app.app_context():
    #     admin = User.query.filter_by(email="pini.sauku@gmail.com").first()
    #     admin.is_admin = True
    #     db.session.commit()

    return app



