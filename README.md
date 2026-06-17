# Product Review Forum

A high-performance, full-stack application for sharing product reviews using **FastAPI** for the backend and **Streamlit** for the frontend.

Users can upload product photos or videos, provide detailed metadata (category, source, rating), and engage with the community through a public feed and a comment system. The application features cloud-based media storage via **ImageKit** and a resilient background task system for cleaning up media.

## 🚀 Features

- **Public Review Feed**: Browse product reviews with pagination and advanced filtering.
- **Rich Media Support**: Integrated with ImageKit for optimized image and video hosting.
- **Product Metadata**: Capture product name, category, purchase source, date, country, and star ratings.
- **Robust Authentication**: JWT-based security system with hashed password storage.
- **Community Engagement**:
  - Publicly visible comment threads.
  - **15-Minute Edit Window**: Users can modify or retract their comments within a 15-minute grace period.
- **Resilient Background Tasks**:
  - Media deletion is handled in the background to ensure fast API response times.
  - **Tenacity Integration**: Cloud storage operations utilize exponential backoff retries to handle transient network failures.
- **Clean Architecture**: Separation of concerns using Pydantic schemas, SQLAlchemy ORM models, and modular routing.

## 🛠️ Tech Stack

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=python&logoColor=white)
![ImageKit](https://img.shields.io/badge/ImageKit-0033CC?style=for-the-badge&logo=image&logoColor=white)
![Tenacity](https://img.shields.io/badge/Tenacity-FFD43B?style=for-the-badge&logo=python&logoColor=blue)
![uv](https://img.shields.io/badge/uv-de5fe9?style=for-the-badge&logo=rust&logoColor=white)

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous)
- **Frontend**: [Streamlit](https://streamlit.io/) (Custom CSS Themed)
- **Database**: PostgreSQL with [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async)
- **Media Storage**: [ImageKit.io](https://imagekit.io/)
- **Task Resilience**: [Tenacity](https://tenacity.readthedocs.io/)
- **Dependency Management**: [uv](https://github.com/astral-sh/uv)

## 📂 Project Structure

```text
.
|-- app/
|   |-- api/routes/ # Modular API
|   |   |-- authRoutes.py
|   |   `-- postRoutes.py
|   |-- core/  # Configuration
|   |   |-- config.py
|   |   |-- exceptions.py
|   |   |-- imagekit.py
|   |   |-- logger.py
|   |   `-- security.py
|   |-- database/   # DB engine and
|   |   |-- base.py
|   |   `-- db.py
|   |-- models/  # SQLAlchemy ORM
|   |   `-- models.py
|   |-- schemas/       # Pydantic validation
|   |   |-- auth_schemas.py
|   |   `-- post_schemas.py
|   `-- app.py
|-- main.py    # Backend entry point
|-- streamlit_app.py  # Frontend application
|-- pyproject.toml # Modern project
|-- requirements.txt  # Standard dependency
|-- uv.lock
|-- .env.example
`-- README.md
```

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.13+
- PostgreSQL
- ImageKit Account (Free tier works)

### 1. Clone & Environment

```bash
git clone https://github.com/your-username/fastapi-streamlit-product-review-forum.git
cd fastapi-streamlit-product-review-forum
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory based on `.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
IMAGEKIT_PUBLIC_KEY=your_public_key
IMAGEKIT_PRIVATE_KEY=your_private_key
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your_id
AUTH_SECRET_KEY=your_super_secret_key
```

### 3. Install Dependencies

Using **uv** (recommended):

```bash
uv sync
```

Using **pip**:

```bash
pip install -r requirements.txt
```

## 🏃 Running the Application

### Start the Backend

```bash
python main.py
```

- **API**: http://localhost:8000
- **Docs (Swagger)**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Start the Frontend

In a new terminal:

```bash
streamlit run streamlit_app.py
```

- **Frontend**: http://localhost:8501

## 🛣️ API Endpoints

### Authentication

| Method  | Endpoint         | Description              |
| :------ | :--------------- | :----------------------- |
| `POST`  | `/auth/register` | Create a new account     |
| `POST`  | `/auth/login`    | Obtain JWT access token  |
| `GET`   | `/auth/me`       | Get current user profile |
| `PATCH` | `/auth/me`       | Update user profile      |

### Posts & Media

| Method   | Endpoint             | Description                             |
| :------- | :------------------- | :-------------------------------------- |
| `GET`    | `/posts/feed`        | Paginated public feed                   |
| `POST`   | `/posts/upload`      | Upload media and review (Auth required) |
| `GET`    | `/posts/me`          | Get reviews by current user             |
| `DELETE` | `/posts/{id}`        | Delete post and cloud media             |
| `POST`   | `/posts/bulk-delete` | Batch delete multiple posts             |

### Comments

| Method   | Endpoint               | Description                  |
| :------- | :--------------------- | :--------------------------- |
| `GET`    | `/posts/{id}/comments` | List comments for a post     |
| `POST`   | `/posts/{id}/comments` | Post a new comment           |
| `PATCH`  | `/comments/{id}`       | Edit comment (15-min window) |
| `DELETE` | `/comments/{id}`       | Delete comment               |

## 🛡️ Security & Reliability

1.  **Transactional Safety**: Database operations use async sessions with automatic rollbacks on failure.
2.  **Orphaned File Prevention**: If a database save fails after a media upload, the application attempts to clean up the file from ImageKit immediately.
3.  **Tenacity Retries**: Background deletion tasks are decorated with `@retry`. If ImageKit is temporarily unreachable, the app will retry with **exponential backoff** (waiting longer between attempts) to ensure cloud storage remains in sync with the database.
4.  **Input Sanitization**: All text inputs are stripped of whitespace and validated against length constraints using Pydantic.

## 📝 Development Notes

- **Database Migrations**: Tables are currently created automatically on startup in `app/app.py`. For production use, it is recommended to transition to **Alembic**.
- **Virtual Environments**: Ensure your IDE is using the Python interpreter located inside your `venv` or `.venv` folder to resolve imports correctly.

## 📄 License

This project is open-source and available under the MIT License.

---

_Developed with ❤️ using FastAPI and Streamlit._
