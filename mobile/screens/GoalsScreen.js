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
  Animated,
  RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';
import { gamificationAPI } from '../services/api';

// Goal templates for quick selection
const GOAL_TEMPLATES = [
  {
    title: 'Drink More Water',
    description: 'Stay hydrated by drinking at least 8 glasses of water daily',
    targetDays: 21,
    icon: 'water-outline',
    category: 'hydration',
  },
  {
    title: 'Eat More Vegetables',
    description: 'Include vegetables in at least 2 meals every day',
    targetDays: 30,
    icon: 'leaf-outline',
    category: 'nutrition',
  },
  {
    title: 'Reduce Sugar Intake',
    description: 'Avoid added sugars and sugary drinks',
    targetDays: 14,
    icon: 'close-circle-outline',
    category: 'nutrition',
  },
  {
    title: 'Take Daily Vitamins',
    description: 'Remember to take your daily multivitamin supplement',
    targetDays: 30,
    icon: 'medical-outline',
    category: 'supplements',
  },
  {
    title: 'Eat Breakfast',
    description: 'Start each day with a nutritious breakfast',
    targetDays: 21,
    icon: 'sunny-outline',
    category: 'habits',
  },
  {
    title: 'No Late Night Snacks',
    description: 'Stop eating at least 3 hours before bedtime',
    targetDays: 14,
    icon: 'moon-outline',
    category: 'habits',
  },
  {
    title: 'Meal Prep Weekly',
    description: 'Prepare healthy meals ahead for the week',
    targetDays: 8,
    icon: 'calendar-outline',
    category: 'planning',
  },
  {
    title: 'More Protein',
    description: 'Include protein in every meal for better nutrition',
    targetDays: 21,
    icon: 'fitness-outline',
    category: 'nutrition',
  },
];

// Circular progress component
const CircularProgress = ({ progress, size = 60, strokeWidth = 6, children }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <View style={{ width: size, height: size, justifyContent: 'center', alignItems: 'center' }}>
      <View style={[styles.circularBase, { width: size, height: size, borderRadius: size / 2, borderWidth: strokeWidth }]} />
      <View style={[styles.circularProgress, {
        width: size,
        height: size,
        borderRadius: size / 2,
        borderWidth: strokeWidth,
        borderColor: progress >= 100 ? colors.success : colors.primaryDark,
        transform: [{ rotate: '-90deg' }],
        borderRightColor: 'transparent',
        borderBottomColor: 'transparent',
        borderLeftColor: progress > 25 ? (progress >= 100 ? colors.success : colors.primaryDark) : 'transparent',
        borderTopColor: progress > 50 ? (progress >= 100 ? colors.success : colors.primaryDark) : 'transparent',
      }]} />
      <View style={styles.circularCenter}>
        {children}
      </View>
    </View>
  );
};

const GoalsScreen = () => {
  const [goals, setGoals] = useState([]);
  const [badges, setBadges] = useState([]);
  const [availableBadges, setAvailableBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [generatingGoals, setGeneratingGoals] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [templateModalVisible, setTemplateModalVisible] = useState(false);
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
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const selectTemplate = (template) => {
    setNewGoal({
      title: template.title,
      description: template.description,
      targetDays: template.targetDays.toString(),
    });
    setTemplateModalVisible(false);
    setModalVisible(true);
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

      Alert.alert('Goal Created!', 'Your new goal has been added. Good luck!');
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
      if (result.alreadyUpdated) {
        Alert.alert('Already Done!', "You've already logged progress for this goal today.");
      } else if (result.newlyCompleted) {
        Alert.alert('Goal Complete!', 'Congratulations! You achieved your goal!');
        checkAndGenerateGoals();
      } else {
        const xpMessage = result.xp?.xpAwarded
          ? ` (+${result.xp.xpAwarded} XP)`
          : '';
        Alert.alert('Progress Updated!', `Day ${result.currentDays} of ${result.targetDays} complete!${xpMessage}`);
      }
      loadData();
    } catch (error) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to update progress');
    }
  };

  const deleteGoal = (goalId, title) => {
    Alert.alert(
      'Delete Goal',
      `Are you sure you want to delete "${title}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await gamificationAPI.deleteGoal(goalId);
              loadData();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete goal');
            }
          },
        },
      ]
    );
  };

  const checkAndGenerateGoals = async () => {
    try {
      const result = await gamificationAPI.generateGoals();
      if (result.generated) {
        Alert.alert(
          'New Goals Generated!',
          `You've completed all your goals! ${result.newGoals.length} new personalized goals have been created for you.`,
          [{ text: 'View Goals', onPress: loadData }]
        );
      }
    } catch (error) {
      console.error('Error generating goals:', error);
    }
  };

  const handleGenerateGoals = async () => {
    setGeneratingGoals(true);
    try {
      const result = await gamificationAPI.generateGoals();
      if (result.generated) {
        Alert.alert(
          'New Goals!',
          `${result.newGoals.length} personalized goals have been created for you.`,
          [{ text: 'View Goals', onPress: loadData }]
        );
      } else {
        Alert.alert('Active Goals', result.message || 'Complete your current goals first.');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to generate goals. Please try again.');
    } finally {
      setGeneratingGoals(false);
      loadData();
    }
  };

  const earnedBadgeIds = badges.map((b) => b.badgeId);

  // Calculate overall progress
  const activeGoals = goals.filter(g => !g.completed);
  const completedGoals = goals.filter(g => g.completed);
  const totalProgress = goals.length > 0
    ? Math.round(goals.reduce((sum, g) => sum + (g.currentDays / g.targetDays) * 100, 0) / goals.length)
    : 0;

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
          <Text style={styles.headerTitle}>Your Progress</Text>
          <Text style={styles.headerSubtitle}>Track your nutrition journey</Text>
        </View>

        {/* Progress Summary Card */}
        <View style={styles.summaryCard}>
          <LinearGradient
            colors={gradients.button}
            style={styles.summaryGradient}
          >
            <View style={styles.summaryContent}>
              <View style={styles.summaryStats}>
                <View style={styles.summaryStat}>
                  <Text style={styles.summaryValue}>{activeGoals.length}</Text>
                  <Text style={styles.summaryLabel}>Active Goals</Text>
                </View>
                <View style={styles.summaryDivider} />
                <View style={styles.summaryStat}>
                  <Text style={styles.summaryValue}>{completedGoals.length}</Text>
                  <Text style={styles.summaryLabel}>Completed</Text>
                </View>
                <View style={styles.summaryDivider} />
                <View style={styles.summaryStat}>
                  <Text style={styles.summaryValue}>{badges.length}</Text>
                  <Text style={styles.summaryLabel}>Badges</Text>
                </View>
              </View>
            </View>
          </LinearGradient>
        </View>

        {/* Earned Badges Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitleInline}>Achievements</Text>
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
                      <Ionicons name="ribbon" size={32} color={colors.primaryDark} />
                    </View>
                    <Text style={styles.badgeName}>{badge.name}</Text>
                    <Text style={styles.badgeDescription}>{badge.description}</Text>
                  </LinearGradient>
                </View>
              ))}
            </ScrollView>
          ) : (
            <View style={styles.emptyState}>
              <View style={styles.emptyIconContainer}>
                <Ionicons name="trophy-outline" size={40} color={colors.textMuted} />
              </View>
              <Text style={styles.emptyText}>No badges yet. Keep checking in to earn your first!</Text>
            </View>
          )}
        </View>

        {/* Goals Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitleInline}>My Goals</Text>
            <View style={styles.buttonGroup}>
              <TouchableOpacity
                style={styles.templateButton}
                onPress={() => setTemplateModalVisible(true)}
                activeOpacity={0.8}
              >
                <Text style={styles.templateButtonText}>Templates</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.addButton}
                onPress={() => setModalVisible(true)}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={gradients.button}
                  style={styles.addButtonGradient}
                >
                  <Text style={styles.addButtonText}>+ New</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </View>

          {goals.length > 0 ? (
            goals.map((goal, index) => {
              const progress = Math.min((goal.currentDays / goal.targetDays) * 100, 100);
              const isCompleted = goal.completed;
              const remaining = goal.targetDays - goal.currentDays;

              return (
                <View key={index} style={styles.goalCard}>
                  <LinearGradient
                    colors={isCompleted ? [colors.successLight, '#f0fdf4'] : [colors.white, colors.offWhite]}
                    style={styles.goalGradient}
                  >
                    <View style={styles.goalRow}>
                      <View style={styles.goalProgressCircle}>
                        <View style={[
                          styles.progressCircleOuter,
                          { borderColor: isCompleted ? colors.success : colors.primaryDark }
                        ]}>
                          <Text style={[
                            styles.progressCircleText,
                            { color: isCompleted ? colors.success : colors.primaryDark }
                          ]}>
                            {Math.round(progress)}%
                          </Text>
                        </View>
                      </View>

                      <View style={styles.goalInfo}>
                        <View style={styles.goalHeader}>
                          <Text style={styles.goalTitle}>{goal.title}</Text>
                          {isCompleted && (
                            <View style={styles.completedBadge}>
                              <Text style={styles.completedText}>Done</Text>
                            </View>
                          )}
                        </View>

                        {goal.description && (
                          <Text style={styles.goalDescription} numberOfLines={2}>
                            {goal.description}
                          </Text>
                        )}

                        <View style={styles.goalMeta}>
                          <Text style={styles.goalMetaText}>
                            {goal.currentDays}/{goal.targetDays} days
                          </Text>
                          {!isCompleted && remaining > 0 && (
                            <Text style={styles.goalRemaining}>
                              {remaining} {remaining === 1 ? 'day' : 'days'} left
                            </Text>
                          )}
                        </View>

                        <View style={styles.goalProgressBar}>
                          <View style={styles.progressBarBackground}>
                            <View
                              style={[
                                styles.progressBarFill,
                                { width: `${progress}%` },
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
                        </View>
                      </View>
                    </View>

                    <View style={styles.goalActions}>
                      {!isCompleted && (
                        <TouchableOpacity
                          style={styles.updateButton}
                          onPress={() => updateProgress(goal.goalId)}
                          activeOpacity={0.8}
                        >
                          <LinearGradient
                            colors={gradients.button}
                            style={styles.updateButtonGradient}
                          >
                            <Ionicons name="checkmark-circle-outline" size={16} color={colors.white} style={{ marginRight: 6 }} />
                            <Text style={styles.updateButtonText}>Mark Today Complete</Text>
                          </LinearGradient>
                        </TouchableOpacity>
                      )}
                      <TouchableOpacity
                        style={styles.deleteButton}
                        onPress={() => deleteGoal(goal.goalId, goal.title)}
                        activeOpacity={0.7}
                      >
                        <Ionicons name="trash-outline" size={16} color={colors.error} />
                      </TouchableOpacity>
                    </View>
                  </LinearGradient>
                </View>
              );
            })
          ) : (
            <View style={styles.emptyState}>
              <View style={styles.emptyIconContainer}>
                <Ionicons name="flag-outline" size={40} color={colors.textMuted} />
              </View>
              <Text style={styles.emptyText}>No goals yet. Create your first goal or pick from templates!</Text>
            </View>
          )}

          {/* AI Generate Goals Button */}
          <TouchableOpacity
            style={styles.generateButton}
            onPress={handleGenerateGoals}
            activeOpacity={0.8}
            disabled={generatingGoals}
          >
            <View style={styles.generateButtonInner}>
              {generatingGoals ? (
                <ActivityIndicator size="small" color={colors.primaryDark} style={{ marginRight: 8 }} />
              ) : (
                <Ionicons name="sparkles-outline" size={18} color={colors.primaryDark} style={{ marginRight: 8 }} />
              )}
              <Text style={styles.generateButtonText}>
                {generatingGoals ? 'Generating...' : 'Generate AI Goals'}
              </Text>
            </View>
          </TouchableOpacity>
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
                      <Ionicons
                        name={isEarned ? 'ribbon' : 'lock-closed-outline'}
                        size={isEarned ? 32 : 24}
                        color={isEarned ? colors.primaryDark : colors.textMuted}
                      />
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

      </ScrollView>

      {/* Template Selection Modal */}
      <Modal
        visible={templateModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setTemplateModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.templateModalContent}>
            <LinearGradient
              colors={[colors.white, colors.offWhite]}
              style={styles.templateModalGradient}
            >
              <View style={styles.templateModalHeader}>
                <Text style={styles.modalTitle}>Goal Templates</Text>
                <TouchableOpacity
                  style={styles.closeButton}
                  onPress={() => setTemplateModalVisible(false)}
                >
                  <Text style={styles.closeButtonText}>X</Text>
                </TouchableOpacity>
              </View>

              <Text style={styles.templateSubtitle}>
                Choose a template to get started quickly
              </Text>

              <ScrollView style={styles.templateList} showsVerticalScrollIndicator={false}>
                {GOAL_TEMPLATES.map((template, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.templateItem}
                    onPress={() => selectTemplate(template)}
                    activeOpacity={0.7}
                  >
                    <View style={styles.templateIcon}>
                      <Ionicons name={template.icon} size={24} color={colors.primaryDark} />
                    </View>
                    <View style={styles.templateInfo}>
                      <Text style={styles.templateTitle}>{template.title}</Text>
                      <Text style={styles.templateDesc} numberOfLines={1}>
                        {template.description}
                      </Text>
                      <Text style={styles.templateDays}>{template.targetDays} days</Text>
                    </View>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </LinearGradient>
          </View>
        </View>
      </Modal>

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
                  onPress={() => {
                    setModalVisible(false);
                    setNewGoal({ title: '', description: '', targetDays: '' });
                  }}
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
                    <Text style={styles.modalCreateText}>Create Goal</Text>
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
  scrollViewContent: {
    flexGrow: 1,
    paddingBottom: Platform.OS === 'ios' ? 120 : 100,
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
  summaryCard: {
    marginHorizontal: spacing['2xl'],
    marginBottom: spacing.xl,
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.lg,
  },
  summaryGradient: {
    padding: spacing.lg,
  },
  summaryContent: {
    alignItems: 'center',
  },
  summaryStats: {
    flexDirection: 'row',
    width: '100%',
    justifyContent: 'space-around',
  },
  summaryStat: {
    alignItems: 'center',
    flex: 1,
  },
  summaryValue: {
    fontSize: typography['3xl'],
    fontWeight: '700',
    color: colors.white,
  },
  summaryLabel: {
    fontSize: typography.xs,
    color: 'rgba(255,255,255,0.8)',
    marginTop: spacing.xs,
  },
  summaryDivider: {
    width: 1,
    backgroundColor: 'rgba(255,255,255,0.3)',
    marginVertical: spacing.xs,
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
  sectionTitleInline: {
    fontSize: typography['2xl'],
    fontWeight: '700',
    color: colors.text,
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
  buttonGroup: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  templateButton: {
    backgroundColor: colors.white,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
    borderWidth: 2,
    borderColor: colors.primaryDark,
  },
  templateButtonText: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.primaryDark,
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
    fontSize: 14,
    color: colors.text,
    fontWeight: '600',
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
  goalRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  goalProgressCircle: {
    marginRight: spacing.base,
  },
  progressCircleOuter: {
    width: 60,
    height: 60,
    borderRadius: 30,
    borderWidth: 4,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.white,
  },
  progressCircleText: {
    fontSize: typography.sm,
    fontWeight: '700',
  },
  goalInfo: {
    flex: 1,
  },
  goalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  goalTitle: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.text,
    flex: 1,
  },
  completedBadge: {
    backgroundColor: colors.success,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
  },
  completedText: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.white,
  },
  goalDescription: {
    fontSize: typography.sm,
    color: colors.textLight,
    lineHeight: typography.sm * 1.4,
    marginBottom: spacing.sm,
  },
  goalMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  goalMetaText: {
    fontSize: typography.sm,
    color: colors.text,
    fontWeight: '600',
  },
  goalRemaining: {
    fontSize: typography.sm,
    color: colors.textMuted,
  },
  goalProgressBar: {
    marginBottom: spacing.sm,
  },
  progressBarBackground: {
    height: 8,
    backgroundColor: colors.gray100,
    borderRadius: borderRadius.full,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: borderRadius.full,
  },
  progressGradient: {
    flex: 1,
  },
  goalActions: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.base,
    gap: spacing.sm,
  },
  updateButton: {
    flex: 1,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
    ...shadows.sm,
  },
  updateButtonGradient: {
    flexDirection: 'row',
    paddingVertical: spacing.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  updateButtonText: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.white,
  },
  deleteButton: {
    width: 40,
    height: 40,
    borderRadius: borderRadius.md,
    backgroundColor: colors.errorLight,
    justifyContent: 'center',
    alignItems: 'center',
  },
  generateButton: {
    marginHorizontal: spacing['2xl'],
    marginTop: spacing.base,
    borderRadius: borderRadius.md,
    borderWidth: 2,
    borderColor: colors.primaryDark,
    borderStyle: 'dashed',
    overflow: 'hidden',
  },
  generateButtonInner: {
    flexDirection: 'row',
    paddingVertical: spacing.base,
    alignItems: 'center',
    justifyContent: 'center',
  },
  generateButtonText: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.primaryDark,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: spacing['3xl'],
    paddingHorizontal: spacing['2xl'],
  },
  emptyIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.gray100,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.base,
  },
  emptyText: {
    fontSize: typography.base,
    color: colors.textLight,
    textAlign: 'center',
    lineHeight: typography.base * 1.5,
  },
  // Modal styles
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
  templateModalContent: {
    width: '100%',
    maxHeight: '80%',
    borderRadius: borderRadius['2xl'],
    overflow: 'hidden',
    ...shadows.xl,
  },
  templateModalGradient: {
    paddingBottom: spacing.lg,
  },
  templateModalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.gray100,
  },
  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.gray100,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.text,
  },
  templateSubtitle: {
    fontSize: typography.sm,
    color: colors.textLight,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.base,
  },
  templateList: {
    maxHeight: 400,
    paddingHorizontal: spacing.lg,
  },
  templateItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.base,
    backgroundColor: colors.gray50,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.gray100,
  },
  templateIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.base,
  },
  templateIconText: {
    fontSize: typography.xs,
    color: colors.primaryDark,
    fontWeight: '600',
  },
  templateInfo: {
    flex: 1,
  },
  templateTitle: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  templateDesc: {
    fontSize: typography.sm,
    color: colors.textLight,
    marginBottom: spacing.xs,
  },
  templateDays: {
    fontSize: typography.xs,
    color: colors.primaryDark,
    fontWeight: '600',
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
  circularBase: {
    position: 'absolute',
    borderColor: colors.gray200,
  },
  circularProgress: {
    position: 'absolute',
  },
  circularCenter: {
    position: 'absolute',
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default GoalsScreen;
