import os
from collections import Counter
from functools import wraps
from flask import Blueprint, abort, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import func, text    # `text()` is used to execute raw SQL safely via SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm, AddBooks, EditUser
from ai_agent import ai_to_sql, generate_natural_answer, recommend_books, answers_from_web, insights_summary, analyze_reading_habits
from app_factory import db, User, Books, login_manager
import re


blueprint = Blueprint("blueprint", __name__)


# returns True if the question needs external web info, rather than the database
def web_answers(user_text: str) -> bool:
    lower_user_text = user_text.lower()
    keywords = [
        "price", "expensive", "cheapest", "cost", "worth", "value",
        "how much does", "how much is",
        "pages", "page count", "how many pages",
        "year published", "publication year", "release year",
        "summary", "synopsis", "plot",
        "rating", "goodreads", "amazon rating",
    ]

    return any(word in lower_user_text for word in keywords)


# computes summary metrics for one specific user
def compute_user_metrics(user_id: int) -> dict:
    if user_id is None:
        raise ValueError("user_id must not be None")

    user = User.query.get_or_404(user_id)
    books = Books.query.filter_by(user_id=user_id).all()

    statuses = Counter([book.reading_status for book in books])
    genres = Counter([book.genre for book in books])
    authors = Counter([book.author for book in books])

    total = len(books)
    completed = statuses.get("Completed", 0)
    reading = statuses.get("Reading", 0)
    completion_rate = (completed/total) if total else 0

    return {
        "scope": "user",
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "totals": {"books": total, "completed": completed, "reading": reading},
        "completion_rate": round(completion_rate * 100, 1),
        "top_genres": genres.most_common(5),
        "top_authors": authors.most_common(5),
    }


# computes metrics for the entire library (excluding admin accounts)
def compute_library_metrics() -> dict:
    total_users = db.session.query(User).filter(User.is_admin == False).count()
    total_books = (
        db.session.query(Books).join(User, Books.user_id == User.id)
        .filter(User.is_admin == False).count()
    )

    # Top user by book count
    top_user = (
        db.session.query(User, func.count(Books.id)).join(Books)
        .filter(User.is_admin == False).group_by(User.id)
        .order_by(func.count(Books.id).desc()).first()
    )

    # Top genre
    top_genre = (
        db.session.query(Books.genre, func.count(Books.id)).join(User, Books.user_id == User.id)
        .filter(User.is_admin == False).group_by(Books.genre)
        .order_by(func.count(Books.id).desc()).first()
    )

    # status breakdown and genre distribution
    all_books = (
        db.session.query(Books).join(User, Books.user_id == User.id)
        .filter(User.is_admin == False).all()
    )
    statuses = Counter([book.reading_status for book in all_books])
    genres = Counter([book.genre for book in all_books])

    return {
        "scope": "library",
        "totals": {"users": total_users, "books": total_books},
        "top_user": {"name": top_user[0].name, "count": int(top_user[1])} if top_user else None,
        "top_genre": {"genre": top_genre[0], "count": int(top_genre[1])} if top_genre else None,
        "status_breakdown": dict(statuses),
        "top_genres": genres.most_common(8),
    }


# route decorator: only allows authenticated admin users
def admin_only(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return abort(403)

        return func(*args, **kwargs)

    return decorated_function


# reloads the user from the session
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


# creates a new user and logs them in
@blueprint.route("/register", methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        email = register_form.email.data.strip().lower()

        existing_user = db.session.execute(db.select(User).where(User.email == register_form.email.data)).scalar()

        if existing_user:
            flash("You have already signed up with that email. Please log in instead.")
            return redirect(url_for("blueprint.login"))

        hashed_password = generate_password_hash(
            register_form.password.data,
            method="pbkdf2:sha256",
            salt_length=4
        )

        # assigns the admin when first registering
        admin_email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()

        new_user = User(
            name=register_form.name.data,
            email=register_form.email.data,
            password=hashed_password,
            is_admin=(admin_email != "" and email == admin_email),
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("blueprint.home"))
    return render_template("register.html", form=register_form, logged_in=current_user.is_authenticated)



# authenticates existing users
@blueprint.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == login_form.email.data)).scalar()
        password = login_form.password.data

        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for("blueprint.login"))
        elif not check_password_hash(user.password, password):
            flash("Incorrect password.")
            return redirect(url_for("blueprint.login"))
        else:
            login_user(user)

            return redirect(url_for("blueprint.home"))

    return render_template("login.html", form=login_form, logged_in=current_user.is_authenticated)



# logs out the current user
@blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("blueprint.login"))



# main landing page: Admins see admin dashboard, regular users see their book list
@blueprint.route("/")
@login_required
def home():
    # Admin Dashboard
    if current_user.is_admin:
        total_users = db.session.scalar(db.select(func.count(User.id)).where(User.is_admin == False))
        total_books = db.session.scalar(db.select(func.count(Books.id)).join(User).where(User.is_admin == False))

        top_user_row = db.session.execute(db.select(User, func.count(Books.id).label("book_count"))
                                          .join(Books, isouter=True).where(User.is_admin == False).group_by(User.id)
                                          .order_by(func.count(Books.id).desc()).limit(1)).first()

        top_genre_row = db.session.execute(db.select(Books.genre, func.count(Books.id).label("cnt")).join(User)
        .where(User.is_admin == False)
        .group_by(Books.genre).order_by(func.count(Books.id).desc()).limit(
            1)).first()

        return render_template("admin-dashboard.html", total_users=total_users,
                               total_books=total_books, top_user=top_user_row, top_genre=top_genre_row,
                               logged_in=current_user.is_authenticated)

    # User Dashboard
    books = current_user.books
    return render_template("home.html", all_books=books, logged_in=current_user.is_authenticated)



# manage users as an admin, lists users and their book counts (excluding admin users)
@blueprint.route("/admin/users")
@login_required
@admin_only
def manage_users():
    users = db.session.execute(db.select(User, func.count(Books.id).label("book_count"))
                               .join(Books, isouter=True).where(User.is_admin == False)
                               .group_by(User.id).order_by(User.name)).all()

    return render_template("manage-users.html", users=users, logged_in=current_user.is_authenticated)



# views one specific user's books as an admin
@blueprint.route("/admin/users/<int:user_id>/books")
@login_required
@admin_only
def view_books(user_id):
    user = db.get_or_404(User, user_id)

    if user.is_admin:
        abort(403)

    books = user.books

    return render_template("view-books.html", user=user, books=books,
                           logged_in=current_user.is_authenticated)



# views all books across non-admin users
@blueprint.route("/admin/books")
@login_required
@admin_only
def manage_books():
    books = db.session.execute(db.select(Books).join(User).where(User.is_admin == False)
                               .order_by(Books.title)).scalars().all()

    return render_template("manage-books.html", books=books,
                           logged_in=current_user.is_authenticated)



# user creates a new book in their library
@blueprint.route("/books/create", methods=["GET", "POST"])
@login_required
def add_book():
    addbook_form = AddBooks()
    if addbook_form.validate_on_submit():
        new_book = Books(
            title=addbook_form.title.data.strip().title(),
            author=addbook_form.author.data.title(),
            genre=addbook_form.genre.data.title(),
            reading_status=addbook_form.reading_status.data,
            user=current_user
        )

        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for("blueprint.home"))
    return render_template("add-books.html", form=addbook_form, is_edit=False, logged_in=current_user.is_authenticated)



# user edits an existing book
@blueprint.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
def edit_book(book_id):
    book = db.get_or_404(Books, book_id)
    edit_form = AddBooks(
        title=book.title,
        author=book.author,
        genre=book.genre,
        reading_status=book.reading_status
    )
    edit_form.submit.label.text = "Save"

    if edit_form.validate_on_submit():
        book.title = edit_form.title.data.strip().title()
        book.author = edit_form.author.data
        book.genre = edit_form.genre.data
        book.reading_status = edit_form.reading_status.data

        db.session.commit()
        return redirect(url_for("blueprint.home"))
    return render_template("add-books.html", form=edit_form, is_edit=True, logged_in=current_user.is_authenticated)



# user deletes a book
@blueprint.route("/books/<int:book_id>/delete", methods=["GET", "POST"])
@login_required
def delete_book(book_id):
    book_to_delete = db.get_or_404(Books, book_id)
    db.session.delete(book_to_delete)
    db.session.commit()
    return redirect(url_for("blueprint.home"))



"""
- can be used by both admins and users
- summarizes, analyzes reading habits
- recommends books
- handles questions that need web information
- generates read-only SQL and answers from database results
"""
@blueprint.route("/ai-chat", methods=["POST"])
@login_required
def ai_chat():
    data = request.get_json() or {}
    user_message = (data.get("message") or "").strip()
    lower_user_message = user_message.lower()

    if not user_message:
        return jsonify({"reply": "Please type something first."}), 400

    #                 ADMIN INSIGHTS
    if current_user.is_admin and (lower_user_message.startswith("/insights")
                                  or lower_user_message in ["insights", "library insights", "admin insights"]):
        parts = user_message.split()
        user_id = None
        if len(parts) >= 3 and parts[1].lower() == "user":
            try:
                user_id = int(parts[2])
            except ValueError:
                user_id = None

        if user_id is not None:
            metrics = compute_user_metrics(user_id)
        else:
            metrics = compute_library_metrics()

        summary = insights_summary(metrics)
        return jsonify({"reply": summary})

    #               BOOK RECOMMENDATIONS
    # checks for recommendations before habit analysis
    # keywords: recommend, suggest, recommendation, suggestions
    recommendation_keywords = ["recommend", "suggest", "recommendation", "suggestions"]
    is_recommendation_query = any(word in lower_user_message for word in recommendation_keywords)

    if is_recommendation_query and "book" in lower_user_message:
        # checks if admin is asking for another user
        target_user = None
        target_user_name = None

        if current_user.is_admin:
            # extracts user name from query
            # patterns: "recommend for [Name]", "add to [Name]'s library", "for user [Name]"

            # pattern 1: "for [Name]" or "to [Name]'s"
            match = re.search(r'\b(?:for|to)\s+([A-Z][a-z]+(?:\'s)?)', user_message)
            if match:
                potential_name = match.group(1).replace("'s", "").strip()
                # finds user by name
                target_user = User.query.filter(
                    User.name.ilike(potential_name),
                    User.is_admin == False
                ).first()

            # pattern 2: "user [Name]"
            if not target_user:
                match = re.search(r'\buser\s+([A-Z][a-z]+)', user_message, re.IGNORECASE)
                if match:
                    potential_name = match.group(1).strip()
                    target_user = User.query.filter(User.name.ilike(potential_name),
                                                    User.is_admin == False).first()

        # determines whose books to analyze
        if target_user:
            # admin asks for specific user
            user_books = [
                {
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre,
                    "reading_status": book.reading_status,
                }
                for book in target_user.books
            ]
            target_user_name = target_user.name
        else:
            # regular user asking for themselves or admin asking for themselves
            user_books = [
                {
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre,
                    "reading_status": book.reading_status,
                }
                for book in current_user.books
            ]
            target_user_name = current_user.name

        # checks if user has books to base recommendations on
        if not user_books:
            if current_user.is_admin and target_user:
                return jsonify({
                                   "reply": f"{target_user_name} doesn't have any books yet. Add some books to their library first to get recommendations."})
            else:
                return jsonify({
                                   "reply": "You don't have any books yet. Add some books to your library first so I can give you personalized recommendations!"})

        try:
            reply_text = recommend_books(requester_name=current_user.name,
                                         target_user_name=target_user_name,
                                         user_books=user_books,
                                         is_admin=current_user.is_admin)
        except Exception as e:
            print("Recommendation error:", repr(e))
            reply_text = ("I had trouble generating recommendations right now. Please try again in a moment.")

        return jsonify({"reply": reply_text})


    #             WEB SEARCH QUERIES
    # checks if a query requires web search before attempting SQL
    web_required = web_answers(user_message)

    # if web search is required goes directly to web search path
    if web_required:
        # gets all the books from the library
        if current_user.is_admin:
            all_books = db.session.execute(db.select(Books).join(User)
                                            .where(User.is_admin == False).order_by(Books.title)
                                            ).scalars().all()
            user_books = [
                {"title": book.title, "author": book.author, "genre": book.genre}
                for book in all_books
            ]
        else:
            user_books = [
                {"title": book.title, "author": book.author, "genre": book.genre}
                for book in current_user.books
            ]

        try:
            reply_text = answers_from_web(
                user_question=user_message, user_books=user_books,
                is_admin=current_user.is_admin
            )
        except Exception as e2:
            print("Web-answer error:", repr(e2))
            reply_text = "I tried looking this up on the internet, but something went wrong. Please try again later."

        return jsonify({"reply": reply_text})


    #                READING HABIT ANALYSIS
    # specific to avoid catching recommendation queries

    # checks for keyword that indicates wanting analysis/summary
    analysis_keywords = ["summarize", "summary", "summarise", "analyze", "analyse"]
    context_keywords = ["reading", "book", "library"]

    has_analysis_word = any(word in lower_user_message for word in analysis_keywords)
    has_context_word = any(word in lower_user_message for word in context_keywords)
    has_habit_word = "habit" in lower_user_message  # Catches both "habit" and "habits"

    # specific phrases that clearly indicate habit analysis, not recommendations
    habit_phrases = [
        "my reading habits",
        "reading habits",
        "reading patterns",
        "reading style",
        "how do i read",
        "what do i read",
        "analyze my reading",
        "summarize my reading"
    ]
    has_habit_phrase = any(phrase in lower_user_message for phrase in habit_phrases)

    # only trigger habit analysis if it's about habits/patterns
    is_habit_query = (
            (has_analysis_word and (has_context_word or has_habit_word)) or
            has_habit_phrase or
            has_habit_word
    )

    if is_habit_query:

        # checks if asking about a specific user (admin only)
        target_user = None
        target_user_name = None

        if current_user.is_admin:
            patterns = [
                r'\b([A-Z][a-z]+)(?:\'s?)\s+(?:reading|book|library)',
                r'(?:for|about)\s+([A-Z][a-z]+)',
                r'([A-Z][a-z]+)\s+(?:reading|book|library)',
            ]
            # finds user name in query
            for pattern in patterns:
                match = re.search(pattern, user_message)
                if match:
                    potential_name = match.group(1).replace("'s", "").replace("'", "").strip()
                    target_user = User.query.filter(User.name.ilike(potential_name),
                                                    User.is_admin == False).first()
                    if target_user:
                        break  # found a user, stop searching

        # determines whose habits to analyze
        if target_user:
            user_books = [
                {
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre,
                    "reading_status": book.reading_status,
                }
                for book in target_user.books
            ]
            target_user_name = target_user.name
        elif current_user.is_admin and not target_user and any(char.isupper() for char in user_message):
            # if admin asks about a user and the user is not found
            return jsonify({"reply": "I couldn't find that user. Please check the name and try again."})
        else:
            user_books = [
                {
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre,
                    "reading_status": book.reading_status,
                }
                for book in current_user.books
            ]
            target_user_name = current_user.name

        # checks if user has books
        if not user_books:
            if current_user.is_admin and target_user:
                return jsonify(
                    {"reply": f"{target_user_name} doesn't have any books yet. Add some books to their library first."})
            else:
                return jsonify({"reply": "You don't have any books yet. Add some books to your library first!"})

        try:
            reply_text = analyze_reading_habits(
                requester_name=current_user.name,
                target_user_name=target_user_name,
                user_books=user_books
            )
        except Exception as e:
            print("Reading habits analysis error:", repr(e))
            reply_text = "I had trouble analyzing reading habits. Please try again."

        return jsonify({"reply": reply_text})



    #                  SQL-BASED QUERIES
    sql_query = ai_to_sql(user_message, current_user.id, is_admin=current_user.is_admin)
    print("AI-generated SQL:", sql_query)

    # used so that non-admin users cannot have information about other users
    if not current_user.is_admin:
        lowered_sql_query = (sql_query or "").lower()
        if "from users" in lowered_sql_query or "join users" in lowered_sql_query:
            return jsonify({"reply": "You don't have permission."})

        if any(message in lower_user_message for message in
               ["list all users", "show all users", "who are the users", "all users"]):
            return jsonify({"reply": "You don't have permission."})

    # block operations
    forbidden = ["update", "delete", "insert", "alter", "drop", "truncate", "create"]
    if any(word in sql_query.lower() for word in forbidden):
        return jsonify({"reply": "I only support read-only questions. I can't modify data."})

    # executes sql
    try:
        result = db.session.execute(text(sql_query)).fetchall()
    except Exception as e:
        print("SQL/AI error:", repr(e))
        return jsonify({"reply": "I couldn't understand that question. Try rephrasing it."})

    # convert rows to dictionaries
    rows = [dict(row._mapping) for row in result]

    # generates natural language answer
    try:
        reply_text = generate_natural_answer(
            user_question=user_message,
            sql_query=sql_query,
            rows=rows,
            user_name=current_user.name,
            is_admin=current_user.is_admin,
        )
    except Exception as e:
        print("Answer generation error:", repr(e))
        if not rows:
            reply_text = "I couldn't find any matching records."
        else:
            sample = rows[0]
            if {"title", "author", "genre", "reading_status"} <= set(sample.keys()):
                lines = [
                    f"- {row['title']} by {row['author']} ({row['genre']}, {row['reading_status']})"
                    for row in rows
                ]
                reply_text = "Here's what I found:\n" + "\n".join(lines)
            else:
                lines = []
                for row in rows:
                    parts = [f"{k}: {v}" for k, v in row.items()]
                    lines.append("- " + ", ".join(parts))
                reply_text = "Here are the results:\n" + "\n".join(lines)

    return jsonify({"reply": reply_text})



# shows insights for whole library or a selected user
@blueprint.route("/admin/insights")
@login_required
@admin_only
def admin_insights():
    user_id = request.args.get("user_id", type=int)
    users = User.query.filter(User.is_admin == False).order_by(User.name.asc()).all()

    if user_id:
        metrics = compute_user_metrics(user_id)
    else:
        metrics = compute_library_metrics()

    summary = insights_summary(metrics)

    return render_template("admin-insights.html", metrics=metrics,
                           summary=summary,users=users,selected_user_id=user_id
                           , logged_in=current_user.is_authenticated)



# admin edits a user
@blueprint.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_only
def admin_edit_user(user_id):
    user = db.get_or_404(User, user_id)

    if user.is_admin:
        abort(403)

    form = EditUser(obj=user)
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data

        # only updates the password if admin typed one
        if form.password.data:
            user.password = generate_password_hash(form.password.data)

        db.session.commit()
        return redirect(url_for("blueprint.manage_users"))

    return render_template("edit-users.html", form=form, user=user,
                           logged_in=current_user.is_authenticated)



# admin adds a book to a specific user's library
@blueprint.route("/admin/users/<int:user_id>/books/add", methods=["GET", "POST"])
@login_required
@admin_only
def admin_add_book(user_id):
    user = db.get_or_404(User, user_id)

    if user.is_admin:
        abort(403)

    form = AddBooks()
    if form.validate_on_submit():
        new_book = Books(
            title=form.title.data.title().strip().title(),
            author=form.author.data.title(),
            genre=form.genre.data.title(),
            reading_status=form.reading_status.data,
            user=user
        )

        db.session.add(new_book)
        db.session.commit()

        return redirect(url_for("blueprint.view_books", user_id=user.id))
    return render_template("add-books.html", form=form, is_edit=False,
                           logged_in=current_user.is_authenticated, admin_target_user=user)



# admin deletes a user
@blueprint.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_only
def admin_delete_user(user_id):
    user = db.get_or_404(User, user_id)

    if user.is_admin:
        abort(403)    # can't delete admin users

    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("blueprint.manage_users"))
