import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  Modal,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';
import { gamificationAPI } from '../services/api';

const GoalsScreen = () => {
  const [goals, setGoals] = useState([]);
  const [badges, setBadges] = useState([]);
  const [availableBadges, setAvailableBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    targetDays: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [goalsData, badgesData, availableData] = await Promise.all([
        gamificationAPI.getGoals(),
        gamificationAPI.getBadges(),
        gamificationAPI.getAvailableBadges(),
      ]);

      setGoals(goalsData);
      setBadges(badgesData);
      setAvailableBadges(availableData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const createGoal = async () => {
    if (!newGoal.title.trim() || !newGoal.targetDays) {
      Alert.alert('Missing Information', 'Please fill in all required fields');
      return;
    }

    try {
      await gamificationAPI.createGoal(
        newGoal.title,
        newGoal.description,
        parseInt(newGoal.targetDays)
      );

      Alert.alert('Success! 🎯', 'Goal created successfully');
      setModalVisible(false);
      setNewGoal({ title: '', description: '', targetDays: '' });
      loadData();
    } catch (error) {
      Alert.alert('Error', 'Failed to create goal');
    }
  };

  const updateProgress = async (goalId) => {
    try {
      const result = await gamificationAPI.updateGoalProgress(goalId);
      Alert.alert('Progress Updated! 🎉', result.message);
      loadData();
    } catch (error) {
      Alert.alert('Error', 'Failed to update progress');
    }
  };

  const earnedBadgeIds = badges.map((b) => b.badgeId);

  if (loading) {
    return (
      <LinearGradient colors={gradients.main} style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primaryDark} />
        </View>
      </LinearGradient>
    );
  }

  return (
    <LinearGradient colors={gradients.main} style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Your Progress</Text>
          <Text style={styles.headerSubtitle}>Track your nutrition journey</Text>
        </View>

        {/* Earned Badges Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Achievements</Text>
            <View style={styles.badgeCount}>
              <Text style={styles.badgeCountText}>{badges.length}</Text>
            </View>
          </View>

          {badges.length > 0 ? (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.badgesScroll}
            >
              {badges.map((badge, index) => (
                <View key={index} style={styles.badgeCard}>
                  <LinearGradient
                    colors={[colors.white, colors.primaryLight]}
                    style={styles.badgeGradient}
                  >
                    <View style={styles.badgeIconContainer}>
                      <Text style={styles.badgeIcon}>{badge.icon}</Text>
                    </View>
                    <Text style={styles.badgeName}>{badge.name}</Text>
                    <Text style={styles.badgeDescription}>{badge.description}</Text>
                  </LinearGradient>
                </View>
              ))}
            </ScrollView>
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyEmoji}>🏆</Text>
              <Text style={styles.emptyText}>No badges yet. Keep checking in to earn your first!</Text>
            </View>
          )}
        </View>

        {/* Available Badges */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Available Badges</Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.badgesScroll}
          >
            {availableBadges.map((badge, index) => {
              const isEarned = earnedBadgeIds.includes(badge.badgeId);
              return (
                <View key={index} style={styles.badgeCard}>
                  <LinearGradient
                    colors={isEarned ? [colors.white, colors.primaryLight] : [colors.gray50, colors.gray100]}
                    style={styles.badgeGradient}
                  >
                    <View style={[styles.badgeIconContainer, !isEarned && styles.lockedBadge]}>
                      <Text style={styles.badgeIcon}>{isEarned ? badge.icon : '🔒'}</Text>
                    </View>
                    <Text style={[styles.badgeName, !isEarned && styles.lockedText]}>{badge.name}</Text>
                    <Text style={[styles.badgeDescription, !isEarned && styles.lockedText]}>
                      {badge.description}
                    </Text>
                  </LinearGradient>
                </View>
              );
            })}
          </ScrollView>
        </View>

        {/* Goals Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>My Goals</Text>
            <TouchableOpacity
              style={styles.addButton}
              onPress={() => setModalVisible(true)}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={gradients.button}
                style={styles.addButtonGradient}
              >
                <Text style={styles.addButtonText}>+ Add</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>

          {goals.length > 0 ? (
            goals.map((goal, index) => {
              const progress = (goal.currentDays / goal.targetDays) * 100;
              const isCompleted = goal.completed;

              return (
                <View key={index} style={styles.goalCard}>
                  <LinearGradient
                    colors={[colors.white, colors.offWhite]}
                    style={styles.goalGradient}
                  >
                    <View style={styles.goalHeader}>
                      <Text style={styles.goalTitle}>{goal.title}</Text>
                      {isCompleted && (
                        <View style={styles.completedBadge}>
                          <Text style={styles.completedText}>✓ Done</Text>
                        </View>
                      )}
                    </View>

                    {goal.description && (
                      <Text style={styles.goalDescription}>{goal.description}</Text>
                    )}

                    <View style={styles.goalProgress}>
                      <View style={styles.progressBarBackground}>
                        <View
                          style={[
                            styles.progressBarFill,
                            { width: `${Math.min(progress, 100)}%` },
                          ]}
                        >
                          <LinearGradient
                            colors={isCompleted ? gradients.success : gradients.button}
                            start={{ x: 0, y: 0 }}
                            end={{ x: 1, y: 0 }}
                            style={styles.progressGradient}
                          />
                        </View>
                      </View>
                      <Text style={styles.progressText}>
                        {goal.currentDays} / {goal.targetDays} days
                      </Text>
                    </View>

                    {!isCompleted && (
                      <TouchableOpacity
                        style={styles.updateButton}
                        onPress={() => updateProgress(goal.goalId)}
                        activeOpacity={0.8}
                      >
                        <Text style={styles.updateButtonText}>Mark Today</Text>
                      </TouchableOpacity>
                    )}
                  </LinearGradient>
                </View>
              );
            })
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyEmoji}>🎯</Text>
              <Text style={styles.emptyText}>No goals yet. Create your first goal to get started!</Text>
            </View>
          )}
        </View>

        <View style={styles.bottomSpacer} />
      </ScrollView>

      {/* Create Goal Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <LinearGradient
              colors={[colors.white, colors.offWhite]}
              style={styles.modalGradient}
            >
              <Text style={styles.modalTitle}>Create New Goal</Text>

              <View style={styles.modalInputContainer}>
                <Text style={styles.modalLabel}>Goal Title *</Text>
                <TextInput
                  style={styles.modalInput}
                  placeholder="e.g., Eat more vegetables"
                  value={newGoal.title}
                  onChangeText={(text) => setNewGoal({ ...newGoal, title: text })}
                  placeholderTextColor={colors.textMuted}
                />
              </View>

              <View style={styles.modalInputContainer}>
                <Text style={styles.modalLabel}>Description (optional)</Text>
                <TextInput
                  style={[styles.modalInput, styles.textArea]}
                  placeholder="Add more details about your goal..."
                  value={newGoal.description}
                  onChangeText={(text) => setNewGoal({ ...newGoal, description: text })}
                  multiline
                  numberOfLines={3}
                  textAlignVertical="top"
                  placeholderTextColor={colors.textMuted}
                />
              </View>

              <View style={styles.modalInputContainer}>
                <Text style={styles.modalLabel}>Target Days *</Text>
                <TextInput
                  style={styles.modalInput}
                  placeholder="e.g., 30"
                  value={newGoal.targetDays}
                  onChangeText={(text) => setNewGoal({ ...newGoal, targetDays: text })}
                  keyboardType="number-pad"
                  placeholderTextColor={colors.textMuted}
                />
              </View>

              <View style={styles.modalButtons}>
                <TouchableOpacity
                  style={styles.modalCancelButton}
                  onPress={() => setModalVisible(false)}
                  activeOpacity={0.8}
                >
                  <Text style={styles.modalCancelText}>Cancel</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.modalCreateButton}
                  onPress={createGoal}
                  activeOpacity={0.8}
                >
                  <LinearGradient
                    colors={gradients.button}
                    style={styles.modalCreateGradient}
                  >
                    <Text style={styles.modalCreateText}>Create</Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            </LinearGradient>
          </View>
        </View>
      </Modal>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    paddingHorizontal: spacing['2xl'],
    paddingTop: Platform.OS === 'ios' ? 70 : 50,
    paddingBottom: spacing.lg,
  },
  headerTitle: {
    fontSize: typography['4xl'],
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.xs,
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: typography.base,
    color: colors.textLight,
  },
  section: {
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
    paddingHorizontal: spacing['2xl'],
    marginBottom: spacing.base,
  },
  badgeCount: {
    backgroundColor: colors.primaryDark,
    width: 32,
    height: 32,
    borderRadius: borderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
    ...shadows.sm,
  },
  badgeCountText: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.white,
  },
  badgesScroll: {
    paddingHorizontal: spacing['2xl'],
    gap: spacing.base,
  },
  badgeCard: {
    width: 140,
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.md,
    marginRight: spacing.base,
  },
  badgeGradient: {
    padding: spacing.base,
    alignItems: 'center',
  },
  badgeIconContainer: {
    width: 80,
    height: 80,
    borderRadius: borderRadius.full,
    backgroundColor: colors.white,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
    ...shadows.sm,
  },
  lockedBadge: {
    backgroundColor: colors.gray200,
  },
  badgeIcon: {
    fontSize: 40,
  },
  badgeName: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.text,
    textAlign: 'center',
    marginBottom: spacing.xs,
  },
  badgeDescription: {
    fontSize: typography.xs,
    color: colors.textMuted,
    textAlign: 'center',
    lineHeight: typography.xs * 1.4,
  },
  lockedText: {
    color: colors.textMuted,
  },
  addButton: {
    borderRadius: borderRadius.md,
    overflow: 'hidden',
    ...shadows.sm,
  },
  addButtonGradient: {
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.sm,
  },
  addButtonText: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.white,
  },
  goalCard: {
    marginHorizontal: spacing['2xl'],
    marginBottom: spacing.base,
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.lg,
  },
  goalGradient: {
    padding: spacing.lg,
  },
  goalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  goalTitle: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.text,
    flex: 1,
  },
  completedBadge: {
    backgroundColor: colors.successLight,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
  },
  completedText: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.success,
  },
  goalDescription: {
    fontSize: typography.sm,
    color: colors.textLight,
    lineHeight: typography.sm * 1.5,
    marginBottom: spacing.base,
  },
  goalProgress: {
    marginBottom: spacing.base,
  },
  progressBarBackground: {
    height: 8,
    backgroundColor: colors.gray100,
    borderRadius: borderRadius.full,
    overflow: 'hidden',
    marginBottom: spacing.xs,
  },
  progressBarFill: {
    height: '100%',
    borderRadius: borderRadius.full,
  },
  progressGradient: {
    flex: 1,
  },
  progressText: {
    fontSize: typography.sm,
    color: colors.textLight,
    fontWeight: '600',
  },
  updateButton: {
    backgroundColor: colors.white,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: colors.primaryDark,
  },
  updateButtonText: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.primaryDark,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: spacing['3xl'],
    paddingHorizontal: spacing['2xl'],
  },
  emptyEmoji: {
    fontSize: 64,
    marginBottom: spacing.base,
  },
  emptyText: {
    fontSize: typography.base,
    color: colors.textLight,
    textAlign: 'center',
    lineHeight: typography.base * 1.5,
  },
  bottomSpacer: {
    height: spacing['2xl'],
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing['2xl'],
  },
  modalContent: {
    width: '100%',
    maxWidth: 400,
    borderRadius: borderRadius['2xl'],
    overflow: 'hidden',
    ...shadows.xl,
  },
  modalGradient: {
    padding: spacing.xl,
  },
  modalTitle: {
    fontSize: typography['2xl'],
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.xl,
    textAlign: 'center',
  },
  modalInputContainer: {
    marginBottom: spacing.base,
  },
  modalLabel: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  modalInput: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.md,
    padding: spacing.base,
    fontSize: typography.base,
    color: colors.text,
    borderWidth: 2,
    borderColor: colors.gray100,
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.xl,
  },
  modalCancelButton: {
    flex: 1,
    backgroundColor: colors.white,
    paddingVertical: spacing.base,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: colors.gray200,
  },
  modalCancelText: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.text,
  },
  modalCreateButton: {
    flex: 1,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
    ...shadows.md,
  },
  modalCreateGradient: {
    paddingVertical: spacing.base,
    alignItems: 'center',
  },
  modalCreateText: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.white,
  },
});

export default GoalsScreen;
