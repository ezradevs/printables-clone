# Printables Clone

This is a minimal web application similar to Printables.com, built with Python, Flask, and SQLite.

## Features

*   User authentication (sign up, log in, log out)
*   Secure password hashing
*   Model uploading (STL/3MF files) with title, description, and tags
*   Model browsing with search by title or tags
*   Model detail page with download button
*   Download count per model

## Setup and Running

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Run the application:**

    ```bash
    python app.py
    ```

    The application will be available at `http://127.0.0.1:5000`.

## File Structure

*   `app.py`: The main Flask application file, containing all routes and logic.
*   `requirements.txt`: A list of the Python packages required to run the application.
*   `templates/`: HTML templates for the application.
*   `static/`: Static files (not used in this MVP).
*   `uploads/`: Directory where uploaded model files and images are stored.
*   `instance/app.db`: The SQLite database file.
*   `README.md`: This file.
