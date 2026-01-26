import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';

const XPProgressBar = ({
  currentLevel = 1,
  xpProgress = 0,
  xpToNextLevel = 100,
  totalXP = 0,
  todayXP = 0,
  comboMultiplier = 1.0,
  compact = false,
  showDetails = true,
}) => {
  const progressAnim = useRef(new Animated.Value(0)).current;
  const progressPercent = Math.min((xpProgress / Math.max(xpToNextLevel, 1)) * 100, 100);

  useEffect(() => {
    Animated.timing(progressAnim, {
      toValue: progressPercent,
      duration: 800,
      useNativeDriver: false,
    }).start();
  }, [progressPercent]);

  const progressWidth = progressAnim.interpolate({
    inputRange: [0, 100],
    outputRange: ['0%', '100%'],
  });

  if (compact) {
    return (
      <View style={styles.compactContainer}>
        <View style={styles.compactLevelBadge}>
          <Text style={styles.compactLevelText}>{currentLevel}</Text>
        </View>
        <View style={styles.compactBarContainer}>
          <View style={styles.compactProgressBg}>
            <Animated.View style={[styles.compactProgressFill, { width: progressWidth }]}>
              <LinearGradient
                colors={[colors.gold, colors.goldLight]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.compactGradient}
              />
            </Animated.View>
          </View>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Level Badge and Progress */}
      <View style={styles.mainRow}>
        {/* Level Badge */}
        <View style={styles.levelBadge}>
          <LinearGradient
            colors={[colors.gold, colors.goldDark]}
            style={styles.levelBadgeGradient}
          >
            <Text style={styles.levelNumber}>{currentLevel}</Text>
          </LinearGradient>
          <Text style={styles.levelLabel}>Level</Text>
        </View>

        {/* Progress Section */}
        <View style={styles.progressSection}>
          <View style={styles.progressHeader}>
            <Text style={styles.xpText}>{xpProgress} / {xpToNextLevel} XP</Text>
            {comboMultiplier > 1 && (
              <View style={styles.comboBadge}>
                <Ionicons name="flash" size={12} color={colors.gold} />
                <Text style={styles.comboText}>{comboMultiplier}x</Text>
              </View>
            )}
          </View>

          {/* Progress Bar */}
          <View style={styles.progressBarBg}>
            <Animated.View style={[styles.progressBarFill, { width: progressWidth }]}>
              <LinearGradient
                colors={[colors.goldLight, colors.gold]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.progressGradient}
              />
            </Animated.View>
          </View>

          {showDetails && (
            <View style={styles.detailsRow}>
              <View style={styles.detailItem}>
                <Ionicons name="star" size={12} color={colors.goldDark} />
                <Text style={styles.detailText}>{totalXP} total</Text>
              </View>
              {todayXP > 0 && (
                <View style={styles.detailItem}>
                  <Ionicons name="today" size={12} color={colors.primaryDark} />
                  <Text style={styles.detailText}>+{todayXP} today</Text>
                </View>
              )}
            </View>
          )}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.xl,
    padding: spacing.base,
    ...shadows.sm,
  },
  mainRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  levelBadge: {
    alignItems: 'center',
    marginRight: spacing.base,
  },
  levelBadgeGradient: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    ...shadows.md,
  },
  levelNumber: {
    fontSize: typography.xl,
    fontWeight: '800',
    color: colors.white,
  },
  levelLabel: {
    fontSize: typography.xs,
    color: colors.textMuted,
    marginTop: 2,
    fontWeight: '600',
  },
  progressSection: {
    flex: 1,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  xpText: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.text,
  },
  comboBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.goldBg,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.full,
    gap: 2,
  },
  comboText: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.goldDark,
  },
  progressBarBg: {
    height: 10,
    backgroundColor: colors.gray100,
    borderRadius: borderRadius.full,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: borderRadius.full,
    overflow: 'hidden',
  },
  progressGradient: {
    flex: 1,
  },
  detailsRow: {
    flexDirection: 'row',
    marginTop: spacing.xs,
    gap: spacing.base,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  detailText: {
    fontSize: typography.xs,
    color: colors.textMuted,
  },
  // Compact styles
  compactContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  compactLevelBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.gold,
    justifyContent: 'center',
    alignItems: 'center',
    ...shadows.sm,
  },
  compactLevelText: {
    fontSize: typography.sm,
    fontWeight: '800',
    color: colors.white,
  },
  compactBarContainer: {
    flex: 1,
    maxWidth: 100,
  },
  compactProgressBg: {
    height: 6,
    backgroundColor: colors.gray100,
    borderRadius: borderRadius.full,
    overflow: 'hidden',
  },
  compactProgressFill: {
    height: '100%',
    borderRadius: borderRadius.full,
    overflow: 'hidden',
  },
  compactGradient: {
    flex: 1,
  },
});

export default XPProgressBar;
