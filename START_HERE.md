# 🌱 Welcome to Remedi!

**Your AI-Powered Nutrition Assistant**

This is a complete, production-ready mobile app with gorgeous professional design. Follow this guide to get it running on your iPhone in 15 minutes!

---

## 🎨 What Is Remedi?

Remedi is a beautiful nutrition app that helps you:

1. **🗺️ Find Food** - Locate nearby shelters, kitchens, and food banks
2. **🔍 Analyze Health** - Get AI-powered natural food remedies for health concerns
3. **🏆 Track Progress** - Set goals, earn badges, and track your nutrition journey

---

## ✨ Design Highlights

- **Premium UI** - Multi-million dollar company quality design
- **Green/White Theme** - Professional and calming color scheme
- **Smooth Animations** - Delightful micro-interactions throughout
- **Story-Driven Onboarding** - Duolingo-style warm welcome experience
- **Gorgeous Gradients** - Beautiful depth and shadows everywhere

---

## 🚀 Quick Start

### 1. **Read SETUP_GUIDE.md** 📖
Complete step-by-step instructions for Windows, Mac, and Linux

### 2. **Install Prerequisites** 💻
- Python 3.11
- Node.js 18+
- Expo Go app on iPhone

### 3. **Start Backend** 🐍
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 4. **Configure IP Address** 🌐
Edit `mobile/services/api.js` with your computer's IP

### 5. **Start Mobile App** 📱
```bash
cd mobile
npm install
npx expo start
```

### 6. **Scan QR Code** 📷
Open Expo Go on iPhone and scan the QR code

---

## 📁 Project Structure

```
nutrition-app/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # Main API server
│   ├── database.py         # DynamoDB configuration
│   ├── models.py           # Data models
│   ├── auth.py             # Authentication
│   ├── services/           # Business logic
│   └── routes/             # API endpoints
│
├── mobile/                  # React Native mobile app
│   ├── App.js              # Main app component
│   ├── screens/            # All app screens
│   ├── services/           # API client
│   ├── theme/              # Colors and styles
│   └── utils/              # Animations and utilities
│
└── docs/                    # Documentation
    ├── SETUP_GUIDE.md      # Complete setup instructions
    ├── API_DOCUMENTATION.md # API reference
    └── DEPLOYMENT.md       # Production deployment guide
```

---

## 🎯 Features Implemented

### ✅ Backend (Python/FastAPI)
- JWT authentication
- AWS DynamoDB integration
- OpenAI GPT-4 Vision for health analysis
- FDA FoodData Central API integration
- OpenStreetMap location search
- Gamification system (streaks, badges, goals)
- User profile management

### ✅ Mobile App (React Native)
- Beautiful onboarding (4 screens)
- Story-driven user setup (6 screens)
- Home dashboard with streak tracking
- Location finder with map
- Health analysis with camera
- Goals and achievements
- Premium animations throughout

---

## 🔑 Configuration

### Required (Already Set):
- ✅ AWS DynamoDB credentials (in `.env`)
- ✅ FDA API key (in `.env`)

### Optional:
- ⚠️ OpenAI API key (needed for full health analysis)
  - Get from: https://platform.openai.com/api-keys
  - Add to `backend/.env`

---

## 🎨 Design System

### Colors:
- **Primary Green:** #bdf0cb (your requested color)
- **Dark Green:** #4CAF50
- **White:** #FFFFFF
- **Gradients:** Smooth green-to-white transitions

### Typography:
- **Headers:** 32-40px, bold
- **Body:** 16px, regular
- **Small:** 12-14px, medium

### Spacing:
- Consistent 8px grid system
- Generous padding for breathing room

### Shadows:
- Subtle depth on all cards
- Elevation for interactive elements

---

## 📱 User Flow

1. **First Launch** → Onboarding (4 screens)
2. **Sign Up** → Story-driven setup (6 screens)
3. **Main App** → Home dashboard
4. **Features:**
   - Find Food → Map with filters
   - Health → Camera or text input → AI analysis
   - Goals → Create goals, track progress, earn badges

---

## 🛠️ Tech Stack

**Mobile:**
- React Native (JavaScript)
- Expo
- React Navigation
- Expo Linear Gradient
- Expo Image Picker
- Expo Location

**Backend:**
- Python 3.11
- FastAPI
- AWS DynamoDB
- OpenAI API
- FDA FoodData Central API
- OpenStreetMap/Overpass API

---

## 📊 What's Included

- ✅ Complete source code
- ✅ All dependencies listed
- ✅ AWS credentials configured
- ✅ Comprehensive documentation
- ✅ Setup guides for all platforms
- ✅ API documentation
- ✅ Deployment guide
- ✅ Professional UI/UX design
- ✅ Smooth animations
- ✅ Error handling
- ✅ Loading states
- ✅ Form validation

---

## 🎓 Next Steps After Testing

1. **Test All Features** - Go through each screen
2. **Add OpenAI Key** - For full health analysis
3. **Deploy Backend** - AWS EC2, DigitalOcean, or Heroku
4. **Build for Production** - `expo build:ios`
5. **Submit to App Store** - Apple Developer account required ($99/year)

---

## 💡 Pro Tips

- Keep both terminals open while testing
- Shake iPhone to access developer menu
- Press 'r' in Expo terminal to reload app
- Check backend logs for debugging
- Use real device for best performance

---

## 📞 Troubleshooting

**Can't connect to backend?**
- Verify IP address in `api.js`
- Check both devices on same WiFi
- Ensure backend is running

**Module errors?**
```bash
cd mobile && rm -rf node_modules && npm install
```

**Python errors?**
```bash
cd backend && pip install -r requirements.txt
```

---

## 🎉 You're Ready!

Everything is set up and ready to go. Just follow **SETUP_GUIDE.md** for detailed instructions.

Your Remedi app features:
- ✨ Gorgeous professional design
- 🎭 Smooth animations
- 🌱 Green/white aesthetic
- 📱 Production-ready code
- 🚀 Ready for App Store

**Let's get started!** 🌟

---

**Questions? Check the other documentation files:**
- `SETUP_GUIDE.md` - Detailed setup instructions
- `API_DOCUMENTATION.md` - API reference
- `DEPLOYMENT.md` - Production deployment
- `QUICKSTART.md` - 10-minute quick start

**Built with ❤️ for your nutrition journey**
