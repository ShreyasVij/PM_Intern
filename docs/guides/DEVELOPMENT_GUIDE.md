# Development Guide

## Getting Started

### Prerequisites
- Python 3.8+
- MongoDB Atlas account (recommended)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PM_Intern
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   copy .env.example .env  # Windows
   # or
   cp .env.example .env    # Linux/Mac
   ```
   
   Edit `.env` with your configuration (Atlas recommended):
   ```
   MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/pm_intern?retryWrites=true&w=majority
   DB_NAME=pm_intern
   DISABLE_JSON_FALLBACK=True
   SECRET_KEY=dev-secret-key-change-in-production
   JWT_SECRET_KEY=jwt-secret-key-change-in-production
   FLASK_ENV=development
   API_PORT=3000
   ```

### Running the Application

#### Development Mode
```bash
python run.py --debug
```

#### Production Mode
```bash
python run.py --port 8000
```

#### With Custom Environment
```bash
python run.py --env production
```

#### Verify Atlas Connectivity
```bash
curl http://127.0.0.1:3000/api/admin/db-stats
```

## Project Structure

```
PM_Intern/
├── app/                    # Main application code
│   ├── main.py            # Flask app factory
│   ├── config.py          # Configuration management
│   ├── api/               # API endpoints
│   │   ├── internships.py
│   │   └── recommendations.py
│   ├── core/              # Core business logic
│   │   ├── database.py
│   │   └── ml_engine.py
│   ├── utils/             # Utility functions
│   └── models/            # Data models
├── scripts/               # Maintenance scripts
│   └── migration/         # Database migration
├── frontend/              # Client-side code
│   ├── pages/            # HTML pages
│   ├── assets/           # CSS, JS, images
│   └── components/       # Reusable components
├── data/                 # JSON data files (legacy/migration only; not used at runtime in Atlas-only mode)
├── docs/                 # Documentation
└── tests/                # Test files
```

## Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**
   ```bash
   python -m pytest tests/
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Add your feature description"
   git push origin feature/your-feature-name
   ```

### Code Style Guidelines

- **Python**: Follow PEP 8
- **JavaScript**: Use ES6+ features
- **HTML/CSS**: Use semantic HTML and organized CSS
- **Documentation**: Use Markdown for all docs

### Database Development

#### Using MongoDB Atlas
```python
from app.core.database import db_manager

db = db_manager.get_db()
collection = db.candidates
```

> Note: In Atlas-only mode (DISABLE_JSON_FALLBACK=True), the app will not read/write JSON files at runtime.

### API Development

1. **Create new endpoint in `app/api/`**
2. **Use response helpers for consistency**:
   ```python
   from app.utils.response_helpers import success_response, error_response
   
   return success_response(data, "Operation successful")
   ```
3. **Add proper error handling**
4. **Update API documentation**

### Frontend Development

1. **Organize assets properly**:
   - CSS in `frontend/assets/css/`
   - JavaScript in `frontend/assets/js/`
   - Images in `frontend/assets/images/`

2. **Use the component system for reusable UI elements**

3. **Follow responsive design principles**

## Testing

### Running Tests
```bash
# All tests
python -m pytest

# Specific test file
python -m pytest tests/test_api.py

# With coverage
python -m pytest --cov=app tests/
```

### Writing Tests
```python
import unittest
from app.main import create_app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
    
    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
```

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in environment
- [ ] Configure proper database connection
- [ ] Set secure `SECRET_KEY`
- [ ] Configure CORS for production domains
- [ ] Set up proper logging
- [ ] Configure reverse proxy (nginx/Apache)

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 3000

CMD ["python", "run.py", "--port", "3000"]
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're in the virtual environment
   - Check PYTHONPATH settings

2. **Database Connection Issues**
   - Verify MongoDB is running
   - Check connection string in `.env`
   - Fallback to JSON mode if needed

3. **Frontend Not Loading**
   - Check static file serving in `app/main.py`
   - Verify file paths in HTML templates

4. **API Errors**
   - Check application logs
   - Verify request format matches API spec
   - Test with curl or Postman

### Debugging Tips

1. **Enable debug mode**:
   ```bash
   python run.py --debug
   ```

2. **Check logs**:
   ```bash
   tail -f logs/application.log
   ```

3. **Use Python debugger**:
   ```python
   import pdb; pdb.set_trace()
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

For questions or issues, please create an issue on the repository.