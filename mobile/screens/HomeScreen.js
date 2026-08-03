import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  RefreshControl,
  Platform,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';
import { gamificationAPI } from '../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import CelebrationModal from '../components/CelebrationModal';
import XPProgressBar from '../components/XPProgressBar';

const HomeScreen = ({ navigation }) => {
  const [username, setUsername] = useState('');
  const [streak, setStreak] = useState({
    currentStreak: 0,
    longestStreak: 0,
    streakFreezes: 0,
    hasFreezeProtection: false,
    streakAtRisk: false,
    checkedInToday: false,
    nextMilestone: null,
    daysToNextMilestone: null,
    daysUntilFreeze: 7,
  });
  const [badges, setBadges] = useState([]);
  const [xp, setXp] = useState({
    totalXP: 0,
    currentLevel: 1,
    xpProgress: 0,
    xpToNextLevel: 100,
    todayXP: 0,
    comboMultiplier: 1.0,
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Celebration modal state
  const [showCelebration, setShowCelebration] = useState(false);
  const [celebrationData, setCelebrationData] = useState({
    type: 'milestone',
    title: '',
    subtitle: '',
    xpEarned: null,
  });

  // Animation refs
  const flamePulse = useRef(new Animated.Value(1)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    loadUserData();
    startFlameAnimation();
  }, []);

  useEffect(() => {
    // Animate progress bar when streak data changes
    if (streak.nextMilestone) {
      const progress = streak.currentStreak / streak.nextMilestone.days;
      Animated.timing(progressAnim, {
        toValue: Math.min(progress, 1),
        duration: 800,
        useNativeDriver: false,
      }).start();
    }
  }, [streak.currentStreak, streak.nextMilestone]);

  const startFlameAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(flamePulse, {
          toValue: 1.15,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(flamePulse, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const loadUserData = async () => {
    try {
      const storedUsername = await AsyncStorage.getItem('username');
      setUsername(storedUsername || 'User');

      const streakData = await gamificationAPI.getStreak();
      setStreak(streakData);

      const badgesData = await gamificationAPI.getBadges();
      setBadges(badgesData);

      // Fetch XP data
      const xpData = await gamificationAPI.getXP();
      setXp(xpData);
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

      // Queue of celebrations to show
      const celebrations = [];

      // Check for level up first (highest priority)
      if (result.xp?.levelUp) {
        celebrations.push({
          type: 'milestone',
          title: `Level ${result.xp.newLevel}!`,
          subtitle: 'You reached a new level! Keep up the amazing work.',
          xpEarned: result.xp?.xpAwarded,
          icon: 'star',
          iconColor: '#F59E0B',
        });
      }

      // Check for milestone reached
      if (result.milestoneReached) {
        celebrations.push({
          type: 'milestone',
          title: result.milestoneReached.name,
          subtitle: `${result.milestoneReached.days}-day streak achieved!`,
          xpEarned: result.milestoneReached.xp,
        });
      }

      // Check for freeze earned
      if (result.freezeEarned) {
        celebrations.push({
          type: 'freeze',
          title: 'Streak Freeze Earned!',
          subtitle: 'Keep up the great work! Your freeze will protect your streak if you miss a day.',
          xpEarned: null,
        });
      }

      // Check for new badges
      if (result.newBadges && result.newBadges.length > 0) {
        result.newBadges.forEach(badge => {
          celebrations.push({
            type: 'badge',
            title: badge.name,
            subtitle: badge.description,
            xpEarned: 50,
          });
        });
      }

      // Show first celebration if any
      if (celebrations.length > 0) {
        setCelebrationData(celebrations[0]);
        setShowCelebration(true);
      }
      // Check for freeze used (show as alert, not celebration)
      else if (result.freezeUsed) {
        Alert.alert(
          'Streak Saved!',
          'Your streak freeze was used to protect your streak. Keep going!'
        );
      }
      // Normal check-in
      else if (!result.alreadyCheckedIn) {
        // Show XP earned in the message
        const xpMessage = result.xp?.xpAwarded
          ? ` +${result.xp.xpAwarded} XP`
          : '';
        Alert.alert('Great Job!', result.message + xpMessage);
      } else {
        Alert.alert('Already Done!', 'You\'ve already checked in today.');
      }

      loadUserData();
    } catch (error) {
      Alert.alert('Oops!', error.response?.data?.error || 'Check-in failed. Please try again.');
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
      iconColor: colors.gold,
      gradient: [colors.goldBg, '#fffbeb'],
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

  // Calculate milestone progress
  const milestoneProgress = streak.nextMilestone
    ? (streak.currentStreak / streak.nextMilestone.days) * 100
    : 100;

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

        {/* Enhanced Streak Card */}
        <View style={styles.streakCardContainer}>
          <LinearGradient
            colors={[colors.white, colors.primaryLight]}
            style={styles.streakCard}
          >
            {/* Header Row with Flame and Freezes */}
            <View style={styles.streakHeader}>
              <View style={styles.streakTitleRow}>
                <Text style={styles.streakTitle}>Your Streak</Text>
                {streak.streakAtRisk && !streak.checkedInToday && (
                  <View style={styles.atRiskBadge}>
                    <Text style={styles.atRiskText}>At Risk</Text>
                  </View>
                )}
              </View>
              <View style={styles.headerIcons}>
                {/* Freeze Indicator */}
                {streak.streakFreezes > 0 && (
                  <View style={styles.freezeIndicator}>
                    <Ionicons name="shield-checkmark" size={16} color={colors.freeze} />
                    <Text style={styles.freezeCount}>{streak.streakFreezes}</Text>
                  </View>
                )}
                {/* Animated Flame */}
                <Animated.View
                  style={[
                    styles.streakIconContainer,
                    { transform: [{ scale: flamePulse }] },
                  ]}
                >
                  <Ionicons name="flame" size={24} color={colors.flame} />
                </Animated.View>
              </View>
            </View>

            {/* Streak Stats */}
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

            {/* Milestone Progress */}
            {streak.nextMilestone && (
              <View style={styles.milestoneSection}>
                <View style={styles.milestoneHeader}>
                  <Text style={styles.milestoneLabel}>
                    {streak.daysToNextMilestone} days to {streak.nextMilestone.name}
                  </Text>
                  <Text style={styles.milestoneXP}>+{streak.nextMilestone.xp} XP</Text>
                </View>
                <View style={styles.milestoneProgressBar}>
                  <Animated.View
                    style={[
                      styles.milestoneProgressFill,
                      {
                        width: progressAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: ['0%', '100%'],
                        }),
                      },
                    ]}
                  />
                </View>
              </View>
            )}

            {/* Check-in Button */}
            <TouchableOpacity
              style={[
                styles.checkInButton,
                streak.checkedInToday && styles.checkInButtonDisabled,
              ]}
              onPress={handleCheckIn}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={streak.checkedInToday ? [colors.gray200, colors.gray200] : gradients.button}
                style={styles.checkInButtonGradient}
              >
                <Ionicons
                  name={streak.checkedInToday ? 'checkmark-circle' : 'add-circle-outline'}
                  size={20}
                  color={streak.checkedInToday ? colors.textLight : colors.white}
                  style={styles.checkInIcon}
                />
                <Text
                  style={[
                    styles.checkInButtonText,
                    streak.checkedInToday && styles.checkInButtonTextDisabled,
                  ]}
                >
                  {streak.checkedInToday ? 'Checked In Today' : 'Daily Check-In'}
                </Text>
              </LinearGradient>
            </TouchableOpacity>

            {/* Freeze Progress Hint */}
            {streak.currentStreak > 0 && streak.daysUntilFreeze > 0 && streak.daysUntilFreeze < 7 && (
              <Text style={styles.freezeHint}>
                {streak.daysUntilFreeze} day{streak.daysUntilFreeze !== 1 ? 's' : ''} until next streak freeze
              </Text>
            )}
          </LinearGradient>
        </View>

        {/* XP Progress Section */}
        <View style={styles.xpSection}>
          <XPProgressBar
            currentLevel={xp.currentLevel}
            xpProgress={xp.xpProgress}
            xpToNextLevel={xp.xpToNextLevel}
            totalXP={xp.totalXP}
            todayXP={xp.todayXP}
            comboMultiplier={xp.comboMultiplier}
          />
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

      {/* Celebration Modal */}
      <CelebrationModal
        visible={showCelebration}
        onClose={() => setShowCelebration(false)}
        type={celebrationData.type}
        title={celebrationData.title}
        subtitle={celebrationData.subtitle}
        xpEarned={celebrationData.xpEarned}
      />
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
    marginBottom: spacing.lg,
  },
  streakTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  streakTitle: {
    fontSize: typography.xl,
    fontWeight: '700',
    color: colors.text,
  },
  atRiskBadge: {
    backgroundColor: colors.warningLight,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
  },
  atRiskText: {
    fontSize: typography.xs,
    fontWeight: '600',
    color: colors.goldDark,
  },
  headerIcons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  freezeIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.freezeBg,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
    gap: 4,
  },
  freezeCount: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.freeze,
  },
  streakIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.flameBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  streakStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: spacing.lg,
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
  milestoneSection: {
    marginBottom: spacing.lg,
  },
  milestoneHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  milestoneLabel: {
    fontSize: typography.sm,
    color: colors.textLight,
    fontWeight: '500',
  },
  milestoneXP: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.gold,
  },
  milestoneProgressBar: {
    height: 6,
    backgroundColor: colors.gray100,
    borderRadius: 3,
    overflow: 'hidden',
  },
  milestoneProgressFill: {
    height: '100%',
    backgroundColor: colors.primaryDark,
    borderRadius: 3,
  },
  checkInButton: {
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.md,
  },
  checkInButtonDisabled: {
    ...shadows.sm,
  },
  checkInButtonGradient: {
    flexDirection: 'row',
    paddingVertical: spacing.base,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkInIcon: {
    marginRight: spacing.sm,
  },
  checkInButtonText: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.white,
    letterSpacing: 0.3,
  },
  checkInButtonTextDisabled: {
    color: colors.textLight,
  },
  freezeHint: {
    fontSize: typography.xs,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
  xpSection: {
    paddingHorizontal: spacing['2xl'],
    marginBottom: spacing.xl,
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
