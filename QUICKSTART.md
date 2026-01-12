# Quick Start Guide

Get your Nutrition Assistant app running in 10 minutes!

## Prerequisites

- Python 3.11 installed
- Node.js 18+ installed
- iPhone with Expo Go app installed
- Computer and iPhone on the same WiFi network

## Step 1: Start the Backend (2 minutes)

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

✅ You should see: "API ready!" and "Uvicorn running on http://0.0.0.0:8000"

## Step 2: Get Your Computer's IP Address (1 minute)

### On Mac/Linux:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### On Windows:
```bash
ipconfig
```

Look for something like `192.168.1.100` - this is your IP address.

## Step 3: Configure Mobile App (1 minute)

```bash
# Open the API configuration file
# Navigate to: mobile/services/api.js

# Change this line:
const API_BASE_URL = 'http://localhost:8000';

# To this (use YOUR IP address):
const API_BASE_URL = 'http://192.168.1.100:8000';
```

## Step 4: Start the Mobile App (2 minutes)

```bash
# Navigate to mobile folder
cd mobile

# Install dependencies (first time only)
npm install

# Start Expo
npx expo start
```

✅ You should see a QR code in your terminal

## Step 5: Open on Your iPhone (1 minute)

1. Open the **Camera app** on your iPhone
2. Point it at the QR code on your computer screen
3. Tap the notification that appears
4. The app will open in **Expo Go**

## Step 6: Test the App! (3 minutes)

### First Launch - Onboarding
- Swipe through the beautiful onboarding screens
- Click "Get Started"

### Create Account
- Click "Sign Up" tab
- Enter:
  - Username: `testuser`
  - Email: `test@example.com`
  - Password: `password123`
- Click "Sign Up"

### Test Features

1. **Daily Check-In**:
   - On the home screen, click "Daily Check-In 🔥"
   - Your streak will increase to 1!

2. **Find Locations**:
   - Tap "Locations" at the bottom
   - Grant location permission
   - Select location types
   - Click "Search"
   - View nearby food locations

3. **Health Analysis**:
   - Tap "Health" at the bottom
   - Click "📷 Gallery" or "📸 Camera"
   - Take/select a photo
   - Describe your concern
   - Click "Analyze"
   - View AI-generated remedies

4. **Create Goals**:
   - Tap "Goals" at the bottom
   - Click "+ Add Goal"
   - Enter goal details
   - Click "Create"

## Troubleshooting

### "Cannot connect to backend"

**Solution**: Make sure you updated the API URL with your computer's IP address in `mobile/services/api.js`

### "Network request failed"

**Solutions**:
1. Check that backend is running (you should see logs in the terminal)
2. Make sure phone and computer are on the same WiFi
3. Try restarting the backend server
4. Try restarting Expo with: `npx expo start -c`

### "Location permission denied"

**Solution**: Go to iPhone Settings > Expo Go > Location > "While Using the App"

### "Camera permission denied"

**Solution**: Go to iPhone Settings > Expo Go > Camera > Enable

## What's Next?

### Add Your OpenAI API Key

To use the health analysis feature in production:

1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Open `backend/.env`
3. Replace `your_openai_api_key_here` with your actual key
4. Restart the backend server

### Customize the App

- **Colors**: Edit `mobile/theme/colors.js`
- **Features**: Modify screens in `mobile/screens/`
- **API Logic**: Update services in `backend/services/`

### Deploy to Production

See `DEPLOYMENT.md` for full deployment instructions to:
- AWS EC2 (backend)
- Apple App Store (iOS)
- Google Play Store (Android)

## Need Help?

1. Check the main `README.md` for detailed documentation
2. Review `DEPLOYMENT.md` for production setup
3. Check API documentation at `http://localhost:8000/docs`

## Important Notes

### API Keys Provided

✅ **FDA API Key**: Already configured and working
✅ **AWS DynamoDB**: Already configured with your credentials

⚠️ **OpenAI API Key**: You need to add your own for health analysis feature

### Costs

- **Development/Testing**: FREE
- **Production**: See README.md for cost breakdown

### Security

⚠️ The provided AWS credentials and API keys are in the code for testing. In production:
- Use environment variables
- Rotate keys regularly
- Never commit secrets to Git

Enjoy building your nutrition app! 🌱
