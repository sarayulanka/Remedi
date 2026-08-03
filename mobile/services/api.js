import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_GATEWAY_URL = 'https://32udej7tm4.execute-api.us-east-1.amazonaws.com/dev';

const api = axios.create({
  baseURL: API_GATEWAY_URL,
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

// Handle API Gateway responses where body may be a JSON string
api.interceptors.response.use(
  (response) => {
    if (typeof response.data === 'string') {
      try {
        response.data = JSON.parse(response.data);
      } catch (e) {
        // Not JSON, leave as-is
      }
    }
    return response;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Helper to get stored user_id for path parameters
const getUserId = async () => {
  const userId = await AsyncStorage.getItem('userId');
  if (!userId) throw new Error('Not logged in');
  return userId;
};

// Transform snake_case goal from Lambda to camelCase for screens
const transformGoal = (goal) => ({
  ...goal,
  goalId: goal.goal_id || goal.goalId,
  targetDays: parseInt(goal.target_days || goal.targetDays || 0),
  currentDays: parseInt(goal.completed_days || goal.currentDays || 0),
  completed: (goal.status === 'COMPLETED'),
});

// Auth API
export const authAPI = {
  signup: async (signupData) => {
    const email = signupData.email.trim().toLowerCase();

    try {
      // Create user via POST /users (returns token directly)
      const createResponse = await api.post('/users', {
        email: signupData.email,
        username: signupData.username,
        password: signupData.password,
        first_name: signupData.fullName?.split(' ')[0] || signupData.first_name || '',
        last_name: signupData.fullName?.split(' ').slice(1).join(' ') || signupData.last_name || '',
        nutrition_goals: signupData.nutrition_goals || signupData.nutritionGoals || [],
        food_allergies: signupData.food_allergies || signupData.allergies || [],
        diet_type: signupData.diet_type || signupData.dietType || '',
      });

      return createResponse.data;
    } catch (err) {
      // If account already exists (e.g. previous failed attempt), fall back to login
      if (err.response && err.response.status === 409) {
        const loginResponse = await api.post(`/users/${encodeURIComponent(email)}/login`, {
          password: signupData.password,
        });
        return loginResponse.data;
      }
      throw err;
    }
  },

  login: async (email, password) => {
    const response = await api.post(`/users/${encodeURIComponent(email.trim().toLowerCase())}/login`, {
      password,
    });
    return response.data;
  },

  getProfile: async () => {
    const userId = await getUserId();
    const response = await api.get(`/users/${userId}`);
    return response.data.user || response.data;
  },

  updateProfile: async (data) => {
    const userId = await getUserId();
    const response = await api.put(`/users/${userId}`, data);
    return response.data;
  },

  updateDietaryPreferences: async ({ preferences, allergies, dietType }) => {
    const userId = await getUserId();
    const response = await api.put(`/users/${userId}`, {
      nutrition_goals: preferences,
      food_allergies: allergies,
      diet_type: dietType,
    });
    return response.data;
  },

  deleteAccount: async () => {
    const userId = await getUserId();
    const response = await api.delete(`/users/${userId}`);
    return response.data;
  },

  listUsers: async (limit = 20) => {
    const response = await api.get('/users', { params: { limit } });
    return response.data;
  },
};

// Health API
export const healthAPI = {
  analyzeHealthConcern: async (imageBase64, textDescription, userConcerns, allergies = [], dietType = '') => {
    if (imageBase64) {
      const response = await api.post('/recipes/scan', {
        image_base64: imageBase64,
        text_description: textDescription || '',
        user_concerns: userConcerns || '',
        allergies,
        diet_type: dietType,
      });
      return response.data;
    } else {
      const response = await api.post('/recipes/search', {
        text_description: textDescription || '',
        user_concerns: userConcerns || '',
        allergies,
        diet_type: dietType,
      });
      return response.data;
    }
  },

};

// Gamification API
export const gamificationAPI = {
  checkIn: async () => {
    const userId = await getUserId();
    const response = await api.post(`/users/${userId}/checkin`);
    return response.data;
  },

  getStreak: async () => {
    const userId = await getUserId();
    const response = await api.get(`/users/${userId}/streak`);
    return response.data;
  },

  getMilestones: async () => {
    const userId = await getUserId();
    const response = await api.get(`/users/${userId}/streak/milestones`);
    return response.data;
  },

  useStreakFreeze: async () => {
    const userId = await getUserId();
    const response = await api.post(`/users/${userId}/streak/freeze`);
    return response.data;
  },

  getBadges: async () => {
    const userId = await getUserId();
    const response = await api.get(`/users/${userId}/badges`);
    return response.data;
  },

  getAvailableBadges: async () => {
    const response = await api.get('/badges/available');
    return response.data;
  },

  createGoal: async (title, description, targetDays) => {
    const userId = await getUserId();
    const response = await api.post(`/users/${userId}/goals`, {
      title,
      description,
      target_days: targetDays,
    });
    return response.data;
  },

  getGoals: async () => {
    const userId = await getUserId();
    const response = await api.get(`/users/${userId}/goals`);
    const data = response.data;
    const goals = data.goals || data;
    return Array.isArray(goals) ? goals.map(transformGoal) : [];
  },

  updateGoalProgress: async (goalId) => {
    const userId = await getUserId();
    // First get the current goal to know completed_days
    const getResp = await api.get(`/users/${userId}/goals/${encodeURIComponent(goalId)}`);
    const current = getResp.data;
    const currentDays = parseInt(current.completed_days || current.currentDays || 0);
    const targetDays = parseInt(current.target_days || current.targetDays || 0);
    const today = new Date().toISOString().split('T')[0];

    // Check if already updated today
    if (current.last_progress_date === today) {
      return { alreadyUpdated: true };
    }

    const newDays = currentDays + 1;
    const response = await api.put(`/users/${userId}/goals/${encodeURIComponent(goalId)}`, {
      completed_days: newDays,
      last_progress_date: today,
    });
    const updated = response.data;
    const newlyCompleted = (updated.status === 'COMPLETED');

    return {
      alreadyUpdated: false,
      newlyCompleted,
      currentDays: newDays,
      targetDays,
    };
  },

  deleteGoal: async (goalId) => {
    const userId = await getUserId();
    const response = await api.delete(`/users/${userId}/goals/${encodeURIComponent(goalId)}`);
    return response.data;
  },

  generateGoals: async () => {
    const userId = await getUserId();
    const response = await api.post(`/users/${userId}/goals/generate`);
    return response.data;
  },

  // XP System
  getXP: async () => {
    const userId = await getUserId();
    const response = await api.get(`/users/${userId}/xp`);
    return response.data;
  },

  getXPHistory: async () => {
    const userId = await getUserId();
    const response = await api.get(`/users/${userId}/xp/history`);
    return response.data;
  },

  awardXP: async (action, amount = null) => {
    const userId = await getUserId();
    const response = await api.post(`/users/${userId}/xp/award`, {
      action,
      amount,
    });
    return response.data;
  },
};

// Activity API for tracking user activity
export const activityAPI = {
  logActivity: async (apiEndpoint, httpMethod, responseStatus = null, sessionId = null) => {
    const userId = await getUserId();
    const response = await api.post(`/users/${userId}/activity`, {
      api_endpoint: apiEndpoint,
      http_method: httpMethod,
      response_status: responseStatus,
      session_id: sessionId,
    });
    return response.data;
  },

  getActivity: async (startDate = null, endDate = null, limit = 50) => {
    const userId = await getUserId();
    const params = { limit };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await api.get(`/users/${userId}/activity`, { params });
    return response.data;
  },

  getActivityById: async (activityId) => {
    const userId = await getUserId();
    const response = await api.get(`/users/${userId}/activity/${encodeURIComponent(activityId)}`);
    return response.data;
  },

  deleteActivity: async (activityId) => {
    const userId = await getUserId();
    const response = await api.delete(`/users/${userId}/activity/${encodeURIComponent(activityId)}`);
    return response.data;
  },
};

// Image API for dynamic food images
export const imageAPI = {
  getFoodImage: async (foodName, size = 'medium') => {
    const response = await api.get('/images/food', {
      params: { name: foodName, size },
    });
    return response.data;
  },

  getFoodImagesBatch: async (foods, size = 'medium') => {
    const response = await api.post('/images/food/batch', foods, {
      params: { size },
    });
    return response.data;
  },
};

export default api;
