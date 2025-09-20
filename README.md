# PM Intern Recommender 🎯

A sophisticated, production-ready internship recommendation system that connects students with personalized internship opportunities through advanced machine learning algorithms, intelligent matching, and a modern, scalable architecture.

## ✨ Overview

PM Intern Recommender is a professional-grade web application featuring a **modular Flask backend** with **dual database support** (MongoDB + JSON fallback), **comprehensive error handling**, **standardized API responses**, and a **responsive frontend** with organized asset management.

## 🚀 Quick Start

### Installation
```bash
git clone <repository-url>
cd PM_Intern
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Configuration
```bash
copy .env.example .env
# Edit .env with your database settings
```

### Run the Application
```bash
python run.py --debug
```

Frontend (served by the backend) is available at:

- http://127.0.0.1:3000/frontend/pages/index.html

API base (same origin) is:

- http://127.0.0.1:3000/api

## 🌟 Key Features

### 🏠 **Smart Internship Discovery**
- **Advanced Search & Filtering**: Multi-criteria search across titles, companies, skills, and locations
- **AI-Powered Recommendations**: ML-driven "Find Similar" functionality with personalized scoring
- **Real-time Results**: Live internship listings with instant search feedback
- **Interactive UI**: Dark/light theme toggle with persistent preferences

### 👤 **Comprehensive Profile Management**
- **Profile Builder**: Personal info, education, location preferences, skills, and interests
- **Smart Autocomplete**: Dynamic skills management with intelligent suggestions
- **Progress Tracking**: Visual indicators for profile completion and optimization
- **Data Persistence**: Automatic saving with MongoDB and JSON backup systems

### 🔐 **Secure Authentication**
- **User Registration & Login**: Secure account creation and session management
- **Password Security**: Industry-standard hashing with Werkzeug
- **Session Persistence**: Maintained login state across browser sessions
- **Validation & Error Handling**: User-friendly feedback and robust error management

### 🤖 **Advanced AI Recommendation Engine**
- **Multi-factor Scoring Algorithm**:
  - Skills matching (weighted up to 50 points)
  - Geographic proximity with distance calculations (25 points)
  - Sector alignment and field compatibility (20 points)
  - Education level matching (5 points)
- **Intelligent Processing**: Skill normalization, synonym mapping, and fuzzy text matching
- **Performance Optimized**: Efficient algorithms with response caching

## 🏗️ Architecture

### **New Modular Structure (v2.0)**
```
PM_Intern/
├── app/                    # 🚀 Runtime Application
│   ├── main.py            # Flask factory & routing
│   ├── config.py          # Environment configuration
│   ├── api/               # Modular API endpoints
│   ├── core/              # Business logic & database
│   ├── utils/             # Shared utilities
│   └── models/            # Data models & schemas
├── scripts/               # 🔧 Maintenance Tools
├── frontend/              # 🎨 Organized Client Assets
│   ├── pages/            # HTML templates
│   ├── assets/           # CSS, JS, images
│   └── components/       # Reusable UI components
├── docs/                  # 📚 Professional Documentation
│   ├── architecture/     # System design docs
│   ├── guides/           # Development guides
│   └── api/              # API references
└── data/                  # 💾 JSON data storage
```

### **Technology Stack**

#### Backend
- **Python 3.8+** with Flask framework
- **MongoDB** primary database with **JSON fallback**
- **Flask-CORS** for cross-origin support
- **Modular Architecture** with separation of concerns
- **Comprehensive Error Handling** and logging
- **Standardized API Responses** with success/error patterns

#### Frontend
- **HTML5** with semantic markup
- **Modern CSS3** with custom properties and responsive design
- **Vanilla JavaScript** with ES6+ features and Fetch API
- **Component-based Architecture** for reusable UI elements
- **Organized Asset Management** with dedicated folders
 - Responsive design patterns; subtle animations/transitions

#### Data Layer
- **MongoDB** for scalable primary storage
- **JSON Files** for backup and development
- **Dual-write System** ensuring data consistency
- **Connection Pooling** and health checks

### **API Design**

#### **Authentication**
- `POST /signup` - User registration (legacy-compatible alias for `/api/auth/signup`)
- `POST /login` - User authentication and session management (alias for `/api/auth/login`)
- `POST /logout` - Logout (alias for `/api/auth/logout`)

#### **Core API Endpoints**
- `GET /api/internships` - Get internship listings with filtering
- `GET /api/recommendations/{candidate_id}` - Get personalized recommendations
- `GET /api/recommendations/by_internship/{internship_id}` - Get internships similar to a selected one

#### **Profile Management**
- `POST /api/profile` - Create/update user profiles
- `GET /api/profile/{candidate_id}` - Retrieve profile data
- `GET /api/profiles/by_username/{username}` - Fetch by username

#### **Health & Monitoring**
- `GET /health` - Application health check and status
- Comprehensive error responses with standardized format
- Request/response logging and monitoring

## 🚀 Getting Started

### **Prerequisites**
- Python 3.8+ 
- MongoDB (optional - JSON fallback available)
- Modern web browser
- Git

### **Installation**

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd PM_Intern
   ```

2. **Setup Environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup MongoDB**:
   (Optional) Ensure a MongoDB instance is available; otherwise the app will fallback to JSON files.
   ```

4. **Configuration** (Optional)
   ```bash
   copy .env.example .env  # Windows
   # Edit .env for MongoDB connection (fallback to JSON if not configured)
   ```

5. **Run Application**
   ```bash
   python run.py --debug
   ```

6. **Access Application**
   - Open browser to `http://127.0.0.1:3000/frontend/pages/index.html`
   - Application ready! 🎉

### **Development Commands**
```bash
# Development mode with auto-reload
python run.py --debug

# Production mode
python run.py --port 8000

# Custom environment
python run.py --env production
```

## 📊 Data Structure & API

### **Profile Schema**
```json
{
  "candidate_id": "CAND_xxxxxxxx",
  "name": "string",
  "skills_possessed": ["skill1", "skill2"],
  "location_preference": "string",
  "education_level": "Undergraduate|Postgraduate",
}
```

### **Internship Schema**
```json
{
  "internship_id": "INTxxxx",
  "title": "string",
  "company": "string",
  "location": "string",
  "skills_required": ["skill1", "skill2"],
  "sector": "string",
  "education_level": "string",
  "description": "string",
  "duration": "string",
  "stipend": "string"
}
```

### **API Response Format**
```json
{
  "success": true,
  "data": {...},
  "message": "Operation successful",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🎯 Usage Guide

### For Students

1. **Getting Started**:
   - Visit the application homepage
   - Create an account using the signup feature
   - Complete your profile with accurate information

2. **Profile Optimization**:
   - Add all relevant skills (system supports skill synonyms)
### **For Users**

1. **Create Account & Profile**
   - Register with unique username/password
   - Complete profile with skills, location, education
   - Set sector interests and field of study

2. **Discover Internships**
   - Browse internship listings on home page
   - Use advanced search and filtering
   - Get personalized recommendations from your profile
   - Use "Find Similar" feature for targeted discovery

3. **Profile Optimization**
   - Keep skills updated and relevant
   - Specify accurate location preferences
   - Complete all profile sections for better recommendations

### **For Developers**

1. **Development Setup**
   ```bash
   python run.py --debug
   # Access frontend at http://127.0.0.1:3000/frontend/pages/index.html
   ```

2. **Adding Features**
   - Create new API endpoints in `app/api/`
   - Add frontend components in `frontend/components/`
   - Use standardized response helpers from `app/utils/`

3. **Database Operations**
   ```python
   from app.core.database import get_db_connection
   db = get_db_connection()
   # MongoDB operations with JSON fallback
   ```

## 🧪 Testing & Validation

### **Health Checks**
```bash
curl http://127.0.0.1:3000/health
# Returns application status and version
```

### **API Testing**
```bash
# Test internships endpoint
curl http://127.0.0.1:3000/api/internships

# Test recommendations
curl http://127.0.0.1:3000/api/recommendations/CAND_xxxxxxxx
```

### **Data Validation**
- Automatic data integrity checks
- Input validation and sanitization
- Error logging and monitoring

## 🔒 Security & Performance

- **Efficient Algorithms**: O(n log n) sorting for recommendations
- **Caching**: Skill synonym caching for faster lookups
- **Database Indexing**: MongoDB indexes on frequently queried fields
- **Lazy Loading**: Frontend components load on demand
- **Minification**: CSS and JS optimization for production

## 🔮 Future Roadmap

### Planned Features
- **Advanced ML Models**: Deep learning for better recommendations
- **User Analytics**: Dashboard with application tracking
- **Company Integration**: Direct company job posting interface
- **Mobile Application**: React Native or Flutter mobile app
- **Email Notifications**: Automated alerts for new opportunities
- **Social Features**: User reviews and company ratings
- **Resume Builder**: Integrated CV creation tools
- **Interview Preparation**: Resources and practice modules

### **Security Features**
- **Password Security**: Werkzeug-based hashing with salt
- **Input Validation**: Server-side validation and sanitization
- **CORS Protection**: Configured for secure cross-origin requests
- **Session Management**: Secure session handling with proper timeouts
- **Error Handling**: Graceful error responses without information leakage
- **Request Logging**: Comprehensive request/response monitoring

### **Performance Optimizations**
- **Database Connection Pooling**: Efficient MongoDB connections
- **Dual Storage System**: MongoDB primary + JSON fallback for reliability
- **Modular Architecture**: Reduced loading times and improved maintainability
- **Optimized Frontend**: Organized assets and component-based structure
- **Efficient Algorithms**: Optimized recommendation scoring and matching

## 📚 Documentation

### **Complete Documentation Available**
- 📖 **[Development Guide](docs/guides/DEVELOPMENT_GUIDE.md)**: Setup, workflows, and best practices
- 🏗️ **[Architecture Documentation](docs/architecture/)**: System design and comparisons
- 🔧 **[API Reference](docs/api/API_REFERENCE.md)**: Complete endpoint documentation
- 📋 **[Project Guides](docs/guides/)**: Implementation and troubleshooting guides

### **Quick Links**
- **Getting Started**: See [Development Guide](docs/guides/DEVELOPMENT_GUIDE.md)
- **API Documentation**: Check [API Reference](docs/api/API_REFERENCE.md)
- **Architecture Details**: View [Architecture Docs](docs/architecture/)

## 🚀 Deployment & Production

### **Production Checklist**
- [ ] Set `DEBUG=False` in environment
- [ ] Configure MongoDB connection
- [ ] Set secure `SECRET_KEY`
- [ ] Configure CORS for production domains
- [ ] Set up reverse proxy (nginx recommended)
- [ ] Configure application logging

### **Docker Support**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["python", "run.py", "--port", "3000"]
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature-name`
3. **Make changes** following code standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit pull request**

### **Code Standards**
- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use ES6+ features and consistent formatting
- **Documentation**: Update README and docs for significant changes
- **Testing**: Add comprehensive tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask Community** for the excellent web framework
- **MongoDB** for scalable database technology
- **Open Source Libraries**: scikit-learn, geopy, and other dependencies
- **Contributors** and community feedback

---

**PM Intern Recommender v2.0** - Professional Internship Matching Platform 🎯

**Made with ❤️ for connecting students with their dream internships**