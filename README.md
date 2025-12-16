# Library Management System
AI-powered personal library management system with natural language querying capabilities powered by OpenAI GPT-4o.

## 🚀 Features

## Core Features

* **User Authentication** - Secure registration and login with password hashing
* **Book Management** - Full CRUD operations (Create, Read, Update, Delete)
* **Genre Organization** - Categorize books by genre
* **Reading Status Tracking** - Track books as "Reading", "Completed", or "To Read"
* **Admin Dashboard** - Manage all users and their book collections
* **Environment-Based Admin Setup** - Admin privileges assigned via environment variable during registration

## AI-Powered Features

* **Natural Language Queries** - Ask questions like "Who owns the most books?" or "What's my most read genre?"
* **AI Chatbot Interface** - Floating chat widget for instant library insights
* **Reading Insights Dashboard** - Automated analysis of reading habits and patterns
* **Book Recommendations** - AI-generated reading suggestions based on your library
* **Web Search Integration** - Get answers about books beyond your library using DuckDuckGo like "Summary of what a book is about."

## 🛠️ Tech Stack

* **Backend**: Flask (Python 3.11+)
* **Database**: PostgreSQL (Production) / SQLite (Development) with SQLAlchemy ORM
* **Frontend**: Bootstrap 5, Jinja2 templates
* **AI/LLM**: OpenAI GPT-4o via LangChain
* **Forms**: Flask-WTF with CSRF protection
* **Authentication**: Flask-Login
* **Search**: DuckDuckGo Search
* **Testing**: pytest
* **Deployment**: Render

## 📋 Prerequisites

* Python 3.11 or higher
* pip (Python package manager)
* OpenAI API key [(Get one here)](https://platform.openai.com/api-keys)
* PostgreSQL (for production deployment)


## 🔧 Installation
1. Clone the repository

`bashgit clone <your-repo-url>`

`cd library-management-system`

2. Create virtual environment

`bashpython -m venv venv`

`# Activate virtual environment`

`# On Windows:`

`venv\Scripts\activate`

`# On macOS/Linux:`

`source venv/bin/activate`

3. Install dependencies

`bashpip install -r requirements.txt`

4. Set up environment variables
Create a .env file in the project root with the following:

```env
OPENAI_API_KEY=your_openai_api_key_here
FLASK_SECRET_KEY=your_random_secret_key_here
DB_URI=sqlite:///users.db  # For local development
ADMIN_EMAIL=your_email@example.com  # Optional: Set admin on first registration
```

Note: Get your OpenAI API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

5. Run the application

```bash
python main.py
```

The app will be available at [http://localhost:5000](http://localhost:5000)



## 🚀 Deployment (Render)

1. **Create a Render account** at [render.com](https://render.com)

2. **Create a PostgreSQL database**:
   - Go to Dashboard → New → PostgreSQL
   - Copy the Internal Database URL

3. **Create a Web Service**:
   - Connect your GitHub repository
   - Set environment variables:
```
     OPENAI_API_KEY=your_key
     FLASK_SECRET_KEY=your_secret
     DB_URI=your_postgres_internal_url
     ADMIN_EMAIL=admin@example.com
```

4. **Deploy**:
   - Render will auto-deploy on every push to your main branch

5. **Create Admin User**:
   - Register an account using the email set in `ADMIN_EMAIL`
   - The system will automatically grant admin privileges on registration


## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit_tests.py
pytest tests/integration_tests.py
```

## 📱 Usage
**First Time Setup**

1. Navigate to [http://localhost:5000](http://localhost:5000)
2. Click **Register** to create an account
3. Log in with your credentials
4. Start adding books to your library!

**Regular User Features**

* **Add Books**: Click "Add new book" to add titles to your library
* **Edit Books**: Modify book details, change reading status
* **Delete Books**: Remove books from your collection
* **AI Chatbot**: Click the 🤖 icon to ask questions about your library

**AI Chatbot Examples**
**Try asking:**

(As a User)
* "How many books do I have?"
* "What's my most read genre?"
* "Show me all my completed books"
* "Which books am I reading right now?"
* "Recommend me new books based on my reading history"
* "Summarize my reading habits"
* "Give me a summary of what [any book title] is about"  (uses web search)

(As an admin)
* "What books do you recommend me adding to [a user's name] library, based on his book history?"
* "Who owns the most books?"
* "Which is the most popular book?"
* "Show me the prices of [a user's name] books"
* "Summarize [user name] reading habits"


**Admin Features**

Admin users have additional capabilities:

* **Manage Users**: View, edit, and delete user accounts
* **View All Libraries**: Access any user's book collection
* **Manage All Books**: Edit or delete books from any user's library
* **Insights Dashboard**: View library-wide analytics and reading patterns
* **Add Books for Users**: Add books directly to any user's library


**Creating an Admin User**: 
Set the `ADMIN_EMAIL` environment variable to the email address you want to be admin. When that user registers, they'll automatically receive admin privileges.

## 🎯 AI Capabilities

The system leverages OpenAI GPT-4o through LangChain for advanced natural language processing:

1. **Text-to-SQL Translation**
Converts natural language questions into executable SQL queries with PostgreSQL support:
   * "**Who has the most books?**" → `SELECT user_id, COUNT(*) FROM books GROUP BY user_id ORDER BY COUNT(*) DESC LIMIT 1`
   * Supports boolean columns with proper TRUE/FALSE syntax
   * Case-insensitive title matching with automatic whitespace trimming

2. **Natural Language Responses**
Formats query results into human-readable answers with context

3. **Reading Insights Analysis**
Generates comprehensive summaries of reading habits:
   * Most read genres
   * Reading completion rates
   * Reading patterns and trends

4. **Book Recommendations**
Analyzes your reading history to suggest new books based on:
   * Preferred genres
   * Favorite authors
   * Reading patterns

5. **Web-Enhanced Search**
Combines your library data with external sources:
   * DuckDuckGo for general web search
   * Provides context-aware answers

## 📁 Project Structure
library-management-system/
* ├── app_factory.py          `# Flask app initialization, database models`
* ├── routes.py                `# All route handlers and blueprints`
* ├── forms.py                `# WTForms for validation`
* ├── ai_agent.py             `# AI query processing and LLM integration`
* ├── prompt.py               `# System prompts for AI models`
* ├── main.py                 `# Application entry point`
* ├── .env                    `# Environment variables `
* ├── requirements.txt        `# Python dependencies`
* ├── templates/              `# Jinja2 HTML templates`
* │   ├── header.html         `# Navigation and chatbot widget`
* │   ├── footer.html         `# Footer with social links`
* │   ├── home.html           `# User's book library`
* │   ├── login.html          `# Login page`
* │   ├── register.html       `# Registration page`
* │   ├── add-books.html      `# Add new book form`
* │   ├── view-books.html     `# Views books `
* │   ├── manage-users.html   `# Admin user management`
* │   ├── manage-books.html   `# Admin view of user's books`
* │   ├── admin-insights.html `# Reading insights dashboard`
* │   ├── admin-dashboard.html `# Admin homepage `
* │   └── edit-users.html     `# Admin edit user form`
* ├── static/
* │   ├── css/
* │   │   ├── styles.css      `# Main styles`
* │   │   └── chatbot.css     `# Chatbot widget styles`
* │   ├── js/
* │       ├── scripts.js      `# Navigation scripts`
* │       └── chatbot-scripts.js  `# Chatbot functionality`
* │   
* │       
* └── tests/
*       ├── conftest.py     # pytest configuration and fixtures
*       ├── unit_test.py     # Unit tests for AI functions
*       └── integration_tests.py  # Integration tests for routes



## 🔒 Security Features

* **Password Hashing**: Uses Werkzeug for secure password storage
* **CSRF Protection**: All forms protected against Cross-Site Request Forgery
* **SQL Injection Prevention**: SQLAlchemy ORM + query sanitization
* **Session Management**: Secure session handling with Flask-Login
* **Admin-Only Routes**: Decorator-based access control for admin features
* **Environment Variables**: API keys and secrets stored securely in .env file
* **Database URI Configuration**: Supports both local SQLite and production PostgreSQL


## 🐛 Known Limitations

* No pagination on book lists (could be slow with 1000+ books)
* No rate limiting on AI chat endpoint
* AI queries count toward OpenAI API usage/costs
* Free tier deployment may have cold starts (first request takes 30-60 seconds)

## 🔮 Future Enhancements
Potential improvements for production:

1. [x] PostgreSQL database for multi-user support
2. [x] Environment-based admin configuration
3. [ ] Pagination for large book collections
4. [ ] Rate limiting on AI endpoints
5. [ ] Book cover image uploads
6. [ ] Reading statistics visualizations (charts/graphs)
7. [ ] Social features (share libraries, reviews)
8. [ ] Email notifications
9. [ ] Mobile responsive design improvements
10. [ ] Dark mode support
11. [ ] Advanced search and filtering
12. [ ] Reading goals and challenges


## 📊 Testing Coverage
The project includes comprehensive tests:

**Unit Tests**
* SQL query sanitization
* Table name normalization
* Reading status comparison handling
* Boolean column handling

**Integration Tests**
* User authentication flows
* Admin access control
* AI chat endpoint functionality
* Protected route authorization

Run tests with coverage report:
```bash
pytest --cov=. --cov-report=html
```



## 🔧 Technical Improvements

* **PostgreSQL Support**: Proper boolean column handling with TRUE/FALSE
* **Case-Insensitive Queries**: Book titles matched regardless of capitalization
* **Whitespace Normalization**: Automatic trimming of book titles to prevent duplicates
* **Environment-Based Configuration**: Database URI and admin email configurable via environment
* **Temperature Optimization**: AI responses set to temperature=0 for factual accuracy



## 👤 Author
**Marin Sauku**

**GitHub**: [@MarinSauku23](https://github.com/MarinSauku23)

**Instagram**: [@marin_sauku](https://www.instagram.com/marin_sauku/)

**TikTok**: [@pini.s](https://www.tiktok.com/@pini.s)

## 🙏 Acknowledgments

* Built for Ritech as an internship application
* Powered by OpenAI GPT-4o via LangChain framework
* UI components from Bootstrap 5
* Icons from Font Awesome
* Search capabilities from DuckDuckGo
* Deployed on Render


## 🌐 Live Demo

**[View Live Application](https://llm-library-management-system.onrender.com)**

Test Account:
- Email: test@example.com
- Password: test123

*Note: Please be respectful with the demo account. The AI chatbot uses OpenAI API which has usage costs.*
_The database currently has three other users and one admin_

Developed with ❤️ for Ritech International AG
Project Duration: 14 days | December 2025