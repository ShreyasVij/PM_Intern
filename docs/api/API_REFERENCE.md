# API Reference

## Base URL
```
http://127.0.0.1:3000
```

## Endpoints
### Admin
- **GET** `/api/admin/db-stats`
- **Description**: Basic database diagnostics (connection status, Atlas-only flag, and collection counts)
- **Response**:
  ```json
  {
    "database": "connected",
    "atlas_only": true,
    "counts": { "profiles": 9, "internships": 500, "login_info": 11, "skills_synonyms": 480 }
  }
  ```


### Health Check
- **GET** `/health`
- **Description**: Check if the API is running
- **Response**: 
  ```json
  {
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "2.0.0"
  }
  ```

### Authentication
- **POST** `/api/auth/signup`
- **POST** `/api/auth/login` (aliases also available at `/signup` and `/login` for legacy clients)
- **POST** `/api/auth/logout` (alias also at `/logout`)
- **Description**: User authentication
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Response** (login/signup success):
  ```json
  { "message": "Login successful", "username": "string" }
  ```

### Profiles
- **POST** `/api/profile`
  - Create or update a profile
  - Request body:
    ```json
    {
      "candidate_id": "optional string",
      "name": "string",
      "education_level": "Undergraduate|Postgraduate|Diploma|Other",
      "field_of_study": "string",
      "location_preference": "City name",
      "skills_possessed": ["python", "sql"],
      "sector_interests": ["Technology", "Finance"]
    }
    ```
  - Response (created/updated):
    ```json
    { "message": "Profile created.", "candidate": { "candidate_id": "CAND_xxxx", "name": "...", "skills_possessed": ["..."] } }
    ```

- **GET** `/api/profile/{candidate_id}`
  - Retrieve profile by candidate ID
  - Response:
    ```json
    { "profile": { "candidate_id": "CAND_xxxx", "name": "..." } }
    ```

- **GET** `/api/profiles/by_username/{username}`
  - Retrieve profile by username (case-insensitive)

### Internships
- **GET** `/api/internships`
- **Description**: Get all available internships
- **Response**:
  ```json
  { "internships": [ { "internship_id": "INT001", "title": "...", "skills_required": ["..."] } ] }
  ```

### Recommendations
- **GET** `/api/recommendations/{candidate_id}`
- **Description**: Get internship recommendations for a candidate
- **Parameters**:
  - `candidate_id`: Unique identifier for the candidate
- **Response**:
  ```json
  {
    "candidate": "Name",
    "candidate_id": "CAND_xxxx",
    "recommendations": [
      { "internship_id": "INT001", "title": "...", "match_score": 87.5, "location": "...", "organization": "..." }
    ]
  }
  ```

- **GET** `/api/recommendations/by_internship/{internship_id}`
  - Description: Get internships similar to the given internship
  - Response:
    ```json
    {
      "base_internship": "Title",
      "recommendations": [ { "internship_id": "INT002", "match_score": 76.0 } ]
    }
    ```

## Error Responses

Common error shapes returned by endpoints:

```json
{ "error": "Message", "status_code": 404 }
```

or standardized helper format:

```json
{ "success": false, "message": "Message", "status_code": 400, "timestamp": "..." }
```

### Common Error Codes
- `VALIDATION_ERROR` (400): Invalid request data
- `NOT_FOUND` (404): Resource not found
- `INTERNAL_ERROR` (500): Server error
- `DATABASE_ERROR` (503): Database connection issues

## Rate Limiting
- Defaults suitable for local development. Add reverse proxy or API gateway limits for production.

## Data Formats
- All requests and responses use JSON
- Dates are in ISO 8601 format
- Responses may be in a minimal shape for legacy compatibility or standardized via helpers