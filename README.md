# Votez Backend

A FastAPI-based backend application for a polling/voting platform with real-time updates via WebSockets.

## Features

- User authentication and authorization (JWT-based)
- Create, read, update, and manage polls
- Real-time voting and poll updates via WebSockets
- Like functionality for polls
- PostgreSQL database with SQLAlchemy
- Async/await architecture for high performance
- RESTful API with FastAPI pagination

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL (async via SQLAlchemy)
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose)
- **Real-time**: WebSockets
- **Package Management**: pip

## Prerequisites

- Python 3.9 or higher
- PostgreSQL database
- pip or poetry for dependency management

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd "Votez Backend"
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory (you can copy from `sample-env.env`):

```bash
cp sample-env.env .env
```

Edit `.env` with your configuration:

```env
# Environment Configuration
ENVIRONMENT=local

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# Server Configuration
SERVER_NAME=localhost
SERVER_HOST=http://localhost:8000
SERVER_ADDRESS=0.0.0.0
SERVER_PORT=8000

# CORS Origins (JSON array format)
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# Frontend
FRONTEND_URL=http://localhost:3000

# PostgreSQL Database
POSTGRES_SERVER=localhost
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=votez
POSTGRES_POOL_SIZE=50
POSTGRES_MAX_OVERFLOW=0

# Cookie Configuration
COOKIE_KEY=cookie?

# Development Settings
WATCH_FILES=true
```

### 5. Set Up PostgreSQL Database

#### Option A: Using Docker

```bash
docker run --name votez-postgres \
  -e POSTGRES_USER=db \
  -e POSTGRES_PASSWORD=db \
  -e POSTGRES_DB=votez \
  -p 5432:5432 \
  -d postgres:15
```

#### Option B: Local PostgreSQL

Create a database named `votez`:

```bash
createdb votez
# or using psql:
psql -U postgres
CREATE DATABASE votez;
```

### 6. Run Database Migrations

```bash
alembic upgrade head
```

### 7. Start the Development Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

API Documentation (Swagger UI): `http://localhost:8000/docs`
Alternative Documentation (ReDoc): `http://localhost:8000/redoc`

## Project Structure

```
Votez Backend/
├── alembic/              # Database migrations
│   ├── versions/          # Migration files
│   └── env.py           # Alembic configuration
├── api/                  # API routes
│   ├── auth_api.py      # Authentication endpoints
│   ├── poll_api.py      # Poll CRUD endpoints
│   ├── websocket_api.py # WebSocket handlers
│   └── api.py           # Router aggregation
├── core/                 # Core functionality
│   ├── async_engine.py  # Database async engine
│   ├── auth.py          # Authentication utilities
│   ├── base.py          # Base models
│   ├── connection_manager.py # WebSocket connection management
│   ├── depends.py       # FastAPI dependencies
│   └── settings.py      # Configuration settings
├── crud/                 # Database operations
│   ├── like_crud.py
│   ├── poll_crud.py
│   ├── poll_option_crud.py
│   ├── user_crud.py
│   └── vote_crud.py
├── models/               # SQLAlchemy models
│   ├── like_model.py
│   ├── poll_model.py
│   ├── poll_options_model.py
│   ├── user_model.py
│   └── vote_model.py
├── schemas/              # Pydantic schemas
│   ├── poll_schema.py
│   └── user_schema.py
├── alembic.ini          # Alembic configuration
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── sample-env.env      # Environment template
├── render.yaml          # Render deployment configuration
├── runtime.txt          # Python version for deployment
└── Procfile             # Process file for Heroku/Render
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user information

### Polls
- `GET /polls` - List polls (paginated)
- `POST /polls` - Create a new poll
- `GET /polls/{poll_uuid}` - Get poll details
- `PATCH /polls/{poll_uuid}` - Update poll
- `DELETE /polls/{poll_uuid}` - Delete poll
- `POST /polls/{poll_uuid}/vote` - Vote on a poll option
- `POST /polls/{poll_uuid}/like` - Like a poll
- `DELETE /polls/{poll_uuid}/like` - Unlike a poll

### WebSocket
- `WS /ws/poll/{poll_uuid}` - Real-time updates for a poll

## Database Migrations

### Create a New Migration

```bash
alembic revision --autogenerate -m "description of changes"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1
```

## Development Guidelines

1. **Code Style**: Follow PEP 8 Python style guide
2. **Type Hints**: Use type hints for better code documentation
3. **Error Handling**: Use try-except blocks with proper error messages
4. **Async**: Use async/await for all database operations
5. **Environment Variables**: Never commit sensitive data, use environment variables

## Deployment to Render

The project includes a `render.yaml` file for easy deployment to [Render](https://render.com), a modern cloud hosting platform.

### Prerequisites
- Git repository (GitHub/GitLab/Bitbucket)
- Render account at [render.com](https://render.com)

### Method 1: Quick Deploy with Blueprint (Recommended)

> **Note:** The project includes a `render.yaml` file that automates the deployment process. This file defines all the infrastructure and settings needed for your application.

1. **Push your code to your Git repository**

2. **Go to Render Dashboard** → "New +" → "Blueprint"

3. **Connect your repository**

4. **Render will automatically detect and parse the `render.yaml` file**

5. **Review the configuration** (review what will be created)

6. **Click "Apply"** and Render will:
   - Create a PostgreSQL database
   - Set up the web service with correct build and start commands
   - Link the database to the web service automatically
   - Configure all environment variables (except frontend URLs)

7. **Update environment variables** after deployment:
   - Go to your web service settings → Environment
   - Set `BACKEND_CORS_ORIGINS` to your frontend URL(s) in JSON array format: `["https://your-frontend.com"]`
   - Set `FRONTEND_URL` to your frontend URL: `https://your-frontend.com`
   - Click "Save Changes" (this will trigger a new deploy)

### Method 2: Manual Deployment

If you prefer manual setup:

#### 1. Create PostgreSQL Database

Go to Render Dashboard → "New +" → "PostgreSQL"
- Name: `votez-db`
- Plan: Starter
- Note the connection details

#### 2. Create Web Service

Go to Render Dashboard → "New +" → "Web Service"
- Connect your repository
- Name: `votez-backend`
- Environment: Python 3
- Branch: `main` (or your default branch)
- Build Command: `pip install --upgrade pip && pip install -r requirements.txt && alembic upgrade head`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### 3. Configure Environment Variables

Add these variables in the Environment section:

```env
ENVIRONMENT=production
SECRET_KEY=<generate-strong-key>
ACCESS_TOKEN_EXPIRE_MINUTES=11520
SERVER_ADDRESS=0.0.0.0
WATCH_FILES=false
POSTGRES_POOL_SIZE=50
POSTGRES_MAX_OVERFLOW=0
LOG_LEVEL=info
BACKEND_CORS_ORIGINS=["https://your-frontend-url.com"]
FRONTEND_URL=https://your-frontend-url.com
```

**Database variables** (get from PostgreSQL service):
- `POSTGRES_SERVER` → Use Internal Database URL host
- `POSTGRES_USER` → Database username
- `POSTGRES_PASSWORD` → Database password
- `POSTGRES_DB` → Database name

#### 4. Link Database to Web Service

In your web service settings, scroll to "Linking" section and link the PostgreSQL service.

#### 5. Deploy

Click "Create Web Service" or "Save Changes"

### Post-Deployment

Once deployed:

1. **Access your API:**
   - API: `https://your-app-name.onrender.com`
   - Docs: `https://your-app-name.onrender.com/docs`

2. **Monitor logs** for any errors

3. **Test endpoints** to ensure everything works

### Deployment Configuration Files

The project includes several files to support deployment:

- **`render.yaml`**: Declarative configuration for Render Blueprint deployment (automatically creates database and web service)
- **`Procfile`**: Process file that tells Render how to run your application
- **`runtime.txt`**: Specifies the Python version for your application

These files ensure your application is ready for deployment without additional configuration.

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment type | `local`, `production` |
| `SECRET_KEY` | JWT secret key | Generate with Python's secrets module |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `11520` (8 days) |
| `SERVER_ADDRESS` | Server bind address | `0.0.0.0` |
| `SERVER_PORT` | Server port | `8000` (local), `10000` (Render) |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:3000"]` |
| `FRONTEND_URL` | Frontend URL | `http://localhost:3000` |
| `POSTGRES_SERVER` | PostgreSQL host | `localhost` or Render internal DNS |
| `POSTGRES_USER` | PostgreSQL username | `db` |
| `POSTGRES_PASSWORD` | PostgreSQL password | Your password |
| `POSTGRES_DB` | PostgreSQL database name | `votez` |
| `POSTGRES_POOL_SIZE` | Connection pool size | `50` |
| `POSTGRES_MAX_OVERFLOW` | Max overflow connections | `0` |
| `COOKIE_KEY` | Cookie encryption key | Random string |
| `WATCH_FILES` | Enable auto-reload | `true` (local), `false` (production) |
| `LOG_LEVEL` | Logging level | `info`, `debug`, `warning`, `error` |

#### Database Connection Issues
- Verify environment variables are set correctly in `.env`
- Check database is running and accessible
- Verify firewall settings
- Test connection: `psql -h localhost -U your_user -d votez`

#### Migration Issues
- Ensure all migrations are applied: `alembic upgrade head`
- Check Alembic version history: `alembic history`
- For fresh start: `alembic stamp head`
- If stuck: drop and recreate database, then run migrations

#### Import Errors
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (requires 3.9+)
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

#### Port Already in Use
- Change `SERVER_PORT` in `.env` to a different port
- Or find and kill the process: `lsof -ti:8000 | xargs kill`

#### Build Fails
- Check build logs in Render dashboard
- Verify `requirements.txt` is up to date
- Ensure Python version is compatible
- Try clearing build cache and redeploying

#### Database Connection Error
- Verify database is linked to web service
- Check `POSTGRES_SERVER` is using internal hostname (not localhost)
- Confirm database credentials are correct
- Ensure database exists and is in same region

#### Application Crashes
- Check logs for specific error messages
- Verify all environment variables are set
- Test database connectivity from Render console
- Check if database migrations ran successfully

#### CORS Issues
- Update `BACKEND_CORS_ORIGINS` with exact frontend URL
- Ensure frontend URL format is correct (JSON array format)
- Include protocol (http/https) in URLs
- Add trailing slash if needed: `https://example.com/`

## Security Notes

- Never commit `.env` files to version control
- Use strong SECRET_KEY in production
- Keep CORS origins restricted to your frontend domains
- Use HTTPS in production
- Regularly update dependencies
- Use environment-specific configurations
