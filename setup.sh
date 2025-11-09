#!/bin/bash

echo "=================================================="
echo "CourtVision Pro - AI Research Engine Setup"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1)
echo "Found: $python_version"
echo ""

# Install dependencies
echo "Installing dependencies from requirements.txt..."
echo "This may take several minutes..."
echo ""

pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Dependencies installed successfully!"
    echo ""
else
    echo ""
    echo "✗ Failed to install dependencies"
    echo "Please check the error messages above"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating default .env file..."
    cat > .env << 'EOF'
# Django Settings
SECRET_KEY=django-insecure-courtvision-dev-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
# For PostgreSQL, use: DATABASE_URL=postgresql://user:password@localhost:5432/courtvision

# Redis (optional - comment out if not using)
# REDIS_URL=redis://localhost:6379/0

# AI Configuration (optional - add your API key to enable AI features)
# OPENAI_API_KEY=your-openai-api-key-here
# OPENAI_MODEL=gpt-4-turbo-preview

# Elasticsearch (optional)
# ELASTICSEARCH_HOST=localhost:9200

# Settings
MONITORING_ENABLED=True
ANALYTICS_ENABLED=True
EOF
    echo "✓ Created default .env file"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs logs/ai logs/audit models media static
echo "✓ Directories created"
echo ""

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Database migrations completed!"
    echo ""
else
    echo ""
    echo "✗ Migration failed"
    exit 1
fi

# Check if management command is now available
echo "Verifying management commands..."
python manage.py help import_legal_data > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Management commands are working!"
    echo ""
else
    echo "⚠ Warning: Management commands may not be fully initialized"
    echo ""
fi

echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Create a superuser account:"
echo "   python manage.py createsuperuser"
echo ""
echo "2. Load demo data:"
echo "   python manage.py setup_demo"
echo ""
echo "3. (Optional) Import legal data:"
echo "   python manage.py import_legal_data --days=30"
echo ""
echo "4. Start the development server:"
echo "   python manage.py runserver"
echo ""
echo "5. Access the application at:"
echo "   http://localhost:8000"
echo ""
echo "=================================================="
echo ""
echo "Note: AI features require additional configuration"
echo "Edit .env file to add your OpenAI API key and other services"
echo ""
