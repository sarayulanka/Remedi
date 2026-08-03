import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, gradients } from '../theme/colors';
import { authAPI } from '../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const SignupCompleteScreen = ({ route, navigation }) => {
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    completeSignup();
  }, []);

  const completeSignup = async () => {
    try {
      const {
        username,
        email,
        password,
        fullName,
        age,
        gender,
        location,
        nutritionGoals,
        healthConditions,
        allergies,
        dietType,
      } = route.params;

      // Prepare signup data with snake_case keys for API Gateway
      const signupData = {
        username,
        email,
        password,
        fullName: fullName || '',
        first_name: (fullName || '').split(' ')[0] || '',
        last_name: (fullName || '').split(' ').slice(1).join(' ') || '',
        nutrition_goals: nutritionGoals || [],
        food_allergies: allergies || [],
        diet_type: dietType || '',
      };

      // Call signup API (creates user + logs in, returns token)
      const response = await authAPI.signup(signupData);

      // Store auth token and user_id
      await AsyncStorage.setItem('authToken', response.token);
      await AsyncStorage.setItem('userId', response.user_id);
      await AsyncStorage.setItem('userEmail', response.email);
      await AsyncStorage.setItem('username', response.username);

      console.log('Signup successful:', response);

      // Success! Navigate to main app
      setTimeout(() => {
        navigation.reset({
          index: 0,
          routes: [{ name: 'Main' }],
        });
      }, 1500);

    } catch (error) {
      setIsLoading(false);
      Alert.alert(
        'Signup Failed',
        error.response?.data?.error || 'An error occurred during signup',
        [
          {
            text: 'Try Again',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    }
  };

  return (
    <LinearGradient colors={gradients.main} style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.emoji}>🌱</Text>
        <Text style={styles.title}>Creating Your Profile...</Text>
        <Text style={styles.subtitle}>
          Setting up your personalized nutrition journey
        </Text>
        <ActivityIndicator size="large" color={colors.primaryDark} style={styles.loader} />
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
    padding: 40,
  },
  emoji: {
    fontSize: 80,
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 10,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: colors.textLight,
    textAlign: 'center',
    marginBottom: 30,
  },
  loader: {
    marginTop: 20,
  },
});

export default SignupCompleteScreen;
