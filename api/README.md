To generate a comprehensive `README.md` file for a Flask API project, including
installation of dependencies from `requirements.txt`, setting up PostgreSQL
(PSQL) database, and running the API in development and production modes using
Flask and Gunicorn, you can structure it as follows:

### Project Name

Brief description of your project.

#### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Setup Virtual Environment (recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

#### Setting Up PostgreSQL (PSQL)

1. **Install PostgreSQL:**

   - For Ubuntu:
     ```bash
     sudo apt-get update
     sudo apt-get install postgresql postgresql-contrib
     ```
   - For macOS (using Homebrew):
     ```bash
     brew install postgresql
     ```

2. **Start PostgreSQL service:**

   - Ubuntu:
     ```bash
     sudo service postgresql start
     ```
   - macOS (Homebrew):
     ```bash
     brew services start postgresql
     ```

3. **Connect to PostgreSQL CLI:**

   ```bash
   psql -U postgres
   ```

4. **Create database and user:**

   ```sql
   CREATE DATABASE sautis;
   CREATE USER sautis_user WITH PASSWORD 'password';
   ALTER ROLE sautis_user SET client_encoding TO 'utf8';
   ALTER ROLE sautis_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE sautis_user SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE sautis TO sautis_user;
   ```

5. **Exit PostgreSQL CLI:**
   ```sql
   \q
   ```

#### Running the API

1. **Development Mode (Flask):**

   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   flask run
   ```

2. **Production Mode (Gunicorn):**

   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

   - `-w 4` specifies 4 worker processes (adjust as per your server
     configuration).
   - `-b 0.0.0.0:5000` binds Gunicorn to all interfaces on port 5000.

3. **Access API:** Open a web browser and go to `http://localhost:5000` to
   access the API endpoints.

#### API Endpoints

Document your API endpoints here with examples and descriptions.

#### Additional Notes

Include any additional information or notes relevant to your project setup and
usage.

### Example `.env` File

For managing environment variables (`dotenv`), you can provide an example `.env`
file:

```plaintext
FLASK_APP=app.py
FLASK_ENV=development

# Database
DATABASE_URL=postgresql://sautis_user:password@localhost:5432/sautis
```

Replace placeholders like `<repository-url>`, `<project-directory>`, `password`,
and adjust database settings (`DATABASE_URL`) as per your actual configuration.

This structured `README.md` file provides clear instructions for installing
dependencies, setting up PostgreSQL, and running your Flask API in both
development and production environments using Gunicorn. Adjust paths, database
credentials, and environment variables as per your project specifics.
