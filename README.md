# WhistleDrop

**Speak Without Being Seen**

WhistleDrop is a confidential reporting backend that allows anyone to submit a report without creating an account or providing personal identity details.

Each report receives a unique case code. The reporter can use this case code later to check the status of the report without revealing their identity.

## Features

- Anonymous report submission
- Securely generated case codes
- Anonymous case tracking
- Moderator authentication using JWT
- Moderator report listing
- Filter reports by status and category
- Controlled report status workflow
- Moderator status updates
- Input validation
- PostgreSQL database
- Swagger/OpenAPI documentation
- Automated tests using Pytest

## Technology Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- JWT
- Argon2 password hashing
- Pytest
- Swagger/OpenAPI

## Report Status Flow

```text
SUBMITTED
    |
    v
UNDER_REVIEW
   / \
  v   v
RESOLVED   DISMISSED

A submitted report must first move to UNDER_REVIEW.

A report in UNDER_REVIEW can then be moved to RESOLVED or DISMISSED.

Closed reports cannot be changed again.

API Endpoints
Health Check
GET /health

Checks whether the API is running.

Submit a Report
POST /reports

Example request:

{
  "category": "Technical",
  "description": "Example confidential report.",
  "evidence_url": "https://example.com/evidence"
}

The server generates the case code automatically.

Example response:

{
  "case_code": "WD-XXXX-XXXX-XXXX-XXXX",
  "status": "SUBMITTED"
}
Track a Report
GET /reports/{case_code}

No authentication is required.

Example response:

{
  "case_code": "WD-XXXX-XXXX-XXXX-XXXX",
  "status": "UNDER_REVIEW",
  "status_update": "Moderator is reviewing this report.",
  "created_at": "...",
  "updated_at": "..."
}
Moderator Login
POST /auth/login

Moderator credentials are configured through environment variables.

The endpoint returns a JWT access token.

List Reports
GET /reports

Requires moderator authentication.

Optional filters:

GET /reports?status_filter=SUBMITTED
GET /reports?category=Technical
Update Report Status
PATCH /reports/{case_code}

Requires moderator authentication.

Example request:

{
  "status": "UNDER_REVIEW",
  "status_update": "Moderator is reviewing this report."
}
Authentication

Moderator endpoints use JWT Bearer authentication.

Moderator credentials are stored through environment variables rather than in the source code.

Passwords are stored as Argon2 hashes.

Never commit .env to GitHub.

Anonymity and Privacy

WhistleDrop does not require the reporter to create an account.

The report system does not collect reporter:

Name
Email
Phone number
User account ID

The public tracking endpoint exposes only the case code, status, status update, and timestamps.

Moderator endpoints are protected using JWT authentication.

Case codes are generated server-side using secure random generation rather than being supplied by the reporter.

Error Handling

The API uses appropriate HTTP status codes for different situations:

200 OK — successful request
201 Created — report successfully created
400 Bad Request — invalid status transition
401 Unauthorized — missing or invalid moderator authentication
404 Not Found — case code does not exist
422 Unprocessable Entity — invalid request data
Project Structure
whistledrop/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   └── routers/
│       ├── __init__.py
│       ├── auth.py
│       └── reports.py
│
├── tests/
│   ├── test_health.py
│   └── test_reports.py
│
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
Setup
1. Clone the repository
git clone <repository-url>
cd whistledrop
2. Create a virtual environment

Windows:

python -m venv .venv

Activate it:

.\.venv\Scripts\Activate.ps1
3. Install dependencies
pip install -r requirements.txt
4. Create the PostgreSQL database

Create a PostgreSQL database named:

whistledrop
5. Configure environment variables

Copy:

.env.example

to:

.env

Configure:

DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/whistledrop

MODERATOR_USERNAME=your-moderator-username
MODERATOR_PASSWORD_HASH=your-argon2-password-hash
JWT_SECRET_KEY=your-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30

Never commit the real .env file.

6. Run the API
.\.venv\Scripts\uvicorn.exe app.main:app --reload

The API will be available at:

http://127.0.0.1:8000
Swagger Documentation

FastAPI automatically provides interactive API documentation at:

http://127.0.0.1:8000/docs

Swagger can be used to demonstrate:

Report submission
Anonymous tracking
Moderator login
Moderator report listing
Filtering
Status updates
Running Tests

Run the automated test suite with:

.\.venv\Scripts\pytest.exe

The test suite covers:

Health endpoint
Report creation
Anonymous tracking
Invalid case codes
Moderator authentication
Protected moderator endpoints
Input validation
Invalid status transitions
Design Decisions
No reporter account

The purpose of WhistleDrop is confidential reporting, so requiring registration would unnecessarily connect a report to an identity.

Server-generated case codes

Reporters do not choose their own case codes. The server generates them using secure random generation.

JWT for moderators

Moderator functionality requires authentication while keeping the system simple and suitable for a small backend.

PostgreSQL

PostgreSQL provides persistent storage and works well with SQLAlchemy.

No frontend required

The core system can be demonstrated through Swagger/OpenAPI, Postman, or cURL, so a separate frontend is not required.

Future Improvements

Possible future additions include:

Moderator dashboard
Advanced report searching
Evidence/file uploads
Rate limiting
Deployment
Additional privacy protections