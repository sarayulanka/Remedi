import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { View, Text, ActivityIndicator, Platform, StyleSheet, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

// Screens
import OnboardingScreen from './screens/OnboardingScreen';
import AuthScreen from './screens/AuthScreen';
import HomeScreen from './screens/HomeScreen';
import LocationsScreen from './screens/LocationsScreen';
import HealthScreen from './screens/HealthScreen';
import GoalsScreen from './screens/GoalsScreen';
import StoryOnboardingScreen from './screens/StoryOnboardingScreen';
import SignupCompleteScreen from './screens/SignupCompleteScreen';
import ProfileScreen from './screens/ProfileScreen';

import { colors, gradients, shadows } from './theme/colors';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

const { width: screenWidth } = Dimensions.get('window');

// Custom Tab Bar Icon Component with improved styling
const TabIcon = ({ icon, label, focused, color }) => (
  <View style={[
    tabStyles.iconContainer,
    focused && tabStyles.iconContainerFocused
  ]}>
    <LinearGradient
      colors={focused ? gradients.button : ['transparent', 'transparent']}
      style={tabStyles.iconGradient}
    >
      <Ionicons
        name={icon}
        size={focused ? 26 : 24}
        color={focused ? colors.white : color}
        style={tabStyles.icon}
      />
    </LinearGradient>
  </View>
);

// Tab bar icon configurations
const TAB_ICONS = {
  Home: { active: 'home', inactive: 'home-outline' },
  Locations: { active: 'location', inactive: 'location-outline' },
  Health: { active: 'heart', inactive: 'heart-outline' },
  Goals: { active: 'trophy', inactive: 'trophy-outline' },
  Profile: { active: 'person', inactive: 'person-outline' },
};

const tabStyles = StyleSheet.create({
  iconContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 56,
    height: 56,
    borderRadius: 28,
    marginBottom: Platform.OS === 'ios' ? 0 : 4,
  },
  iconContainerFocused: {
    transform: [{ scale: 1.05 }],
  },
  iconGradient: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    textAlign: 'center',
  },
});

function MainTabs({ navigation }) {
  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('username');
      // Use getParent() to access the Stack Navigator from within Tab Navigator
      const parentNav = navigation.getParent();
      if (parentNav) {
        parentNav.reset({
          index: 0,
          routes: [{ name: 'Auth' }],
        });
      } else {
        // Fallback: use the navigation directly
        navigation.reset({
          index: 0,
          routes: [{ name: 'Auth' }],
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
      // Still try to navigate even if token removal fails
      navigation.reset({
        index: 0,
        routes: [{ name: 'Auth' }],
      });
    }
  };

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarActiveTintColor: colors.primaryDark,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          backgroundColor: colors.white,
          borderTopColor: colors.gray100,
          borderTopWidth: 0,
          paddingBottom: Platform.OS === 'ios' ? 30 : 16,
          paddingTop: 12,
          paddingHorizontal: 10,
          height: Platform.OS === 'ios' ? 100 : 85,
          elevation: 25,
          shadowColor: colors.primaryDark,
          shadowOffset: { width: 0, height: -8 },
          shadowOpacity: 0.12,
          shadowRadius: 16,
          borderTopLeftRadius: 24,
          borderTopRightRadius: 24,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          marginTop: 2,
          marginBottom: Platform.OS === 'ios' ? 0 : 4,
          letterSpacing: 0.3,
        },
        tabBarItemStyle: {
          paddingVertical: 6,
          minWidth: screenWidth / 5 - 8,
        },
        tabBarIcon: ({ focused, color }) => {
          const icons = TAB_ICONS[route.name];
          return (
            <TabIcon
              icon={focused ? icons.active : icons.inactive}
              label={route.name}
              focused={focused}
              color={color}
            />
          );
        },
        headerShown: false,
      })}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarLabel: 'Home',
        }}
      />
      <Tab.Screen
        name="Locations"
        component={LocationsScreen}
        options={{
          tabBarLabel: 'Find Food',
        }}
      />
      <Tab.Screen
        name="Health"
        component={HealthScreen}
        options={{
          tabBarLabel: 'Health',
        }}
      />
      <Tab.Screen
        name="Goals"
        component={GoalsScreen}
        options={{
          tabBarLabel: 'Goals',
        }}
      />
      <Tab.Screen
        name="Profile"
        options={{
          tabBarLabel: 'Profile',
        }}
      >
        {(props) => <ProfileScreen {...props} onLogout={handleLogout} />}
      </Tab.Screen>
    </Tab.Navigator>
  );
}

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [isFirstLaunch, setIsFirstLaunch] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAppState();
  }, []);

  const checkAppState = async () => {
    try {
      // Check if first launch
      const hasLaunched = await AsyncStorage.getItem('hasLaunched');
      if (hasLaunched === null) {
        setIsFirstLaunch(true);
        await AsyncStorage.setItem('hasLaunched', 'true');
      } else {
        setIsFirstLaunch(false);
      }

      // Check authentication
      const token = await AsyncStorage.getItem('authToken');
      setIsAuthenticated(!!token);
    } catch (error) {
      console.error('Error checking app state:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <LinearGradient colors={gradients.main} style={styles.loadingContainer}>
        <View style={styles.loadingContent}>
          <View style={styles.loadingIconContainer}>
            <LinearGradient
              colors={gradients.button}
              style={styles.loadingIconGradient}
            >
              <Text style={styles.loadingIcon}>🥗</Text>
            </LinearGradient>
          </View>
          <Text style={styles.loadingTitle}>Remedi</Text>
          <ActivityIndicator size="large" color={colors.primaryDark} style={styles.loadingSpinner} />
          <Text style={styles.loadingText}>Loading your nutrition journey...</Text>
        </View>
      </LinearGradient>
    );
  }

  // Determine the initial route based on authentication status
  const getInitialRoute = () => {
    if (isFirstLaunch) return 'Onboarding';
    if (!isAuthenticated) return 'Auth';
    return 'Main';
  };

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{ headerShown: false }}
        initialRouteName={getInitialRoute()}
      >
        <Stack.Screen name="Onboarding" component={OnboardingScreen} />
        <Stack.Screen name="Auth" component={AuthScreen} />
        <Stack.Screen name="StoryOnboarding" component={StoryOnboardingScreen} />
        <Stack.Screen name="SignupComplete" component={SignupCompleteScreen} />
        <Stack.Screen name="Main" component={MainTabs} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingContent: {
    alignItems: 'center',
  },
  loadingIconContainer: {
    marginBottom: 20,
    ...shadows.lg,
  },
  loadingIconGradient: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingIcon: {
    fontSize: 48,
  },
  loadingTitle: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.text,
    marginBottom: 20,
    letterSpacing: -0.5,
  },
  loadingSpinner: {
    marginBottom: 16,
  },
  loadingText: {
    color: colors.textLight,
    fontSize: 16,
    fontWeight: '500',
  },
});
