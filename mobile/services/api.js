import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Update this to your backend URL when deployed
// For local testing, use your computer's IP address (not localhost)
const API_BASE_URL = 'http://192.168.1.169:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  signup: async (signupData) => {
    console.log('Sending signup data:', JSON.stringify(signupData, null, 2));
    const response = await api.post('/auth/signup', signupData);
    return response.data;
  },

  login: async (username, password) => {
    const response = await api.post('/auth/login', {
      username,
      password,
    });
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/auth/profile');
    return response.data;
  },

  updateDietaryPreferences: async (preferences) => {
    const response = await api.put('/auth/dietary-preferences', preferences);
    return response.data;
  },
};

// Health API
export const healthAPI = {
  analyzeHealthConcern: async (imageBase64, textDescription, userConcerns, allergies = [], dietType = '') => {
    const response = await api.post('/health/analyze', {
      imageBase64,
      textDescription,
      userConcerns,
      allergies,
      dietType,
    });
    return response.data;
  },

  saveRemedy: async (remedyData) => {
    const response = await api.post('/health/save-remedy', remedyData);
    return response.data;
  },

  getSavedRemedies: async () => {
    const response = await api.get('/health/saved-remedies');
    return response.data;
  },
};

// Location API
export const locationAPI = {
  searchLocations: async (latitude, longitude, radius, types) => {
    const params = new URLSearchParams({
      latitude: latitude.toString(),
      longitude: longitude.toString(),
      radius: radius.toString(),
    });
    
    if (types) {
      params.append('types', types.join(','));
    }
    
    const response = await api.get(`/locations/search?${params.toString()}`);
    return response.data;
  },

  saveLocation: async (locationData) => {
    const response = await api.post('/locations/save', locationData);
    return response.data;
  },

  getSavedLocations: async () => {
    const response = await api.get('/locations/saved');
    return response.data;
  },

  deleteSavedLocation: async (locationId) => {
    const response = await api.delete(`/locations/saved/${locationId}`);
    return response.data;
  },
};

// Gamification API
export const gamificationAPI = {
  checkIn: async () => {
    const response = await api.post('/gamification/check-in');
    return response.data;
  },

  getStreak: async () => {
    const response = await api.get('/gamification/streak');
    return response.data;
  },

  getMilestones: async () => {
    const response = await api.get('/gamification/streak/milestones');
    return response.data;
  },

  useStreakFreeze: async () => {
    const response = await api.post('/gamification/streak/use-freeze');
    return response.data;
  },

  getBadges: async () => {
    const response = await api.get('/gamification/badges');
    return response.data;
  },

  getAvailableBadges: async () => {
    const response = await api.get('/gamification/badges/available');
    return response.data;
  },

  createGoal: async (title, description, targetDays) => {
    const response = await api.post('/gamification/goals', {
      title,
      description,
      targetDays,
    });
    return response.data;
  },

  updateGoalProgress: async (goalId) => {
    const response = await api.put(`/gamification/goals/${goalId}/progress`);
    return response.data;
  },

  deleteGoal: async (goalId) => {
    const response = await api.delete(`/gamification/goals/${goalId}`);
    return response.data;
  },

  getGoals: async () => {
    const response = await api.get('/gamification/goals');
    return response.data;
  },

  // XP System
  getXP: async () => {
    const response = await api.get('/gamification/xp');
    return response.data;
  },

  getXPHistory: async () => {
    const response = await api.get('/gamification/xp/history');
    return response.data;
  },

  awardXP: async (action, amount = null) => {
    const response = await api.post('/gamification/xp/award', {
      action,
      amount,
    });
    return response.data;
  },

  // AI Goal Generation
  generateGoals: async () => {
    const response = await api.post('/gamification/goals/generate');
    return response.data;
  },
};

// Image API for dynamic food images
export const imageAPI = {
  getFoodImage: async (foodName, size = 'medium') => {
    const response = await api.get('/images/food', {
      params: { name: foodName, size }
    });
    return response.data;
  },

  getFoodImagesBatch: async (foods, size = 'medium') => {
    const response = await api.post('/images/food/batch', foods, {
      params: { size }
    });
    return response.data;
  },
};

export default api;
