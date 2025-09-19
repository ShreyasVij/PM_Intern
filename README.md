# PM Intern Recommender 🎯

A sophisticated web-based internship recommendation system that leverages machine learning and intelligent matching algorithms to help students discover personalized internship opportunities based on their skills, location preferences, educational background, and career interests.

## 🌟 Features Overview

### 🏠 Home Page (`index.html`)
- **Advanced Search & Filtering**: Multi-criteria search across internship titles, companies, required skills, and locations
- **AI-Powered Recommendations**: Intelligent "Find Similar" functionality using machine learning algorithms
- **Interactive Theme Toggle**: Seamless dark/light mode switching with persistent preferences
- **Real-time Data**: Live internship listings with up-to-date information
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices

### 👤 Profile Management (`profile.html`)
- **Comprehensive Profile Builder**: 
  - Personal information (name, education level)
  - Location preferences with 100+ Indian cities
  - Dynamic skills management with autocomplete
  - Sector interests selection
  - Field of study specification
- **Real-time Validation**: Instant feedback on profile completeness
- **Personalized Recommendations**: AI-driven internship matching based on profile data
- **Profile Persistence**: Automatic saving with MongoDB and JSON backup
- **Progress Tracking**: Visual indicators for profile completion

### 🔐 Authentication System (`login.html`)
- **Secure User Registration**: Account creation with validation
- **Robust Login System**: Session-based authentication
- **Password Security**: Industry-standard hashing with Werkzeug
- **Session Management**: Persistent login state across browser sessions
- **Error Handling**: User-friendly error messages and validation feedback

### 🤖 AI Recommendation Engine
- **Multi-factor Scoring Algorithm**:
  - Skills matching (up to 50 points)
  - Location proximity with geographic calculations (up to 25 points)
  - Sector alignment (15 points)
  - Field of study relevance (5 points)
  - Education level compatibility (5 points)
- **Skill Normalization**: Advanced synonym mapping and skill standardization
- **Geographic Intelligence**: Distance-based scoring using geopy and geographic calculations
- **Fuzzy Matching**: RapidFuzz integration for flexible text matching

## 🛠️ Technical Architecture

### Frontend Stack
- **HTML5**: Semantic markup with accessibility features
- **CSS3**: 
  - CSS custom properties for theming
  - Flexbox and Grid layouts
  - Responsive design patterns
  - Animation and transitions
- **Vanilla JavaScript**: 
  - Modern ES6+ features
  - Fetch API for backend communication
  - Local storage for session management
  - Event-driven architecture

### Backend Stack
- **Python 3.11+** with Flask framework
- **Flask-CORS**: Cross-origin resource sharing
- **PyMongo**: MongoDB integration
- **Werkzeug**: Security utilities and password hashing
- **Geopy**: Geographic calculations and distance measurements
- **Scikit-learn**: Machine learning utilities
- **Pandas & NumPy**: Data processing and analysis

### Database & Storage
- **Primary Storage**: MongoDB for scalable data management
- **Backup Storage**: JSON files for data persistence and migration
- **Dual-write System**: Ensures data consistency across storage layers
- **Data Collections**:
  - `profiles`: User profile information
  - `internships`: Job posting details
  - `login_info`: Authentication credentials
  - `skills_synonyms`: Skill normalization mappings

### API Architecture
RESTful API design with comprehensive endpoint coverage:

#### Authentication Endpoints
- `POST /signup` - User registration with validation
- `POST /login` - User authentication and session creation

#### Profile Management
- `POST /api/profile` - Create/update user profiles with normalization
- `GET /api/profile/<candidate_id>` - Retrieve user profile data
- `GET /api/profiles/by_username/<username>` - Fetch profile by username

#### Internship & Recommendations
- `GET /api/internships` - Retrieve all available internships
- `GET /api/recommendations/<candidate_id>` - Get AI-powered personalized recommendations
- `GET /api/recommendations/by_internship/<internship_id>` - Find similar internships
- `GET /api/recommendations/current_user` - Current user recommendations

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11 or higher
- MongoDB Community Server
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Git (for cloning)

### Step-by-Step Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/DhairyaSood/PM_Intern.git
   cd PM_Intern
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup MongoDB**:
   - Install MongoDB Community Server
   - Start MongoDB service
   - Default connection: `mongodb://localhost:27017/`

5. **Initialize Database**:
   ```bash
   cd backend
   python migrate_data.py
   ```

6. **Start Backend Server**:
   ```bash
   python -m backend.app
   ```
   Server runs on `http://127.0.0.1:3000`

7. **Launch Frontend**:
   - Open `frontend/index.html` in your browser
   - Or use a local web server:
   ```bash
   # Using Python
   cd frontend
   python -m http.server 5500
   
   # Using Node.js (if available)
   npx serve .
   ```

## 📊 Data Structure

### User Profile Schema
```json
{
  "candidate_id": "CAND_xxxxxxxx",
  "name": "string",
  "skills_possessed": ["skill1", "skill2"],
  "location_preference": "string",
  "education_level": "Undergraduate|Postgraduate",
  "field_of_study": "string",
  "sector_interests": ["sector1", "sector2"],
  "created_at": "timestamp",
  "_id": "mongodb_object_id"
}
```

### Internship Schema
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

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:
```env
MONGO_URI=mongodb://localhost:27017/
DB_NAME=internship_recommender
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
```

### MongoDB Configuration
Default settings in `backend/migrate_data.py`:
```python
MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'internship_recommender'
```

## 🎯 Usage Guide

### For Students

1. **Getting Started**:
   - Visit the application homepage
   - Create an account using the signup feature
   - Complete your profile with accurate information

2. **Profile Optimization**:
   - Add all relevant skills (system supports skill synonyms)
   - Specify location preferences accurately
   - Select appropriate education level and field of study
   - Choose sector interests that align with career goals

3. **Finding Opportunities**:
   - Use the search functionality for specific requirements
   - Check personalized recommendations on your profile page
   - Explore similar internships using the AI recommendation feature
   - Filter results based on location, skills, or company

### For Developers

1. **Adding New Features**:
   - Backend: Extend `backend/app.py` with new endpoints
   - Frontend: Add functionality in `frontend/app.js`
   - Database: Update schemas in `backend/migrate_data.py`

2. **Customizing Recommendations**:
   - Modify scoring algorithm in `backend/ml_model.py`
   - Adjust weights for different factors
   - Add new matching criteria

3. **Data Management**:
   - Use `backend/migrate_data.py` for data migrations
   - Update `data/skills_synonyms.json` for skill normalization
   - Backup data regularly using the dual-storage system

## 🧪 Testing

### Manual Testing
1. **User Flow Testing**:
   - Complete signup → profile creation → recommendation viewing
   - Test search and filtering functionality
   - Verify theme switching and data persistence

2. **API Testing**:
   ```bash
   # Test user registration
   curl -X POST http://127.0.0.1:3000/signup \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpass"}'
   
   # Test recommendations
   curl http://127.0.0.1:3000/api/recommendations/CAND_xxxxxxxx
   ```

### Data Validation
- Run `backend/verify_migration.py` to check data integrity
- Use `backend/test_education_interests.py` for specific validations

## 🔒 Security Features

- **Password Security**: Werkzeug-based hashing with salt
- **Input Validation**: Server-side validation for all user inputs
- **CORS Protection**: Configured for development and production
- **Session Management**: Secure session handling
- **Error Handling**: Graceful error responses without sensitive information exposure
- **Data Sanitization**: XSS and injection prevention

## 🚀 Performance Optimizations

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

### Technical Improvements
- **Microservices Architecture**: Service decomposition
- **GraphQL Integration**: More efficient data fetching
- **Redis Caching**: Performance enhancement
- **Docker Containerization**: Simplified deployment
- **CI/CD Pipeline**: Automated testing and deployment
- **API Rate Limiting**: Enhanced security measures

## 📝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

### Code Standards
- Python: Follow PEP 8 guidelines
- JavaScript: Use ES6+ features and consistent formatting
- Documentation: Update README for significant changes
- Testing: Add tests for new functionality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

For support, bug reports, or feature requests:
- Create an issue on GitHub
- Contact: [Your Contact Information]
- Documentation: Check this README and code comments

## 🙏 Acknowledgments

- MongoDB for database technology
- Flask community for web framework
- Scikit-learn for machine learning utilities
- Geopy for geographic calculations
- Contributors and testers

---

**Made with ❤️ for connecting students with their dream internships**