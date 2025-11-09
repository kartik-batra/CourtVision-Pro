# CourtVision Pro - Installation Guide

## Quick Start (Automated Setup)

Run the automated setup script:

```bash
cd /workspace/cmhngkess011yr3ile356tas2/CourtVision-Pro
bash setup.sh
```

This will:
- Install all dependencies
- Create configuration files
- Run database migrations
- Set up directory structure

---

## Manual Installation Steps

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: This installs 30+ packages and may take 5-10 minutes. Required packages include:
- Django 5.1.3
- AI/ML libraries (OpenAI, transformers, scikit-learn, torch)
- Search engines (Elasticsearch client, FAISS)
- Data processing (pdfplumber, beautifulsoup4, selenium)
- And more...

### Step 2: Configure Environment

Create a `.env` file in the project root:

```bash
# Minimal configuration for development
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Optional: Add these for full AI features
# OPENAI_API_KEY=your-openai-api-key
# REDIS_URL=redis://localhost:6379/0
# ELASTICSEARCH_HOST=localhost:9200
```

### Step 3: Initialize Database

```bash
python manage.py migrate
```

This creates the SQLite database with all required tables.

### Step 4: Create Admin User

```bash
python manage.py createsuperuser
```

Follow prompts to create an admin account.

### Step 5: Load Demo Data (Optional)

```bash
python manage.py setup_demo
```

This creates sample cases, courts, and users for testing.

### Step 6: Import Legal Data (Optional)

**Note**: This command requires all dependencies to be installed first.

```bash
# Import recent legal data (last 30 days)
python manage.py import_legal_data --days=30

# View help for more options
python manage.py import_legal_data --help
```

### Step 7: Start the Server

```bash
python manage.py runserver
```

Access the application at: http://localhost:8000

---

## Troubleshooting

### Error: "Unknown command: 'import_legal_data'"

**Cause**: Django is not installed or not found in Python path.

**Solution**:
```bash
# Verify Django is installed
python -c "import django; print(django.VERSION)"

# If not installed, run:
pip install -r requirements.txt
```

### Error: "No module named 'aiohttp'" (or other module)

**Cause**: Not all dependencies are installed.

**Solution**:
```bash
# Install all requirements
pip install -r requirements.txt

# Or install individual packages
pip install aiohttp beautifulsoup4 pdfplumber
```

### Error: Database migration issues

**Solution**:
```bash
# Reset migrations (development only)
rm db.sqlite3
rm -rf legal_research/migrations/0*.py
python manage.py makemigrations
python manage.py migrate
```

### AI Features Not Working

**Cause**: Optional AI dependencies not installed or API keys not configured.

**Solution**:
```bash
# Ensure AI packages are installed
pip install openai transformers sentence-transformers torch

# Add API key to .env file
echo "OPENAI_API_KEY=your-key-here" >> .env
```

---

## System Requirements

### Minimum Requirements
- Python 3.8+
- 2GB RAM
- 1GB disk space

### Recommended for Production
- Python 3.11+
- 8GB RAM
- 10GB disk space
- PostgreSQL database
- Redis server
- Elasticsearch (optional, for enhanced search)

---

## Production Deployment

For production deployment:

1. **Use PostgreSQL** instead of SQLite:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/courtvision
   ```

2. **Set up Redis** for caching:
   ```
   REDIS_URL=redis://localhost:6379/0
   ```

3. **Configure Celery** for background tasks:
   ```bash
   celery -A courtvision worker -l info
   celery -A courtvision beat -l info
   ```

4. **Use a production web server** (Gunicorn):
   ```bash
   gunicorn courtvision.wsgi:application --bind 0.0.0.0:8000
   ```

5. **Set DEBUG=False** and use a strong SECRET_KEY

---

## Next Steps

After installation:

1. **Access Admin Panel**: http://localhost:8000/admin
2. **Explore Features**: Navigate to legal research section
3. **Configure AI Services**: Add API keys for AI features
4. **Import Legal Data**: Use management commands to populate database
5. **Customize Settings**: Edit `courtvision/settings.py` as needed

---

## Getting Help

- Check the main README.md for feature documentation
- Review Django logs in `logs/` directory
- Check AI-specific logs in `logs/ai/` directory
- Review audit logs in `logs/audit/` directory

---

## Available Management Commands

After installation, these commands are available:

```bash
# Import legal data
python manage.py import_legal_data --help

# Set up demo data
python manage.py setup_demo

# Train ML models
python manage.py train_ml_models

# Database operations
python manage.py migrate
python manage.py makemigrations
python manage.py createsuperuser

# Development server
python manage.py runserver
```
