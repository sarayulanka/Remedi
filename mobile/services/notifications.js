import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

class NotificationService {
  constructor() {
    this.expoPushToken = null;
  }

  async initialize() {
    // Check if notifications are enabled by user
    const notificationsEnabled = await AsyncStorage.getItem('notificationsEnabled');
    // Convert string to boolean - 'false' string means disabled
    if (notificationsEnabled === 'false') {
      return null;
    }

    // Register for push notifications
    const token = await this.registerForPushNotificationsAsync();
    this.expoPushToken = token;

    // Set up default scheduled notifications
    await this.setupDefaultNotifications();

    return token;
  }

  async registerForPushNotificationsAsync() {
    let token;

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'default',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#8fd9a3',
      });
    }

    if (Device.isDevice) {
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        console.log('Failed to get push token for push notification!');
        return null;
      }

      try {
        token = (await Notifications.getExpoPushTokenAsync()).data;
        console.log('Push token:', token);
      } catch (error) {
        console.log('Error getting push token:', error);
      }
    } else {
      console.log('Must use physical device for Push Notifications');
    }

    return token;
  }

  async setupDefaultNotifications() {
    // Cancel all existing notifications first
    await Notifications.cancelAllScheduledNotificationsAsync();

    // Check user preferences
    const streakReminder = await AsyncStorage.getItem('streakReminderEnabled');
    const healthTips = await AsyncStorage.getItem('healthTipsEnabled');

    // Schedule streak reminder (daily at 9 AM)
    if (streakReminder !== 'false') {
      await this.scheduleStreakReminder();
    }

    // Schedule health tip (every 3 days at 10 AM)
    if (healthTips !== 'false') {
      await this.scheduleHealthTip();
    }
  }

  async scheduleStreakReminder() {
    await Notifications.scheduleNotificationAsync({
      content: {
        title: "Keep your streak going!",
        body: "Don't forget to check in today to maintain your nutrition streak!",
        data: { type: 'streak_reminder' },
        sound: true,
      },
      trigger: {
        hour: 9,
        minute: 0,
        repeats: true,
      },
    });
  }

  async scheduleHealthTip() {
    const healthTips = [
      "Drink at least 8 glasses of water today for optimal hydration!",
      "Add some leafy greens to your next meal for extra vitamins!",
      "Try a handful of nuts for a healthy snack rich in omega-3!",
      "Colorful vegetables mean diverse nutrients - eat the rainbow!",
      "Protein at every meal helps maintain energy throughout the day!",
      "Fermented foods like yogurt support your gut health!",
      "Whole grains provide sustained energy - choose brown over white!",
      "Berries are packed with antioxidants - add them to breakfast!",
      "Citrus fruits boost your vitamin C - perfect for immunity!",
      "Dark chocolate (70%+) can be a healthy treat in moderation!",
    ];

    const randomTip = healthTips[Math.floor(Math.random() * healthTips.length)];

    await Notifications.scheduleNotificationAsync({
      content: {
        title: "Daily Health Tip",
        body: randomTip,
        data: { type: 'health_tip' },
        sound: true,
      },
      trigger: {
        hour: 10,
        minute: 0,
        repeats: true,
      },
    });
  }

  async scheduleGoalReminder(goalTitle, targetDays, currentDays) {
    const remaining = targetDays - currentDays;
    if (remaining <= 0) return;

    await Notifications.scheduleNotificationAsync({
      content: {
        title: "Goal Progress",
        body: `You're ${currentDays}/${targetDays} days into "${goalTitle}"! Keep going!`,
        data: { type: 'goal_reminder' },
        sound: true,
      },
      trigger: {
        hour: 18,
        minute: 0,
        repeats: false,
      },
    });
  }

  async sendLocalNotification(title, body, data = {}) {
    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        data,
        sound: true,
      },
      trigger: null, // Immediate
    });
  }

  async cancelAllNotifications() {
    await Notifications.cancelAllScheduledNotificationsAsync();
  }

  async enableNotifications() {
    await AsyncStorage.setItem('notificationsEnabled', 'true');
    await this.setupDefaultNotifications();
  }

  async disableNotifications() {
    await AsyncStorage.setItem('notificationsEnabled', 'false');
    await this.cancelAllNotifications();
  }

  async toggleStreakReminders(enabled) {
    await AsyncStorage.setItem('streakReminderEnabled', enabled.toString());
    if (enabled) {
      await this.scheduleStreakReminder();
    } else {
      // Cancel only streak reminders
      const scheduled = await Notifications.getAllScheduledNotificationsAsync();
      for (const notification of scheduled) {
        if (notification.content.data?.type === 'streak_reminder') {
          await Notifications.cancelScheduledNotificationAsync(notification.identifier);
        }
      }
    }
  }

  async toggleHealthTips(enabled) {
    await AsyncStorage.setItem('healthTipsEnabled', enabled.toString());
    if (enabled) {
      await this.scheduleHealthTip();
    } else {
      // Cancel only health tip notifications
      const scheduled = await Notifications.getAllScheduledNotificationsAsync();
      for (const notification of scheduled) {
        if (notification.content.data?.type === 'health_tip') {
          await Notifications.cancelScheduledNotificationAsync(notification.identifier);
        }
      }
    }
  }

  // Send congratulations for achievements
  async sendAchievementNotification(badgeName, badgeIcon) {
    await this.sendLocalNotification(
      "Badge Earned!",
      `Congratulations! You earned the "${badgeName}" badge ${badgeIcon}`,
      { type: 'achievement' }
    );
  }

  // Send streak milestone notification
  async sendStreakMilestoneNotification(days) {
    const milestones = {
      7: "One week strong!",
      14: "Two weeks of dedication!",
      30: "A whole month! Amazing!",
      50: "50 days! You're a legend!",
      100: "100 DAYS! Century club member!",
    };

    const message = milestones[days] || `${days} days! Keep it up!`;

    await this.sendLocalNotification(
      "Streak Milestone",
      message,
      { type: 'streak_milestone' }
    );
  }
}

export const notificationService = new NotificationService();

// Listener setup function to be called from app root
export const setupNotificationListeners = (onNotificationReceived, onNotificationResponse) => {
  const notificationListener = Notifications.addNotificationReceivedListener(onNotificationReceived);
  const responseListener = Notifications.addNotificationResponseReceivedListener(onNotificationResponse);

  return () => {
    Notifications.removeNotificationSubscription(notificationListener);
    Notifications.removeNotificationSubscription(responseListener);
  };
};
