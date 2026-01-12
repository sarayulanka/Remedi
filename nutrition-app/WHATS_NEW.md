# What's New in Remedi

## 🎉 Major Updates

### 1. **Rebranded to "Remedi"**
- App is now called **Remedi** instead of "Nutrition Assistant"
- Updated all branding throughout the app
- New professional identity focused on natural remedies

### 2. **Personalized Onboarding Questionnaire** ✨
When new users sign up, they now go through a beautiful 5-step questionnaire that collects:

#### Step 1: Personal Information
- Full name
- Age (optional)
- Location (optional)

#### Step 2: Demographics
- Gender selection

#### Step 3: Nutrition Goals
Select from multiple goals:
- Weight Management
- Better Energy
- Improved Digestion
- Stronger Immunity
- Better Sleep
- Skin Health
- Heart Health
- Mental Clarity

#### Step 4: Health Conditions
Track existing conditions:
- Diabetes
- High Blood Pressure
- High Cholesterol
- Digestive Issues
- Skin Conditions
- Allergies
- None

#### Step 5: Dietary Preferences
- **Food Allergies**: Peanuts, Tree Nuts, Dairy, Eggs, Soy, Gluten, Fish, Shellfish, None
- **Diet Type**: No Restrictions, Vegetarian, Vegan, Pescatarian, Keto, Paleo, Halal, Kosher

### 3. **Enhanced User Profiles**
All questionnaire data is stored in the user's profile and used to:
- Personalize health recommendations
- Filter food locations by dietary restrictions
- Tailor natural remedy suggestions
- Provide better goal tracking

### 4. **Beautiful UI/UX**
- Progress bar showing questionnaire completion
- Multi-select checkboxes for goals and conditions
- Clean, professional design with green theme
- Smooth navigation between steps

---

## 🔄 Updated Flow

### New User Journey:
1. **Onboarding** → See app features (4 screens)
2. **Sign Up** → Enter username, email, password
3. **Questionnaire** → Answer 5 steps of questions
4. **Profile Creation** → Account created with all data
5. **Main App** → Start using Remedi!

### Returning User Journey:
1. **Login** → Enter credentials
2. **Main App** → Go straight to dashboard

---

## 🗄️ Backend Changes

### Updated Models
- `UserSignup` now includes: age, gender, location, nutritionGoals, healthConditions
- `UserProfile` stores all demographic and preference data
- DynamoDB schema updated to support new fields

### New Screens
- `QuestionnaireScreen.js` - Multi-step form with 5 pages
- `SignupCompleteScreen.js` - Loading screen while creating account

---

## 📱 How to Use

### For New Users:
1. Open the app
2. Tap "Sign Up"
3. Enter basic credentials
4. **NEW**: Complete the 5-step questionnaire
5. Your personalized profile is created!

### For Developers:
All questionnaire data is automatically:
- Validated before submission
- Stored in DynamoDB
- Available via the user profile API
- Used to personalize app features

---

## 🎨 Design Highlights

- **Progress Indicator**: Shows "Step X of 5" with visual progress bar
- **Smart Validation**: Required fields checked before advancing
- **Back Navigation**: Can go back to edit previous answers
- **Responsive**: Works on all screen sizes
- **Accessible**: Clear labels and large touch targets

---

## 🔧 Technical Details

### Files Changed:
- `mobile/App.js` - Added new screens to navigation
- `mobile/screens/AuthScreen.js` - Updated signup flow
- `mobile/screens/QuestionnaireScreen.js` - NEW
- `mobile/screens/SignupCompleteScreen.js` - NEW
- `mobile/screens/OnboardingScreen.js` - Updated branding
- `backend/models.py` - Added new fields
- `backend/services/user_service.py` - Store additional data
- `backend/main.py` - Updated API branding

### Database Schema:
```json
{
  "userId": "uuid",
  "username": "string",
  "email": "string",
  "fullName": "string",
  "age": "number",
  "gender": "string",
  "location": "string",
  "nutritionGoals": ["array"],
  "healthConditions": ["array"],
  "dietaryPreferences": {
    "allergies": ["array"],
    "dietType": "string"
  }
}
```

---

## 🚀 Benefits

### For Users:
- ✅ Personalized experience from day one
- ✅ Better health recommendations
- ✅ Relevant food location filtering
- ✅ Tailored remedy suggestions

### For Developers:
- ✅ Rich user data for analytics
- ✅ Better targeting for features
- ✅ Improved user retention
- ✅ Foundation for ML/AI personalization

---

## 📝 Notes

- All questionnaire fields except name are optional
- Users can skip questions by leaving them unselected
- Data is stored securely in DynamoDB
- Dietary preferences can be updated later in settings
- The questionnaire only appears once during signup

---

## 🎯 Next Steps

After updating to this version:
1. Test the new signup flow
2. Verify questionnaire data is stored correctly
3. Check that dietary preferences are applied
4. Ensure branding is consistent throughout

Enjoy the new **Remedi** experience! 🌱
