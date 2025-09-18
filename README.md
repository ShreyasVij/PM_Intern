# PM Intern Recommender

A web application that helps students find personalized internship recommendations based on their skills, location preferences, and education level.

## Features

### 1. Home Page (index.html)
- **Search & Filter**: Search internships by title, company, skills, or location
- **AI Recommendations**: Click "Find Similar (AI)" on any internship to get AI-powered similar opportunities
- **Theme Toggle**: Switch between light and dark themes
- **Login/Logout**: User authentication with session management

### 2. Profile Page (profile.html)
- **Personal Information**: Enter name, education level (UG/PG), and field of study
- **Location Preference**: Select from 100+ Indian cities
- **Skills Management**: Add/remove skills with a dynamic interface
- **Sector Interests**: Specify areas of interest
- **Personalized Recommendations**: Get internship recommendations based on your profile
- **Real-time Updates**: Profile data is saved to the backend and used for recommendations

### 3. Login/Signup Page (login.html)
- **User Registration**: Create new accounts with username and password
- **Secure Login**: Password hashing for security
- **Session Management**: Persistent login state across pages
- **Error Handling**: User-friendly error messages

## Technical Stack

### Frontend
- **HTML5**: Semantic markup and modern structure
- **CSS3**: Custom styling with CSS variables for theming
- **JavaScript**: Vanilla JS for interactivity and API calls
- **Responsive Design**: Mobile-friendly interface

### Backend
- **Python Flask**: RESTful API server
- **JSON Storage**: File-based data persistence
- **Password Security**: Werkzeug password hashing
- **CORS Support**: Cross-origin resource sharing enabled

### Data Structure
- **Candidates**: User profiles with skills and preferences
- **Internships**: Job postings with requirements and details
- **Login Info**: User authentication data
- **Profiles**: Extended user profile information

## Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Backend Server**:
   ```bash
   cd backend
   python app.py
   ```
   Server runs on `http://127.0.0.1:3000`

3. **Open Frontend**:
   - Open `frontend/index.html` in your web browser
   - Or serve it with a local web server

## API Endpoints

- `POST /signup` - User registration
- `POST /login` - User authentication
- `POST /api/profile` - Save user profile
- `GET /api/profile/<id>` - Get user profile
- `GET /api/internships` - Get all internships
- `GET /api/recommendations/<candidate_id>` - Get personalized recommendations
- `GET /api/recommendations/by_internship/<internship_id>` - Get similar internships

## Usage Flow

1. **Sign Up/Login**: Create an account or log in
2. **Create Profile**: Fill out your profile with skills, location, and education
3. **Get Recommendations**: View personalized internship suggestions
4. **Search & Explore**: Use the search functionality to find specific opportunities
5. **AI Discovery**: Use the AI recommendation feature to find similar internships

## Data Files

- `data/candidates.json` - User profiles and candidate data
- `data/internships.json` - Internship listings
- `data/profiles.json` - Extended profile information
- `data/login-info.json` - User authentication data
- `data/skills_synonyms.json` - Skills normalization data

## Security Features

- Password hashing using Werkzeug
- Input validation and sanitization
- CORS protection
- Error handling and user feedback

## Future Enhancements

- Machine learning model integration
- Advanced filtering options
- User dashboard
- Application tracking
- Email notifications
- Social features

---

# PM_Intern