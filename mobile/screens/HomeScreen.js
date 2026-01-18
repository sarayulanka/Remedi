import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  RefreshControl,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';
import { gamificationAPI } from '../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const HomeScreen = ({ navigation }) => {
  const [username, setUsername] = useState('');
  const [streak, setStreak] = useState({ currentStreak: 0, longestStreak: 0 });
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const storedUsername = await AsyncStorage.getItem('username');
      setUsername(storedUsername || 'User');

      const streakData = await gamificationAPI.getStreak();
      setStreak(streakData);

      const badgesData = await gamificationAPI.getBadges();
      setBadges(badgesData);
    } catch (error) {
      console.error('Error loading user data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleCheckIn = async () => {
    try {
      const result = await gamificationAPI.checkIn();
      Alert.alert('Great Job! 🎉', result.message);
      
      if (result.newBadges && result.newBadges.length > 0) {
        const badgeNames = result.newBadges.map(b => b.name).join(', ');
        setTimeout(() => {
          Alert.alert('New Badge Earned! 🏆', badgeNames);
        }, 500);
      }
      
      loadUserData();
    } catch (error) {
      Alert.alert('Oops!', error.response?.data?.detail || 'Check-in failed. Please try again.');
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadUserData();
  };

  const features = [
    {
      title: 'Health Analysis',
      description: 'Get natural food remedies for health concerns',
      icon: 'search-outline',
      iconColor: '#f59e0b',
      gradient: ['#fef3c7', '#fffbeb'],
      onPress: () => navigation.navigate('Health'),
    },
    {
      title: 'Goals & Badges',
      description: 'Track your progress and earn rewards',
      icon: 'trophy-outline',
      iconColor: '#ec4899',
      gradient: ['#fce7f3', '#fdf2f8'],
      onPress: () => navigation.navigate('Goals'),
    },
  ];

  return (
    <LinearGradient colors={gradients.main} style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollViewContent}
        showsVerticalScrollIndicator={false}
        bounces={true}
        alwaysBounceVertical={true}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primaryDark} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.greeting}>Hello, {username}</Text>
          <Text style={styles.subtitle}>Ready to nourish your body today?</Text>
        </View>

        {/* Streak Card */}
        <View style={styles.streakCardContainer}>
          <LinearGradient
            colors={[colors.white, colors.primaryLight]}
            style={styles.streakCard}
          >
            <View style={styles.streakHeader}>
              <Text style={styles.streakTitle}>Your Streak</Text>
              <View style={styles.streakIconContainer}>
                <Ionicons name="flame" size={24} color="#f97316" />
              </View>
            </View>

            <View style={styles.streakStats}>
              <View style={styles.streakStat}>
                <Text style={styles.streakNumber}>{streak.currentStreak}</Text>
                <Text style={styles.streakLabel}>Current</Text>
              </View>
              
              <View style={styles.streakDivider} />
              
              <View style={styles.streakStat}>
                <Text style={styles.streakNumber}>{streak.longestStreak}</Text>
                <Text style={styles.streakLabel}>Best</Text>
              </View>
            </View>

            <TouchableOpacity
              style={styles.checkInButton}
              onPress={handleCheckIn}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={gradients.button}
                style={styles.checkInButtonGradient}
              >
                <Text style={styles.checkInButtonText}>Daily Check-In</Text>
              </LinearGradient>
            </TouchableOpacity>
          </LinearGradient>
        </View>

        {/* Badges Section */}
        {badges.length > 0 && (
          <View style={styles.badgesSection}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Recent Achievements</Text>
              <TouchableOpacity onPress={() => navigation.navigate('Goals')}>
                <Text style={styles.seeAllText}>See All</Text>
              </TouchableOpacity>
            </View>
            
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.badgesScroll}
            >
              {badges.slice(0, 5).map((badge, index) => (
                <View key={index} style={styles.badgeCard}>
                  <LinearGradient
                    colors={[colors.white, colors.primaryLight]}
                    style={styles.badgeGradient}
                  >
                    <View style={styles.badgeIconContainer}>
                      <Ionicons name="ribbon" size={28} color={colors.primaryDark} />
                    </View>
                    <Text style={styles.badgeName}>{badge.name}</Text>
                  </LinearGradient>
                </View>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Features Section */}
        <View style={styles.featuresSection}>
          <Text style={styles.sectionTitle}>Explore</Text>
          
          {features.map((feature, index) => (
            <TouchableOpacity
              key={index}
              style={styles.featureCard}
              onPress={feature.onPress}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={feature.gradient}
                style={styles.featureGradient}
              >
                <View style={styles.featureContent}>
                  <View style={styles.featureIconContainer}>
                    <Ionicons name={feature.icon} size={26} color={feature.iconColor} />
                  </View>
                  <View style={styles.featureText}>
                    <Text style={styles.featureTitle}>{feature.title}</Text>
                    <Text style={styles.featureDescription}>{feature.description}</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
                </View>
              </LinearGradient>
            </TouchableOpacity>
          ))}
        </View>

      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollViewContent: {
    flexGrow: 1,
    paddingBottom: Platform.OS === 'ios' ? 120 : 100,
  },
  header: {
    paddingHorizontal: spacing['2xl'],
    paddingTop: Platform.OS === 'ios' ? 70 : 50,
    paddingBottom: spacing.xl,
  },
  greeting: {
    fontSize: typography['4xl'],
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.sm,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: typography.base,
    color: colors.textLight,
    lineHeight: typography.base * 1.5,
  },
  streakCardContainer: {
    paddingHorizontal: spacing['2xl'],
    marginBottom: spacing.xl,
  },
  streakCard: {
    borderRadius: borderRadius['2xl'],
    padding: spacing.xl,
    ...shadows.lg,
  },
  streakHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  streakTitle: {
    fontSize: typography.xl,
    fontWeight: '700',
    color: colors.text,
  },
  streakIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#fff7ed',
    justifyContent: 'center',
    alignItems: 'center',
  },
  streakStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: spacing.xl,
  },
  streakStat: {
    alignItems: 'center',
  },
  streakNumber: {
    fontSize: typography['5xl'],
    fontWeight: '800',
    color: colors.primaryDark,
    marginBottom: spacing.xs,
  },
  streakLabel: {
    fontSize: typography.sm,
    color: colors.textLight,
    fontWeight: '600',
  },
  streakDivider: {
    width: 1,
    backgroundColor: colors.gray200,
  },
  checkInButton: {
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.md,
  },
  checkInButtonGradient: {
    paddingVertical: spacing.base,
    alignItems: 'center',
  },
  checkInButtonText: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.white,
    letterSpacing: 0.3,
  },
  badgesSection: {
    marginBottom: spacing.xl,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing['2xl'],
    marginBottom: spacing.base,
  },
  sectionTitle: {
    fontSize: typography['2xl'],
    fontWeight: '700',
    color: colors.text,
  },
  seeAllText: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.primaryDark,
  },
  badgesScroll: {
    paddingHorizontal: spacing['2xl'],
    gap: spacing.base,
  },
  badgeCard: {
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.md,
    marginRight: spacing.base,
  },
  badgeGradient: {
    width: 120,
    padding: spacing.base,
    alignItems: 'center',
  },
  badgeIconContainer: {
    width: 64,
    height: 64,
    borderRadius: borderRadius.full,
    backgroundColor: colors.white,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
    ...shadows.sm,
  },
  badgeName: {
    fontSize: typography.xs,
    color: colors.text,
    textAlign: 'center',
    fontWeight: '600',
  },
  featuresSection: {
    paddingHorizontal: spacing['2xl'],
  },
  featureCard: {
    marginBottom: spacing.base,
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.md,
  },
  featureGradient: {
    borderRadius: borderRadius.xl,
  },
  featureContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.lg,
  },
  featureIconContainer: {
    width: 56,
    height: 56,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.white,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.base,
    ...shadows.sm,
  },
  featureText: {
    flex: 1,
  },
  featureTitle: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  featureDescription: {
    fontSize: typography.sm,
    color: colors.textLight,
    lineHeight: typography.sm * 1.4,
  },
});

export default HomeScreen;
