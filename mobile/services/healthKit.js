import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Note: For full Apple Health integration, you'll need to:
// 1. Install react-native-health: npx expo install react-native-health
// 2. Add HealthKit entitlement to app.json
// 3. Run with expo prebuild or EAS build (not Expo Go)

class HealthKitService {
  constructor() {
    this.isInitialized = false;
    this.isAvailable = Platform.OS === 'ios';
    this.AppleHealthKit = null;
  }

  async initialize() {
    if (!this.isAvailable) {
      console.log('Apple Health is only available on iOS');
      return false;
    }

    try {
      // Dynamic import to prevent errors on Android
      // Uncomment when react-native-health is installed
      // const AppleHealthKit = require('react-native-health').default;
      // this.AppleHealthKit = AppleHealthKit;

      // For now, use mock/demo mode
      console.log('Apple Health Kit initialized (demo mode)');
      this.isInitialized = true;
      return true;
    } catch (error) {
      console.log('Apple Health Kit not available:', error);
      return false;
    }
  }

  async requestPermissions() {
    if (!this.isAvailable) return false;

    const permissions = {
      permissions: {
        read: [
          'Steps',
          'StepCount',
          'DistanceWalkingRunning',
          'ActiveEnergyBurned',
          'Weight',
          'Height',
          'BiologicalSex',
          'DateOfBirth',
          'SleepAnalysis',
          'HeartRate',
          'Water',
          'Fiber',
          'Protein',
          'Carbohydrates',
          'FatTotal',
          'Calcium',
          'Iron',
          'VitaminC',
          'VitaminD',
        ],
        write: [
          'Steps',
          'Water',
        ],
      },
    };

    try {
      // When AppleHealthKit is available:
      // return new Promise((resolve, reject) => {
      //   this.AppleHealthKit.initHealthKit(permissions, (error, results) => {
      //     if (error) {
      //       reject(error);
      //       return;
      //     }
      //     resolve(true);
      //   });
      // });

      // Demo mode - simulate permission granted
      await AsyncStorage.setItem('healthKitConnected', 'true');
      return true;
    } catch (error) {
      console.log('Error requesting HealthKit permissions:', error);
      return false;
    }
  }

  async isConnected() {
    const connected = await AsyncStorage.getItem('healthKitConnected');
    return connected === 'true';
  }

  async disconnect() {
    await AsyncStorage.setItem('healthKitConnected', 'false');
  }

  async getTodaySteps() {
    if (!this.isAvailable) return null;

    const options = {
      startDate: new Date(new Date().setHours(0, 0, 0, 0)).toISOString(),
      endDate: new Date().toISOString(),
    };

    try {
      // When AppleHealthKit is available:
      // return new Promise((resolve, reject) => {
      //   this.AppleHealthKit.getStepCount(options, (err, results) => {
      //     if (err) reject(err);
      //     resolve(results?.value || 0);
      //   });
      // });

      // Demo mode - return random steps
      return Math.floor(Math.random() * 8000) + 2000;
    } catch (error) {
      console.log('Error getting steps:', error);
      return null;
    }
  }

  async getTodayCaloriesBurned() {
    if (!this.isAvailable) return null;

    try {
      // Demo mode
      return Math.floor(Math.random() * 500) + 200;
    } catch (error) {
      return null;
    }
  }

  async getTodayWaterIntake() {
    if (!this.isAvailable) return null;

    try {
      // Demo mode - return in ml
      return Math.floor(Math.random() * 1500) + 500;
    } catch (error) {
      return null;
    }
  }

  async getWeeklySteps() {
    if (!this.isAvailable) return null;

    try {
      // Demo mode
      const weekData = [];
      const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        weekData.push({
          day: days[date.getDay()],
          steps: Math.floor(Math.random() * 10000) + 2000,
        });
      }
      return weekData;
    } catch (error) {
      return null;
    }
  }

  async getWeightHistory(days = 30) {
    if (!this.isAvailable) return null;

    try {
      // Demo mode
      const weightData = [];
      let baseWeight = 70; // kg
      for (let i = days - 1; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        baseWeight += (Math.random() - 0.5) * 0.5; // Small fluctuation
        weightData.push({
          date: date.toISOString().split('T')[0],
          weight: parseFloat(baseWeight.toFixed(1)),
        });
      }
      return weightData;
    } catch (error) {
      return null;
    }
  }

  async getSleepAnalysis() {
    if (!this.isAvailable) return null;

    try {
      // Demo mode
      return {
        hoursSlept: 7.5,
        sleepQuality: 'Good',
        bedtime: '23:00',
        wakeTime: '06:30',
      };
    } catch (error) {
      return null;
    }
  }

  async getNutritionSummary() {
    if (!this.isAvailable) return null;

    try {
      // Demo mode - daily nutrition
      return {
        calories: Math.floor(Math.random() * 800) + 1200,
        protein: Math.floor(Math.random() * 50) + 40,
        carbs: Math.floor(Math.random() * 100) + 150,
        fat: Math.floor(Math.random() * 40) + 40,
        fiber: Math.floor(Math.random() * 15) + 10,
        water: Math.floor(Math.random() * 1000) + 1000, // ml
        vitaminC: Math.floor(Math.random() * 50) + 40, // mg
        vitaminD: Math.floor(Math.random() * 400) + 200, // IU
        calcium: Math.floor(Math.random() * 500) + 500, // mg
        iron: Math.floor(Math.random() * 10) + 8, // mg
      };
    } catch (error) {
      return null;
    }
  }

  async logWater(milliliters) {
    if (!this.isAvailable) return false;

    try {
      // When AppleHealthKit is available:
      // const options = {
      //   value: milliliters,
      //   date: new Date().toISOString(),
      //   unit: 'ml',
      // };
      // return new Promise((resolve, reject) => {
      //   this.AppleHealthKit.saveWater(options, (err, results) => {
      //     if (err) reject(err);
      //     resolve(true);
      //   });
      // });

      console.log(`Logged ${milliliters}ml water to Health (demo mode)`);
      return true;
    } catch (error) {
      console.log('Error logging water:', error);
      return false;
    }
  }

  // Get health insights based on data
  async getHealthInsights() {
    const connected = await this.isConnected();
    if (!connected) return null;

    try {
      const steps = await this.getTodaySteps();
      const calories = await this.getTodayCaloriesBurned();
      const sleep = await this.getSleepAnalysis();
      const nutrition = await this.getNutritionSummary();

      const insights = [];

      // Steps insight
      if (steps < 5000) {
        insights.push({
          type: 'activity',
          title: 'Move More',
          message: `You've taken ${steps} steps today. Try to reach 10,000 for optimal health!`,
          priority: 'medium',
        });
      } else if (steps >= 10000) {
        insights.push({
          type: 'activity',
          title: 'Great Activity!',
          message: `Excellent! You've hit ${steps} steps today. Keep up the great work!`,
          priority: 'low',
        });
      }

      // Sleep insight
      if (sleep && sleep.hoursSlept < 7) {
        insights.push({
          type: 'sleep',
          title: 'Sleep More',
          message: `You got ${sleep.hoursSlept} hours of sleep. Adults need 7-9 hours for optimal health.`,
          priority: 'high',
        });
      }

      // Nutrition insights
      if (nutrition) {
        if (nutrition.protein < 50) {
          insights.push({
            type: 'nutrition',
            title: 'Protein Intake',
            message: 'Your protein intake is low today. Consider adding lean meats, fish, or legumes.',
            priority: 'medium',
          });
        }

        if (nutrition.fiber < 20) {
          insights.push({
            type: 'nutrition',
            title: 'Fiber Intake',
            message: 'Increase fiber intake with whole grains, fruits, and vegetables for better digestion.',
            priority: 'medium',
          });
        }

        if (nutrition.water < 2000) {
          insights.push({
            type: 'hydration',
            title: 'Stay Hydrated',
            message: `You've had ${nutrition.water}ml of water. Aim for at least 2000ml daily.`,
            priority: 'high',
          });
        }
      }

      return insights;
    } catch (error) {
      console.log('Error getting health insights:', error);
      return null;
    }
  }
}

export const healthKitService = new HealthKitService();
