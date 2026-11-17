
# CloudTask

A cloud-native task management application built using Python Flask, SQLite and Docker.

## Features
- User registration and login
- Secure password hashing
- User-specific task management
- Add and delete tasks
- Update task status
- SQLite database integration
- Docker containerization
- Persistent database storage

## Technologies Used
- Python
- Flask
- SQLite
- HTML and CSS
- Docker
- Docker Compose
- Gunicorn

## Run Locally

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

   pip install -r requirements.txt

4. Run the application:

   python app.py

5. Open http://127.0.0.1:5000

## Run Using Docker

Build and start the container:

    docker compose up --build -d

Open http://localhost:5000

Stop the container:

    docker compose down

## Project Status

The application is implemented and containerized.
Cloud deployment and infrastructure automation are planned future improvements.
