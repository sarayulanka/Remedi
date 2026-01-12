# API Documentation

Base URL: `http://localhost:8000`

Interactive API Documentation: `http://localhost:8000/docs`

## Authentication

All endpoints except `/auth/signup` and `/auth/login` require authentication.

**Authentication Header:**
```
Authorization: Bearer <access_token>
```

---

## Endpoints

### Authentication

#### POST /auth/signup
Register a new user.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123",
  "fullName": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe"
}
```

#### POST /auth/login
Login an existing user.

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe"
}
```

#### GET /auth/profile
Get current user's profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "fullName": "John Doe",
  "dietaryPreferences": {
    "allergies": ["peanuts", "shellfish"],
    "dietType": "vegetarian",
    "restrictions": ["gluten"],
    "preferences": ["organic"]
  },
  "createdAt": "2024-12-20T12:00:00.000Z",
  "updatedAt": "2024-12-20T12:00:00.000Z"
}
```

#### PUT /auth/dietary-preferences
Update user's dietary preferences.

**Request Body:**
```json
{
  "allergies": ["peanuts", "shellfish"],
  "dietType": "vegetarian",
  "restrictions": ["gluten"],
  "preferences": ["organic", "local"]
}
```

**Response:**
```json
{
  "message": "Dietary preferences updated successfully"
}
```

---

### Health Analysis

#### POST /health/analyze
Analyze a health concern using image and/or text description.

**Request Body:**
```json
{
  "imageBase64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "textDescription": "I have a red, itchy rash on my arm",
  "userConcerns": "It's been there for 3 days and getting worse"
}
```

**Response:**
```json
{
  "condition": {
    "name": "Skin Rash",
    "type": "rash",
    "explanation": "Based on your description, this appears to be a common skin rash. It could be caused by various factors including allergies, irritants, or environmental factors. The redness and itching suggest inflammation.",
    "severity": "mild"
  },
  "remedy": {
    "recommendedNutrients": ["Vitamin C", "Vitamin E", "Quercetin", "Omega-3"],
    "foodCategories": ["berries", "nuts", "onions", "fish"],
    "specificFoods": [
      {
        "name": "Strawberries, raw",
        "fdcId": 167762,
        "keyNutrients": [
          {
            "name": "Vitamin C",
            "amount": 58.8,
            "unit": "mg"
          }
        ],
        "beneficialFor": ["Vitamin C"]
      }
    ],
    "explanation": "For Skin Rash, your body benefits from nutrients like Vitamin C, Vitamin E, Quercetin, Omega-3. These nutrients help because they: Support your immune system and natural healing, Reduce inflammation in the body..."
  },
  "disclaimer": "This information is for educational purposes only..."
}
```

#### POST /health/save-remedy
Save a remedy to user's collection.

**Request Body:**
```json
{
  "condition": "Skin Rash",
  "conditionExplanation": "Common skin rash with redness and itching",
  "remedy": {
    "recommendedNutrients": ["Vitamin C", "Vitamin E"],
    "foodCategories": ["berries", "nuts"],
    "specificFoods": [...],
    "explanation": "..."
  },
  "imageUrl": "file:///path/to/image.jpg"
}
```

**Response:**
```json
{
  "remedyId": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Remedy saved successfully"
}
```

#### GET /health/saved-remedies
Get all saved remedies for the current user.

**Response:**
```json
[
  {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "dataType": "SAVED_REMEDY#123e4567-e89b-12d3-a456-426614174000",
    "remedyId": "123e4567-e89b-12d3-a456-426614174000",
    "condition": "Skin Rash",
    "conditionExplanation": "...",
    "remedy": {...},
    "imageUrl": "...",
    "savedAt": "2024-12-20T12:00:00.000Z"
  }
]
```

---

### Locations

#### GET /locations/search
Search for food locations near a coordinate.

**Query Parameters:**
- `latitude` (required): User's latitude
- `longitude` (required): User's longitude
- `radius` (optional): Search radius in meters (default: 5000)
- `types` (optional): Comma-separated location types (e.g., "food_bank,shelter")

**Example:**
```
GET /locations/search?latitude=40.7128&longitude=-74.0060&radius=5000&types=food_bank,shelter
```

**Response:**
```json
[
  {
    "id": "12345",
    "name": "Community Food Bank",
    "type": "food_bank",
    "latitude": 40.7130,
    "longitude": -74.0065,
    "address": "123 Main St, New York, NY 10001",
    "phone": "+1-555-0100",
    "website": "https://example.com",
    "hours": "Mo-Fr 09:00-17:00",
    "description": "Provides food assistance to families in need",
    "wheelchair_accessible": true,
    "dietary_options": ["vegetarian", "halal"]
  }
]
```

#### POST /locations/save
Save a location to user's collection.

**Request Body:**
```json
{
  "name": "Community Food Bank",
  "address": "123 Main St, New York, NY 10001",
  "latitude": 40.7130,
  "longitude": -74.0065,
  "type": "food_bank",
  "hours": "Mo-Fr 09:00-17:00",
  "phone": "+1-555-0100"
}
```

**Response:**
```json
{
  "locationId": "789e0123-e89b-12d3-a456-426614174000",
  "message": "Location saved successfully"
}
```

#### GET /locations/saved
Get all saved locations for the current user.

**Response:**
```json
[
  {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "dataType": "SAVED_LOCATION#789e0123-e89b-12d3-a456-426614174000",
    "locationId": "789e0123-e89b-12d3-a456-426614174000",
    "name": "Community Food Bank",
    "address": "123 Main St, New York, NY 10001",
    "latitude": "40.7130",
    "longitude": "-74.0065",
    "type": "food_bank",
    "hours": "Mo-Fr 09:00-17:00",
    "phone": "+1-555-0100",
    "savedAt": "2024-12-20T12:00:00.000Z"
  }
]
```

#### DELETE /locations/saved/{location_id}
Delete a saved location.

**Response:**
```json
{
  "message": "Location deleted successfully"
}
```

---

### Gamification

#### POST /gamification/check-in
Record a daily check-in.

**Response:**
```json
{
  "message": "Check-in successful",
  "currentStreak": 5,
  "longestStreak": 10,
  "newBadges": [
    {
      "badgeId": "week_warrior",
      "name": "Week Warrior",
      "description": "Maintained a 7-day streak",
      "icon": "⭐",
      "requirement": 7
    }
  ]
}
```

#### GET /gamification/streak
Get current streak information.

**Response:**
```json
{
  "currentStreak": 5,
  "longestStreak": 10,
  "lastCheckIn": "2024-12-20T12:00:00.000Z"
}
```

#### GET /gamification/badges
Get all earned badges.

**Response:**
```json
[
  {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "dataType": "BADGE#first_day",
    "badgeId": "first_day",
    "name": "First Step",
    "description": "Started your nutrition journey",
    "icon": "🌱",
    "earnedAt": "2024-12-20T12:00:00.000Z"
  }
]
```

#### GET /gamification/badges/available
Get all available badges.

**Response:**
```json
[
  {
    "badgeId": "first_day",
    "name": "First Step",
    "description": "Started your nutrition journey",
    "icon": "🌱",
    "requirement": 1
  },
  {
    "badgeId": "week_warrior",
    "name": "Week Warrior",
    "description": "Maintained a 7-day streak",
    "icon": "⭐",
    "requirement": 7
  }
]
```

#### POST /gamification/goals
Create a new nutrition goal.

**Request Body:**
```json
{
  "title": "Eat 5 servings of vegetables daily",
  "description": "Focus on leafy greens and colorful vegetables",
  "targetDays": 30
}
```

**Response:**
```json
{
  "goalId": "456e7890-e89b-12d3-a456-426614174000",
  "message": "Goal created successfully"
}
```

#### PUT /gamification/goals/{goal_id}/progress
Update progress on a goal.

**Response:**
```json
{
  "message": "Progress updated",
  "currentDays": 15,
  "targetDays": 30,
  "completed": false
}
```

#### GET /gamification/goals
Get all goals.

**Response:**
```json
[
  {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "dataType": "GOAL#456e7890-e89b-12d3-a456-426614174000",
    "goalId": "456e7890-e89b-12d3-a456-426614174000",
    "title": "Eat 5 servings of vegetables daily",
    "description": "Focus on leafy greens and colorful vegetables",
    "targetDays": 30,
    "currentDays": 15,
    "completed": false,
    "createdAt": "2024-12-20T12:00:00.000Z",
    "completedAt": ""
  }
]
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

---

## Rate Limiting

Currently, there are no rate limits implemented. Consider adding rate limiting in production using:
- FastAPI middleware
- Nginx rate limiting
- API Gateway rate limiting

---

## CORS

CORS is currently configured to allow all origins (`*`). In production, update to allow only your mobile app's domain.

---

## Testing the API

### Using curl

```bash
# Signup
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# Get profile (replace TOKEN with actual token)
curl -X GET http://localhost:8000/auth/profile \
  -H "Authorization: Bearer TOKEN"
```

### Using the Interactive Docs

Visit `http://localhost:8000/docs` for an interactive API documentation where you can:
- View all endpoints
- Test endpoints directly in the browser
- See request/response schemas
- Authenticate and test protected endpoints

---

## Data Models

### User Profile
- `userId`: UUID
- `username`: String (unique)
- `email`: String
- `fullName`: String (optional)
- `dietaryPreferences`: Object (optional)
- `createdAt`: ISO timestamp
- `updatedAt`: ISO timestamp

### Dietary Preferences
- `allergies`: Array of strings
- `dietType`: String (vegetarian, vegan, keto, etc.)
- `restrictions`: Array of strings
- `preferences`: Array of strings

### Streak
- `currentStreak`: Integer
- `longestStreak`: Integer
- `lastCheckIn`: ISO timestamp

### Badge
- `badgeId`: String
- `name`: String
- `description`: String
- `icon`: Emoji string
- `earnedAt`: ISO timestamp

### Goal
- `goalId`: UUID
- `title`: String
- `description`: String
- `targetDays`: Integer
- `currentDays`: Integer
- `completed`: Boolean
- `createdAt`: ISO timestamp
- `completedAt`: ISO timestamp (optional)

### Location
- `id`: String
- `name`: String
- `type`: String (food_bank, soup_kitchen, shelter)
- `latitude`: Float
- `longitude`: Float
- `address`: String
- `phone`: String (optional)
- `hours`: String (optional)
- `website`: String (optional)

---

## Best Practices

1. **Always include error handling** in your client code
2. **Store tokens securely** (use AsyncStorage on mobile)
3. **Refresh tokens** when they expire
4. **Validate input** before sending to API
5. **Handle network errors** gracefully
6. **Implement retry logic** for failed requests
7. **Cache responses** when appropriate
8. **Log errors** for debugging
