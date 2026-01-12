# 🌱 Remedi - Complete Setup Guide

Welcome to **Remedi**, your AI-powered nutrition assistant! This guide will help you get the app running on your iPhone using Expo Go.

---

## 📋 Prerequisites

Before you start, make sure you have:

- ✅ **Windows, Mac, or Linux computer**
- ✅ **Python 3.11** installed
- ✅ **Node.js 18+** installed
- ✅ **iPhone** with Expo Go app installed (free from App Store)
- ✅ **Same WiFi network** for computer and iPhone

---

## 🚀 Quick Start (15 Minutes)

### Step 1: Extract the Project

1. Extract `remedi-app.zip` to your Desktop or Documents folder
2. You should have a folder called `nutrition-app`

### Step 2: Start the Backend

#### On Windows (Command Prompt):

```bash
cd path\to\nutrition-app\backend
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 boto3==1.29.7 python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 python-multipart==0.0.6 requests==2.31.0 openai==1.3.7 pydantic==2.4.2 python-dotenv==1.0.0
python main.py
```

#### On Mac/Linux (Terminal):

```bash
cd path/to/nutrition-app/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 boto3==1.29.7 python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 python-multipart==0.0.6 requests==2.31.0 openai==1.3.7 pydantic==2.4.2 python-dotenv==1.0.0
python main.py
```

✅ **Success:** You should see "Remedi API ready!"

**Keep this terminal window open!**

### Step 3: Get Your Computer's IP Address

#### Windows:
```bash
ipconfig
```
Look for: `IPv4 Address. . . . . . . . . . . : 192.168.X.X`

#### Mac/Linux:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```
Look for: `inet 192.168.X.X`

**Write down your IP address!** (e.g., 192.168.1.100)

### Step 4: Configure Mobile App

1. Open `nutrition-app/mobile/services/api.js` in any text editor
2. Find line 7: `const API_BASE_URL = 'http://localhost:8000';`
3. Replace with your IP: `const API_BASE_URL = 'http://192.168.X.X:8000';`
4. Save the file

### Step 5: Start Mobile App

Open a **NEW** terminal/command prompt:

```bash
cd path/to/nutrition-app/mobile
npm install
npx expo start
```

Wait for the QR code to appear (2-3 minutes first time).

### Step 6: Test on iPhone

1. Open **Expo Go** app on your iPhone
2. Tap **"Scan QR code"**
3. Point camera at the QR code in your terminal
4. Wait for app to load (30-60 seconds first time)

🎉 **You're done!** The app should open on your iPhone!

---

## 🎨 What You'll See

### 1. **Onboarding (4 screens)**
Beautiful intro story about Remedi and your nutrition journey

### 2. **Story-Driven Setup (6 screens)**
- Welcome message
- Name input
- Goals selection
- Allergies (optional)
- Diet type (optional)
- Celebration screen

### 3. **Main App**
- **Home:** Dashboard with streak tracking
- **Find Food:** Map of nearby shelters, kitchens, food banks
- **Health:** AI-powered health analysis with natural remedies
- **Goals:** Track progress, earn badges, set nutrition goals

---

## 🎯 Features

### 🗺️ Location Finder
- Find nearby food banks, shelters, kitchens
- Filter by type, hours, dietary restrictions
- Get directions
- Save favorites

### 🔍 Health Analysis
- Take photo or describe health concern
- AI explains condition in simple terms
- Natural food remedies from FDA database
- Save remedies for later

### 🏆 Gamification
- Track daily streaks
- Earn badges (10 days, 50 days, etc.)
- Set custom nutrition goals
- Progress tracking

---

## 🛠️ Troubleshooting

### "Cannot connect to backend"
- ✅ Make sure backend is running (check terminal)
- ✅ Verify IP address in `api.js` is correct
- ✅ Ensure computer and iPhone are on same WiFi
- ✅ Try restarting both backend and Expo

### "Module not found" errors
```bash
cd mobile
rm -rf node_modules
npm install
```

### "Python package not found"
```bash
cd backend
pip install -r requirements.txt
```

### App won't load on iPhone
- ✅ Make sure Expo Go is updated
- ✅ Try shaking phone and selecting "Reload"
- ✅ Check that QR code is still visible in terminal

---

## 🔑 Optional: Add OpenAI API Key

For full health analysis functionality:

1. Get API key from https://platform.openai.com/api-keys
2. Open `backend/.env`
3. Find: `OPENAI_API_KEY=your_openai_api_key_here`
4. Replace with your actual key
5. Restart backend (Ctrl+C, then `python main.py`)

---

## 📱 Testing Checklist

- [ ] Backend starts without errors
- [ ] Mobile app shows QR code
- [ ] App loads on iPhone
- [ ] Onboarding screens work
- [ ] Can create account
- [ ] Story-driven setup completes
- [ ] Home screen shows username
- [ ] Can find locations
- [ ] Can analyze health concerns
- [ ] Can create goals
- [ ] Streaks update

---

## 🎨 Design Features

- ✨ Premium green/white color scheme
- 🎭 Smooth fade animations
- 💫 Micro-interactions on buttons
- 🌈 Beautiful gradients
- 🎯 Professional shadows and depth
- 📐 Perfect spacing and typography
- 🖼️ Gorgeous card designs

---

## 💡 Tips

- **Keep both terminals open** while testing
- **Shake iPhone** to open developer menu
- **Press 'r' in Expo terminal** to reload app
- **Check backend logs** to see API requests
- **Use real device** for best experience (simulators work but slower)

---

## 🚀 Next Steps

Once you've tested locally:

1. **Deploy Backend** - Use AWS EC2, DigitalOcean, or Heroku
2. **Build for Production** - Run `expo build:ios`
3. **Submit to App Store** - Follow Apple's guidelines
4. **Monitor Usage** - Check AWS costs and API usage

---

## 📞 Need Help?

- Check backend logs for errors
- Verify all prerequisites are installed
- Make sure ports 8000 and 19000 aren't blocked
- Try restarting everything

---

## 🎉 You're Ready!

Your Remedi app is now running! Create an account, explore the features, and start your nutrition journey! 🌱

---

**Built with ❤️ using React Native, FastAPI, AWS DynamoDB, and OpenAI**
