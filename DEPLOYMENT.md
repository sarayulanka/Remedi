# Deployment Guide

## Local Development Setup

### Step 1: Backend Setup

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Create virtual environment**:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
   - Copy `.env.example` to `.env`
   - Fill in your credentials:
     - AWS credentials (already provided)
     - OpenAI API key (you need to add this)
     - FDA API key (already provided)
     - JWT secret (already set, change in production)

5. **Start the backend**:
```bash
python main.py
```

The API will run at `http://localhost:8000`

### Step 2: Mobile App Setup

1. **Navigate to mobile directory**:
```bash
cd mobile
```

2. **Install dependencies**:
```bash
npm install
```

3. **Update API URL**:
   - Open `services/api.js`
   - Find the line: `const API_BASE_URL = 'http://localhost:8000';`
   - For testing on a physical device, replace `localhost` with your computer's IP address
   - To find your IP:
     - **Mac/Linux**: Run `ifconfig | grep "inet " | grep -v 127.0.0.1`
     - **Windows**: Run `ipconfig` and look for IPv4 Address
   - Example: `const API_BASE_URL = 'http://192.168.1.100:8000';`

4. **Start Expo**:
```bash
npx expo start
```

5. **Test on your iPhone**:
   - Install Expo Go from the App Store
   - Make sure your phone and computer are on the same WiFi
   - Scan the QR code with your iPhone Camera app
   - The app will open in Expo Go

## Testing the App

### Test Flow

1. **Onboarding**:
   - First launch shows beautiful onboarding screens
   - Swipe through 4 pages explaining features
   - Click "Get Started"

2. **Sign Up**:
   - Create an account with username, email, and password
   - You'll be automatically logged in

3. **Home Screen**:
   - See your streak (starts at 0)
   - Click "Daily Check-In" to start your streak
   - Explore the three main features

4. **Test Location Finder**:
   - Grant location permission
   - Select location types (food banks, shelters, etc.)
   - Click "Search"
   - View nearby locations
   - Save a location

5. **Test Health Analysis**:
   - Take a photo or upload from gallery
   - Describe your concern
   - Click "Analyze"
   - View AI-generated analysis and food remedies
   - Save the remedy

6. **Test Goals**:
   - Click "Add Goal"
   - Create a nutrition goal
   - Mark days as complete
   - View badges earned

## Production Deployment

### Backend Deployment Options

#### Option 1: AWS EC2

1. **Launch EC2 Instance**:
   - Choose Ubuntu 22.04 LTS
   - t2.micro (free tier) or t2.small
   - Configure security group to allow ports 22 (SSH) and 8000 (API)

2. **Connect and setup**:
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Clone or upload your code
# Upload the backend folder using scp or git

cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
nano .env
# Add your production credentials
```

4. **Install and configure Nginx**:
```bash
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/nutrition-api

# Add this configuration:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable the site
sudo ln -s /etc/nginx/sites-available/nutrition-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

5. **Setup systemd service**:
```bash
sudo nano /etc/systemd/system/nutrition-api.service

# Add this content:
[Unit]
Description=Nutrition Assistant API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/backend
Environment="PATH=/home/ubuntu/backend/venv/bin"
ExecStart=/home/ubuntu/backend/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start the service
sudo systemctl enable nutrition-api
sudo systemctl start nutrition-api
sudo systemctl status nutrition-api
```

6. **Setup HTTPS with Let's Encrypt**:
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

#### Option 2: DigitalOcean App Platform

1. Connect your GitHub repository
2. Select Python as the environment
3. Set environment variables in the dashboard
4. Deploy with one click

#### Option 3: Heroku

1. Install Heroku CLI
2. Create `Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```
3. Deploy:
```bash
heroku create nutrition-assistant-api
git push heroku main
heroku config:set AWS_ACCESS_KEY_ID=your_key
# Set all other environment variables
```

### Mobile App Deployment

#### iOS App Store

1. **Prerequisites**:
   - Apple Developer Account ($99/year)
   - Mac computer (required for iOS builds)

2. **Configure app.json**:
```json
{
  "expo": {
    "name": "Nutrition Assistant",
    "slug": "nutrition-assistant",
    "version": "1.0.0",
    "ios": {
      "bundleIdentifier": "com.yourcompany.nutritionassistant",
      "buildNumber": "1.0.0"
    }
  }
}
```

3. **Build for iOS**:
```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Configure build
eas build:configure

# Build for iOS
eas build --platform ios
```

4. **Submit to App Store**:
```bash
eas submit --platform ios
```

5. **App Store Connect**:
   - Log in to App Store Connect
   - Create a new app
   - Fill in app information
   - Upload screenshots
   - Submit for review

#### Google Play Store

1. **Prerequisites**:
   - Google Play Developer Account ($25 one-time)

2. **Configure app.json**:
```json
{
  "expo": {
    "android": {
      "package": "com.yourcompany.nutritionassistant",
      "versionCode": 1
    }
  }
}
```

3. **Build for Android**:
```bash
eas build --platform android
```

4. **Submit to Google Play**:
```bash
eas submit --platform android
```

5. **Google Play Console**:
   - Create a new app
   - Fill in app details
   - Upload APK/AAB
   - Submit for review

## Update API URL for Production

Before building for production, update the API URL in `mobile/services/api.js`:

```javascript
const API_BASE_URL = 'https://your-production-domain.com';
```

## Environment-Specific Configuration

### Development
```javascript
const API_BASE_URL = __DEV__ 
  ? 'http://YOUR_LOCAL_IP:8000'  // Development
  : 'https://your-production-domain.com';  // Production
```

## Monitoring and Maintenance

### Backend Monitoring

1. **Check logs**:
```bash
# If using systemd
sudo journalctl -u nutrition-api -f

# If using PM2
pm2 logs nutrition-api
```

2. **Monitor DynamoDB**:
   - Check AWS CloudWatch for metrics
   - Monitor read/write capacity
   - Set up billing alerts

3. **Monitor OpenAI Usage**:
   - Check OpenAI dashboard for usage
   - Set up usage alerts

### Mobile App Analytics

Consider adding analytics:
- Firebase Analytics
- Amplitude
- Mixpanel

## Scaling Considerations

### Backend Scaling

1. **Horizontal Scaling**:
   - Use load balancer (AWS ELB, Nginx)
   - Deploy multiple backend instances
   - Use Redis for session management

2. **Database Optimization**:
   - Use DynamoDB auto-scaling
   - Implement caching with Redis
   - Optimize queries

3. **API Optimization**:
   - Implement rate limiting
   - Add response caching
   - Use CDN for static assets

### Cost Optimization

1. **DynamoDB**:
   - Use on-demand pricing for unpredictable traffic
   - Use provisioned capacity for steady traffic
   - Enable auto-scaling

2. **OpenAI API**:
   - Implement caching for similar queries
   - Add rate limiting per user
   - Consider batch processing

3. **Infrastructure**:
   - Use spot instances for non-critical workloads
   - Implement auto-scaling groups
   - Use CloudFront CDN

## Security Checklist

- [ ] Change JWT secret key in production
- [ ] Enable HTTPS for API
- [ ] Implement rate limiting
- [ ] Add input validation
- [ ] Enable CORS only for your domain
- [ ] Use environment variables for all secrets
- [ ] Enable AWS CloudTrail for auditing
- [ ] Implement proper error handling (don't expose stack traces)
- [ ] Add request logging
- [ ] Implement user session management
- [ ] Add API authentication middleware
- [ ] Regular security updates

## Backup Strategy

1. **DynamoDB Backups**:
   - Enable point-in-time recovery
   - Set up automated backups
   - Test restore procedures

2. **Code Backups**:
   - Use Git for version control
   - Regular commits to GitHub/GitLab
   - Tag releases

## Troubleshooting Production Issues

### API Not Responding
```bash
# Check if service is running
sudo systemctl status nutrition-api

# Check logs
sudo journalctl -u nutrition-api -n 100

# Restart service
sudo systemctl restart nutrition-api
```

### High DynamoDB Costs
- Check for inefficient queries
- Implement caching
- Review access patterns
- Consider on-demand vs provisioned capacity

### OpenAI API Errors
- Check API key validity
- Monitor rate limits
- Implement retry logic with exponential backoff
- Add fallback responses

## Support and Maintenance

### Regular Maintenance Tasks
- [ ] Update dependencies monthly
- [ ] Review and rotate API keys quarterly
- [ ] Monitor costs weekly
- [ ] Check error logs daily
- [ ] Update app content as needed
- [ ] Respond to user feedback
- [ ] Test new features in staging

### Emergency Contacts
- AWS Support
- OpenAI Support
- Expo Support
- Apple Developer Support
- Google Play Support
