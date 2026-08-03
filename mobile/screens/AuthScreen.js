import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';
import { authAPI } from '../services/api';

const AuthScreen = ({ navigation }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAuth = async () => {
    if (isLogin && (!email || !password)) {
      Alert.alert('Required Fields', 'Please enter your email and password');
      return;
    }

    if (!isLogin && (!username || !email || !password)) {
      Alert.alert('Required Fields', 'Please fill in all required fields');
      return;
    }

    setLoading(true);

    try {
      if (isLogin) {
        // Login flow - uses email + password
        const response = await authAPI.login(email, password);

        // Save token and user_id
        await AsyncStorage.setItem('authToken', response.token);
        await AsyncStorage.setItem('userId', response.user_id);
        await AsyncStorage.setItem('userEmail', response.email);
        await AsyncStorage.setItem('username', response.username);

        // Navigate to main app - reset navigation to clear stack
        navigation.reset({
          index: 0,
          routes: [{ name: 'Main' }],
        });
      } else {
        // Signup flow - navigate to story onboarding
        navigation.navigate('StoryOnboarding', {
          username,
          email,
          password,
        });
      }
    } catch (error) {
      console.error('Auth error:', error);
      Alert.alert(
        'Authentication Failed',
        error.response?.data?.error || 'Please check your credentials and try again'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <LinearGradient colors={gradients.main} style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.logoContainer}>
              <Text style={styles.headerEmoji}>🌿</Text>
              <View style={styles.logoGlow} />
            </View>
            <Text style={styles.headerTitle}>Remedi</Text>
            <Text style={styles.headerSubtitle}>
              Your journey to better health starts here
            </Text>
          </View>

          {/* Form Card */}
          <View style={styles.formCard}>
            <LinearGradient
              colors={[colors.white, colors.offWhite]}
              style={styles.formGradient}
            >
              {/* Tabs */}
              <View style={styles.tabContainer}>
                <TouchableOpacity
                  style={[styles.tab, isLogin && styles.activeTab]}
                  onPress={() => setIsLogin(true)}
                  activeOpacity={0.8}
                >
                  {isLogin && (
                    <LinearGradient
                      colors={gradients.button}
                      style={styles.activeTabGradient}
                    />
                  )}
                  <Text style={[styles.tabText, isLogin && styles.activeTabText]}>
                    Login
                  </Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={[styles.tab, !isLogin && styles.activeTab]}
                  onPress={() => setIsLogin(false)}
                  activeOpacity={0.8}
                >
                  {!isLogin && (
                    <LinearGradient
                      colors={gradients.button}
                      style={styles.activeTabGradient}
                    />
                  )}
                  <Text style={[styles.tabText, !isLogin && styles.activeTabText]}>
                    Sign Up
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Input Fields */}
              <View style={styles.inputsContainer}>
                {!isLogin && (
                  <View style={styles.inputWrapper}>
                    <Text style={styles.inputLabel}>Username</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="Enter your username"
                      value={username}
                      onChangeText={setUsername}
                      autoCapitalize="none"
                      placeholderTextColor={colors.textMuted}
                    />
                  </View>
                )}

                <View style={styles.inputWrapper}>
                  <Text style={styles.inputLabel}>Email</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="Enter your email"
                    value={email}
                    onChangeText={setEmail}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    placeholderTextColor={colors.textMuted}
                  />
                </View>

                <View style={styles.inputWrapper}>
                  <Text style={styles.inputLabel}>Password</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="Enter your password"
                    value={password}
                    onChangeText={setPassword}
                    secureTextEntry
                    placeholderTextColor={colors.textMuted}
                  />
                </View>
              </View>

              {/* Submit Button */}
              <TouchableOpacity
                style={styles.submitButton}
                onPress={handleAuth}
                disabled={loading}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={gradients.button}
                  style={styles.submitButtonGradient}
                >
                  {loading ? (
                    <ActivityIndicator color={colors.white} />
                  ) : (
                    <Text style={styles.submitButtonText}>
                      {isLogin ? 'Login' : 'Continue'}
                    </Text>
                  )}
                </LinearGradient>
              </TouchableOpacity>
            </LinearGradient>
          </View>

          {/* Footer */}
          <Text style={styles.footer}>
            By continuing, you agree to our Terms of Service and Privacy Policy
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingVertical: Platform.OS === 'ios' ? 80 : 60,
    paddingHorizontal: spacing['2xl'],
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing['4xl'],
  },
  logoContainer: {
    position: 'relative',
    marginBottom: spacing.xl,
  },
  headerEmoji: {
    fontSize: 80,
  },
  logoGlow: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: 80,
    height: 80,
    marginLeft: -40,
    marginTop: -40,
    backgroundColor: colors.glow,
    borderRadius: borderRadius.full,
    opacity: 0.4,
  },
  headerTitle: {
    fontSize: typography['5xl'],
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.sm,
    letterSpacing: -1,
  },
  headerSubtitle: {
    fontSize: typography.base,
    color: colors.textLight,
    textAlign: 'center',
    lineHeight: typography.base * 1.5,
  },
  formCard: {
    borderRadius: borderRadius['2xl'],
    overflow: 'hidden',
    ...shadows.xl,
    marginBottom: spacing.xl,
  },
  formGradient: {
    padding: spacing.xl,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: colors.gray50,
    borderRadius: borderRadius.lg,
    padding: spacing.xs,
    marginBottom: spacing.xl,
  },
  tab: {
    flex: 1,
    paddingVertical: spacing.md,
    alignItems: 'center',
    borderRadius: borderRadius.md,
    position: 'relative',
    overflow: 'hidden',
  },
  activeTab: {
    ...shadows.sm,
  },
  activeTabGradient: {
    ...StyleSheet.absoluteFillObject,
  },
  tabText: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.textLight,
  },
  activeTabText: {
    color: colors.white,
    fontWeight: '700',
  },
  inputsContainer: {
    gap: spacing.lg,
    marginBottom: spacing.xl,
  },
  inputWrapper: {
    gap: spacing.sm,
  },
  inputLabel: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.text,
    marginLeft: spacing.xs,
  },
  input: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    fontSize: typography.base,
    color: colors.text,
    borderWidth: 2,
    borderColor: colors.gray100,
    ...shadows.sm,
  },
  submitButton: {
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.lg,
  },
  submitButtonGradient: {
    paddingVertical: spacing.lg,
    alignItems: 'center',
  },
  submitButtonText: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.white,
    letterSpacing: 0.3,
  },
  footer: {
    fontSize: typography.xs,
    color: colors.textMuted,
    textAlign: 'center',
    lineHeight: typography.xs * 1.5,
    paddingHorizontal: spacing.xl,
  },
});

export default AuthScreen;
