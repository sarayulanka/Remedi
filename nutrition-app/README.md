# Nutrition Assistant Mobile App

A comprehensive mobile nutrition assistant app built with React Native (Expo) and Python (FastAPI) backend, featuring AI-powered health analysis, location finder, and gamification.

## Features

### 1. 🏠 Home Dashboard
- Daily check-in system with streak tracking
- Badge display and achievements
- Quick access to all features

### 2. 📍 Location Finder
- Find nearby food banks, soup kitchens, and shelters
- Filter by location type and dietary preferences
- Integration with OpenStreetMap (Overpass API)
- Save favorite locations
- Get directions via Google Maps

### 3. 🔍 Health Analysis
- Take photos or describe health concerns
- AI-powered analysis using OpenAI GPT-4 Vision
- Natural food remedies backed by FDA FoodData Central database
- Simple explanations of conditions
- Save remedies for future reference

### 4. 🏆 Goals & Gamification
- Set nutrition goals with target days
- Track progress with visual progress bars
- Earn badges for achievements
- Streak system to maintain consistency

## Tech Stack

### Backend
- **Python 3.11** with FastAPI
- **AWS DynamoDB** for data storage
- **OpenAI GPT-4 Vision** for health analysis
- **FDA FoodData Central API** for nutritional data
- **OpenStreetMap Overpass API** for location search

### Mobile App
- **React Native** with Expo
- **JavaScript** (no TypeScript)
- **React Navigation** for routing
- **Expo Linear Gradient** for beautiful UI
- **Expo Image Picker** for camera/gallery access
- **Expo Location** for geolocation

## Project Structure

```
nutrition-app/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # DynamoDB configuration
│   ├── auth.py                 # Authentication utilities
│   ├── models.py               # Pydantic models
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables
│   ├── routes/
│   │   ├── auth_routes.py      # Authentication endpoints
│   │   ├── health_routes.py    # Health analysis endpoints
│   │   ├── location_routes.py  # Location search endpoints
│   │   └── gamification_routes.py  # Gamification endpoints
│   └── services/
│       ├── user_service.py     # User management logic
│       ├── health_service.py   # Health analysis logic
│       ├── fda_service.py      # FDA API integration
│       ├── location_service.py # Location search logic
│       └── gamification_service.py  # Gamification logic
└── mobile/
    ├── App.js                  # Main app component
    ├── package.json            # Node dependencies
    ├── screens/
    │   ├── OnboardingScreen.js # Onboarding flow
    │   ├── AuthScreen.js       # Login/Signup
    │   ├── HomeScreen.js       # Dashboard
    │   ├── LocationsScreen.js  # Location finder
    │   ├── HealthScreen.js     # Health analysis
    │   └── GoalsScreen.js      # Goals & badges
    ├── services/
    │   └── api.js              # API client
    └── theme/
        └── colors.js           # Color scheme
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- AWS Account with DynamoDB access
- OpenAI API key
- FDA FoodData Central API key (free)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables in `.env`:
```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=nutrition-users

OPENAI_API_KEY=your_openai_api_key

FDA_API_KEY=your_fda_api_key

JWT_SECRET_KEY=your_secure_random_secret_key

PORT=8000
HOST=0.0.0.0
```

5. Start the backend server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Mobile App Setup

1. Navigate to the mobile directory:
```bash
cd mobile
```

2. Install dependencies:
```bash
npm install
```

3. Update the API URL in `services/api.js`:
   - For local testing on physical device: Use your computer's IP address (e.g., `http://192.168.1.100:8000`)
   - For iOS Simulator: Use `http://localhost:8000`
   - For Android Emulator: Use `http://10.0.2.2:8000`

4. Start the Expo development server:
```bash
npx expo start
```

5. Test the app:
   - **iOS**: Scan QR code with Camera app (requires Expo Go app)
   - **Android**: Scan QR code with Expo Go app
   - **iOS Simulator**: Press `i` in terminal
   - **Android Emulator**: Press `a` in terminal

## Testing with Expo Go

1. Install Expo Go on your iPhone:
   - Download from App Store: [Expo Go](https://apps.apple.com/app/expo-go/id982107779)

2. Ensure your phone and computer are on the same WiFi network

3. Update `services/api.js` with your computer's local IP:
```javascript
const API_BASE_URL = 'http://YOUR_COMPUTER_IP:8000';
```

4. Start the backend server on your computer

5. Start the Expo development server:
```bash
npx expo start
```

6. Scan the QR code with your iPhone Camera app

7. The app will open in Expo Go

## API Endpoints

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/profile` - Get user profile
- `PUT /auth/dietary-preferences` - Update dietary preferences

### Health Analysis
- `POST /health/analyze` - Analyze health concern with image/text
- `POST /health/save-remedy` - Save a remedy
- `GET /health/saved-remedies` - Get saved remedies

### Locations
- `GET /locations/search` - Search nearby food locations
- `POST /locations/save` - Save a location
- `GET /locations/saved` - Get saved locations
- `DELETE /locations/saved/{id}` - Delete saved location

### Gamification
- `POST /gamification/check-in` - Daily check-in
- `GET /gamification/streak` - Get streak info
- `GET /gamification/badges` - Get earned badges
- `GET /gamification/badges/available` - Get all available badges
- `POST /gamification/goals` - Create a goal
- `PUT /gamification/goals/{id}/progress` - Update goal progress
- `GET /gamification/goals` - Get all goals

## Deployment

### Backend Deployment (AWS EC2 or Similar)

1. Set up a server (AWS EC2, DigitalOcean, etc.)
2. Install Python 3.11 and dependencies
3. Configure environment variables
4. Use a process manager like `systemd` or `supervisor`
5. Set up a reverse proxy with Nginx
6. Enable HTTPS with Let's Encrypt

### Mobile App Deployment

#### iOS (App Store)

1. Create an Apple Developer account ($99/year)
2. Build the app:
```bash
expo build:ios
```
3. Submit to App Store via App Store Connect

#### Android (Google Play)

1. Create a Google Play Developer account ($25 one-time)
2. Build the app:
```bash
expo build:android
```
3. Submit to Google Play Console

## Environment Variables

### Backend (.env)
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region (e.g., us-east-1)
- `DYNAMODB_TABLE_NAME` - DynamoDB table name
- `OPENAI_API_KEY` - OpenAI API key
- `FDA_API_KEY` - FDA FoodData Central API key
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 0.0.0.0)

## Design

### Color Scheme
- Primary: `#bdf0cb` (Light green)
- Primary Dark: `#8fd9a3` (Medium green)
- White: `#ffffff`
- Background: `#f8fff9` (Very light green)
- Text: `#2d3436` (Dark gray)
- Text Light: `#636e72` (Medium gray)

### UI Elements
- Gradient backgrounds with green and white
- Rounded corners (15-20px border radius)
- Card-based layouts with shadows
- Emoji icons for visual appeal
- Clean, professional design

## Cost Estimates

### Development & Testing
- **Free**: Expo Go, React Native, Python, OpenStreetMap

### Production (Monthly)
- **AWS DynamoDB**: $0-10 for first 1,000 users (free tier available)
- **OpenAI API**: ~$0.01-0.02 per image analysis
  - 100 users × 1 analysis/day = ~$30/month
  - 1,000 users × 1 analysis/day = ~$300/month
- **Server Hosting**: $5-50/month (AWS EC2, DigitalOcean, etc.)

### One-Time Costs
- **Apple Developer Account**: $99/year
- **Google Play Developer Account**: $25 one-time

## Troubleshooting

### Backend Issues

**DynamoDB Connection Error**
- Verify AWS credentials in `.env`
- Check IAM permissions for DynamoDB access
- Ensure table exists or app can create it

**OpenAI API Error**
- Verify API key is valid
- Check API usage limits
- Ensure sufficient credits

### Mobile App Issues

**Cannot Connect to Backend**
- Verify backend is running
- Check API URL in `services/api.js`
- Ensure phone and computer are on same WiFi
- Try using IP address instead of localhost

**Expo Go Not Loading**
- Clear Expo cache: `npx expo start -c`
- Restart Expo Go app
- Check for JavaScript errors in terminal

**Image Picker Not Working**
- Grant camera/gallery permissions in phone settings
- Restart Expo Go app

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at `http://localhost:8000/docs`
3. Check Expo documentation: https://docs.expo.dev/

## License

This project is for educational and personal use.

## Acknowledgments

- FDA FoodData Central for nutritional data
- OpenStreetMap for location data
- OpenAI for AI capabilities
- Expo team for excellent React Native tooling
