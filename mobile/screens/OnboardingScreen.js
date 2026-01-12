import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  ScrollView,
  Animated,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';

const { width, height } = Dimensions.get('window');

const OnboardingScreen = ({ navigation }) => {
  const [currentPage, setCurrentPage] = useState(0);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const pages = [
    {
      title: 'Welcome to Remedi',
      description:
        'Your personal nutrition companion, powered by science and designed with care. Discover the healing power of food.',
      emoji: '🌱',
      gradient: ['#e8f8eb', '#ffffff'],
    },
    {
      title: 'Find Nourishment',
      description:
        'Locate nearby food banks, shelters, and kitchens. Filter by your dietary needs and preferences.',
      emoji: '📍',
      gradient: ['#f0f9ff', '#ffffff'],
    },
    {
      title: 'Natural Remedies',
      description:
        'Snap a photo or describe your concerns. Get personalized food-based remedies backed by FDA nutritional data.',
      emoji: '🔍',
      gradient: ['#fef3c7', '#ffffff'],
    },
    {
      title: 'Track Your Progress',
      description:
        'Build healthy habits with streaks, earn badges, and celebrate your wins. Make nutrition fun and rewarding.',
      emoji: '🏆',
      gradient: ['#fce7f3', '#ffffff'],
    },
  ];

  const handleNext = () => {
    if (currentPage < pages.length - 1) {
      // Animate transition
      Animated.sequence([
        Animated.parallel([
          Animated.timing(fadeAnim, {
            toValue: 0,
            duration: 200,
            useNativeDriver: true,
          }),
          Animated.timing(scaleAnim, {
            toValue: 0.9,
            duration: 200,
            useNativeDriver: true,
          }),
        ]),
        Animated.parallel([
          Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 300,
            useNativeDriver: true,
          }),
          Animated.spring(scaleAnim, {
            toValue: 1,
            tension: 50,
            friction: 7,
            useNativeDriver: true,
          }),
        ]),
      ]).start();
      
      setCurrentPage(currentPage + 1);
    } else {
      navigation.replace('Auth');
    }
  };

  const handleSkip = () => {
    navigation.replace('Auth');
  };

  return (
    <LinearGradient colors={pages[currentPage].gradient} style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View
          style={[
            styles.content,
            {
              opacity: fadeAnim,
              transform: [{ scale: scaleAnim }],
            },
          ]}
        >
          <View style={styles.emojiContainer}>
            <Text style={styles.emoji}>{pages[currentPage].emoji}</Text>
            <View style={styles.emojiGlow} />
          </View>
          
          <Text style={styles.title}>{pages[currentPage].title}</Text>
          <Text style={styles.description}>{pages[currentPage].description}</Text>
        </Animated.View>

        <View style={styles.pagination}>
          {pages.map((_, index) => (
            <View
              key={index}
              style={[
                styles.dot,
                index === currentPage && styles.activeDot,
              ]}
            />
          ))}
        </View>

        <View style={styles.buttonContainer}>
          {currentPage < pages.length - 1 && (
            <TouchableOpacity
              onPress={handleSkip}
              style={styles.skipButton}
              activeOpacity={0.7}
            >
              <Text style={styles.skipText}>Skip</Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            onPress={handleNext}
            style={styles.nextButton}
            activeOpacity={0.8}
          >
            <LinearGradient
              colors={gradients.button}
              style={styles.nextButtonGradient}
            >
              <Text style={styles.nextText}>
                {currentPage < pages.length - 1 ? 'Next' : 'Get Started'}
              </Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'space-between',
    paddingVertical: Platform.OS === 'ios' ? 80 : 60,
    paddingHorizontal: spacing['2xl'],
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emojiContainer: {
    position: 'relative',
    marginBottom: spacing['4xl'],
  },
  emoji: {
    fontSize: 120,
    textAlign: 'center',
  },
  emojiGlow: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: 100,
    height: 100,
    marginLeft: -50,
    marginTop: -50,
    backgroundColor: colors.glow,
    borderRadius: borderRadius.full,
    opacity: 0.3,
  },
  title: {
    fontSize: typography['4xl'],
    fontWeight: '800',
    color: colors.text,
    textAlign: 'center',
    marginBottom: spacing.xl,
    letterSpacing: -0.5,
  },
  description: {
    fontSize: typography.lg,
    color: colors.textLight,
    textAlign: 'center',
    lineHeight: typography.lg * 1.6,
    paddingHorizontal: spacing.base,
  },
  pagination: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: spacing['3xl'],
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: borderRadius.full,
    backgroundColor: colors.gray200,
    marginHorizontal: spacing.xs,
  },
  activeDot: {
    width: 32,
    height: 8,
    backgroundColor: colors.primaryDark,
  },
  buttonContainer: {
    gap: spacing.base,
  },
  skipButton: {
    alignItems: 'center',
    paddingVertical: spacing.base,
  },
  skipText: {
    fontSize: typography.base,
    color: colors.textLight,
    fontWeight: '600',
  },
  nextButton: {
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.lg,
  },
  nextButtonGradient: {
    paddingVertical: spacing.lg,
    alignItems: 'center',
  },
  nextText: {
    fontSize: typography.xl,
    fontWeight: '700',
    color: colors.white,
    letterSpacing: 0.3,
  },
});

export default OnboardingScreen;
