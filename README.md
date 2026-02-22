# Headless Chat API - Developer Guide

Welcome to the Headless Chat API project! This guide will help you set up your development environment, understand the
architecture, and start contributing. This is an open-source project built with modern Python async patterns.

## 🚀 Tech Stack

* **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Async Python API framework)
* **Database**: PostgreSQL with [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/) (Async Engine) and `asyncpg`.
* **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
* **Realtime/PubSub**: [Redis](https://redis.io/) (using `redis-py` async)
* **Server**: [Uvicorn](https://www.uvicorn.org/)
* **Authentication**: JWT (JSON Web Tokens) with Argon2 password hashing.

---

## 🛠️ Local Setup

### Prerequisites

* Python 3.12+
* Docker & Docker Compose (for Postgres and Redis)
* `git`

### 1. Clone & Environment

Clone the repository and set up a virtual environment:

```bash
git clone <repository_url>
    cd headless-chat
    python -m venv venv
    source venv/bin/activate # On Windows: venv\\Scripts\\activate
    ```

    ### 2. Install Dependencies

    We use a standard `pyproject.toml` file.

    ```bash
    pip install -e .
    # If you are going to run tests:
    pip install pytest pytest-asyncio httpx
    ```

    *(Note: I use `hatchling` as a build backend, but a simple `pip install` works fine for development).*

    ### 3. Start Infrastructure (Database & Redis)

    The project includes a `docker-compose.yml` file to quickly spin up the required backing services.

    ```bash
    docker compose up -d
    ```

    This starts:
    * PostgreSQL on port `5432`
    * Redis on port `6379`

    ### 4. Configuration

    The application uses `pydantic-settings` to manage configuration via a `.env` file. Create one in the root
    directory:

    ```bash
    cat <<EOF> .env
        PROJECT_NAME="Headless Chat API - Dev"
        DEBUG=True
        # Points to localhost because your app runs on host, while DB is in Docker mapping to 5432
        DATABASE_URL=postgresql+asyncpg://chat_user:chat_password@localhost:5432/chat_db
        REDIS_URL=redis://localhost:6379/0
        SECRET_KEY=yoursecretkey_change_me_in_production
        ALGORITHM=HS256
        ACCESS_TOKEN_EXPIRE_MINUTES=30
        EOF
        ```

        ### 5. Run Database Migrations

        Before running the server, ensure your database schema is up-to-date.

        ```bash
        alembic upgrade head
        ```

        If you make changes to `src/models/all_models.py`, generate a new migration:

        ```bash
        alembic revision --autogenerate -m "Description of change"
        alembic upgrade head
        ```

        ---

        ## 🏃 Running the Server

        Start the FastAPI application using Uvicorn with auto-reload enabled:

        ```bash
        # Make sure you are in your virtual environment
        uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
        ```

        * **Interactive API Docs (Swagger UI)**: `http://localhost:8000/docs`
        * **Alternative Docs (ReDoc)**: `http://localhost:8000/redoc`

        ---

        ## 🧪 Testing

        We use `pytest` with `pytest-asyncio` for testing. The test suite is configured to use an isolated, in-memory
        SQLite database (`aiosqlite`) so you don't need a dedicated test PostgreSQL instance, making tests fast and
        independent.

        To run the test suite:

        ```bash
        pytest tests/ -v
        ```

        ---

        ## 🏗️ Architecture Overview

        The codebase is organized into modules to keep concerns separated:

        * `src/api/deps.py`: FastAPI Dependency Injection (Authentication, Database Sessions, WebSockets).
        * `src/core/`: Application-wide settings, logging, Connection Manager (for WebSockets), and Redis Pub/Sub
        manager.
        * `src/database/`: SQLAlchemy engine initialization and session management.
        * `src/models/`: SQLAlchemy ORM models. All models import from `src.database.base_class.Base`.
        * `src/modules/`: The core business logic, separated by domain (`auth`, `users`, `conversations`, `messages`,
        `realtime`).
        * Each module usually contains a `router.py` defining the REST endpoints.
        * `src/schemas/`: Pydantic models for request validation and response serialization.

        ### Realtime Flow

        1. A user connects to `ws://localhost:8000/ws?token=<JWT>`.
            2. The `ConnectionManager` stores the active websocket mapped to the user's ID.
            3. When *any* user sends a message via `POST /api/v1/conversations/{id}/messages`:
            * The message is saved to PostgreSQL.
            * The API fetches all participants of that conversation.
            * It publishes the message and participant list to a Redis channel (`chat_events`) via the
            `RedisPubSubManager`.
            4. All connected FastAPI worker processes are listening to that Redis channel.
            5. When a worker receives the event, it checks if any of the target participants have an active websocket
            connected *to that specific worker instance*, and if so, pushes the message down the socket.

            ---

            ## 🤝 Contributing

            1. Fork the repository.
            2. Create a feature branch (`git checkout -b feature/amazing-feature`).
            3. Commit your changes (`git commit -m 'Add amazing feature'`).
            4. Write tests for new logic if applicable.
            5. Push to the branch (`git push origin feature/amazing-feature`).
            6. Open a Pull Request.

            Happy coding!