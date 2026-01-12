import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { View, Text, ActivityIndicator } from 'react-native';

// Screens
import OnboardingScreen from './screens/OnboardingScreen';
import AuthScreen from './screens/AuthScreen';
import HomeScreen from './screens/HomeScreen';
import LocationsScreen from './screens/LocationsScreen';
import HealthScreen from './screens/HealthScreen';
import GoalsScreen from './screens/GoalsScreen';
import StoryOnboardingScreen from './screens/StoryOnboardingScreen';
import SignupCompleteScreen from './screens/SignupCompleteScreen';

import { colors } from './theme/colors';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: colors.primaryDark,
        tabBarInactiveTintColor: colors.textLight,
        tabBarStyle: {
          backgroundColor: colors.white,
          borderTopColor: colors.gray,
          paddingBottom: 5,
          paddingTop: 5,
          height: 60,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '600',
        },
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarLabel: 'Home',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>🏠</Text>
          ),
        }}
      />
      <Tab.Screen
        name="Locations"
        component={LocationsScreen}
        options={{
          tabBarLabel: 'Locations',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>📍</Text>
          ),
        }}
      />
      <Tab.Screen
        name="Health"
        component={HealthScreen}
        options={{
          tabBarLabel: 'Health',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>🔍</Text>
          ),
        }}
      />
      <Tab.Screen
        name="Goals"
        component={GoalsScreen}
        options={{
          tabBarLabel: 'Goals',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>🏆</Text>
          ),
        }}
      />
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
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={colors.primaryDark} />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {isFirstLaunch ? (
          <Stack.Screen name="Onboarding" component={OnboardingScreen} />
        ) : null}
        {!isAuthenticated ? (
          <>
            <Stack.Screen name="Auth" component={AuthScreen} />
            <Stack.Screen name="StoryOnboarding" component={StoryOnboardingScreen} />
            <Stack.Screen name="SignupComplete" component={SignupCompleteScreen} />
          </>
        ) : null}
        <Stack.Screen name="Main" component={MainTabs} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
