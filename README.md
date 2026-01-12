# SilentCare

A healthcare queue management and analytics system.


## Features

### Core Functionality
-   **OPD Queue Management**: Real-time tracking of patient queues, active doctors, and consultation times.
-   **Role-Based Access**:
    -   **Admin**: View analytics, resolve issues, and manage system data.
    -   **Patient**: View live wait times and historical upload data.

### Machine Learning & Analytics
-   **Wait Time Prediction**: Uses Random Forest Regression (`sklearn`) to predict estimated wait times based on queue size, doctor availability, and time of day.
-   **Future Forecasting**: Predicts hourly crowd intensity for the next 24 hours.
-   **Anomaly Detection**: Automatically detects and alerts on:
    -   Sudden crowd surges (Z-Score analysis).
    -   Severe staff shortages.
    -   Rapid queue growth trends.

## Technology Stack

-   **Backend**: Python, Flask
-   **Database**: PostgreSQL (Production) / SQLite (Dev), SQLAlchemy ORM
-   **ML/AI**: scikit-learn, pandas, numpy
-   **Authentication**: Flask-Login
-   **Deployment**: Render (Gunicorn, Build Scripts)

## Setup

1.  Installed dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Environment Configuration:
    - Copy `.env.example` to `.env`.
    - Update `SECRET_KEY` and `DATABASE_URL`.

3.  Initialize Database:
    ```bash
    python init_db.py
    ```

    *Note: This will create tables with `sc_` prefix (e.g., `sc_users`) to avoid conflicts.*

4.  Run Application:
    ```bash
    python run.py
    ```

## Deployment on Render

This project is configured for deployment on Render.

1.  **Web Service**:
    - **Build Command**: `./build.sh`
    - **Start Command**: `gunicorn run:app`
2.  **Environment Variables**:
    - Add `DATABASE_URL` (Internal Connection URL from Render Postgres).
    - Add `SECRET_KEY`.
    - Add `PYTHON_VERSION` (optional, e.g., `3.9.0`).
