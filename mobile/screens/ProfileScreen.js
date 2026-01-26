import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Modal,
  Platform,
  RefreshControl,
  TextInput,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';
import { authAPI, gamificationAPI } from '../services/api';

const NUTRITION_GOALS = [
  { id: 'weight_management', label: 'Weight Management', icon: 'scale-outline' },
  { id: 'energy_boost', label: 'Boost Energy', icon: 'flash-outline' },
  { id: 'better_digestion', label: 'Better Digestion', icon: 'leaf-outline' },
  { id: 'skin_health', label: 'Skin Health', icon: 'sparkles-outline' },
  { id: 'immune_support', label: 'Immune Support', icon: 'shield-checkmark-outline' },
  { id: 'muscle_building', label: 'Build Muscle', icon: 'barbell-outline' },
  { id: 'heart_health', label: 'Heart Health', icon: 'heart-outline' },
  { id: 'mental_clarity', label: 'Mental Clarity', icon: 'bulb-outline' },
];

const ALLERGIES = [
  { id: 'peanuts', label: 'Peanuts', icon: 'nutrition-outline' },
  { id: 'tree_nuts', label: 'Tree Nuts', icon: 'nutrition-outline' },
  { id: 'dairy', label: 'Dairy', icon: 'water-outline' },
  { id: 'eggs', label: 'Eggs', icon: 'egg-outline' },
  { id: 'gluten', label: 'Gluten', icon: 'restaurant-outline' },
  { id: 'soy', label: 'Soy', icon: 'leaf-outline' },
  { id: 'shellfish', label: 'Shellfish', icon: 'fish-outline' },
  { id: 'fish', label: 'Fish', icon: 'fish-outline' },
];

const DIET_TYPES = [
  { id: 'none', label: 'No Preference', icon: 'checkmark-circle-outline' },
  { id: 'vegetarian', label: 'Vegetarian', icon: 'leaf-outline' },
  { id: 'vegan', label: 'Vegan', icon: 'flower-outline' },
  { id: 'pescatarian', label: 'Pescatarian', icon: 'fish-outline' },
  { id: 'keto', label: 'Keto', icon: 'flame-outline' },
  { id: 'paleo', label: 'Paleo', icon: 'nutrition-outline' },
  { id: 'mediterranean', label: 'Mediterranean', icon: 'sunny-outline' },
  { id: 'low_carb', label: 'Low Carb', icon: 'trending-down-outline' },
  { id: 'other', label: 'Other (specify)', icon: 'create-outline' },
];

const ProfileScreen = ({ onLogout }) => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState(null);
  const [streak, setStreak] = useState(null);
  const [badges, setBadges] = useState([]);

  // Edit modals
  const [goalsModalVisible, setGoalsModalVisible] = useState(false);
  const [allergiesModalVisible, setAllergiesModalVisible] = useState(false);
  const [dietModalVisible, setDietModalVisible] = useState(false);

  // Editable state
  const [selectedGoals, setSelectedGoals] = useState([]);
  const [selectedAllergies, setSelectedAllergies] = useState([]);
  const [selectedDiet, setSelectedDiet] = useState('none');
  const [customAllergy, setCustomAllergy] = useState('');
  const [customDiet, setCustomDiet] = useState('');
  const [healthConditions, setHealthConditions] = useState([]);

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    try {
      setLoading(true);
      const [profileData, streakData, badgesData] = await Promise.all([
        authAPI.getProfile(),
        gamificationAPI.getStreak(),
        gamificationAPI.getBadges(),
      ]);

      setProfile(profileData);
      setStreak(streakData);
      setBadges(badgesData || []);

      // Set editable values from profile or dietary preferences
      const prefs = profileData.dietaryPreferences || {};
      setSelectedGoals(prefs.preferences || profileData.nutritionGoals || []);
      setHealthConditions(profileData.healthConditions || []);

      // Handle allergies - separate predefined and custom
      const allAllergies = prefs.allergies || profileData.allergies || [];
      const predefinedIds = ALLERGIES.map(a => a.id);
      const predefined = allAllergies.filter(a => predefinedIds.includes(a));
      const custom = allAllergies.filter(a => !predefinedIds.includes(a));
      setSelectedAllergies(predefined);
      setCustomAllergy(custom.join(', '));

      // Handle diet type - check if it's predefined or custom
      const dietValue = prefs.dietType || profileData.dietType || 'none';
      const predefinedDiets = DIET_TYPES.map(d => d.id);
      if (predefinedDiets.includes(dietValue)) {
        setSelectedDiet(dietValue);
        setCustomDiet('');
      } else if (dietValue && dietValue !== 'none') {
        setSelectedDiet('other');
        setCustomDiet(dietValue);
      } else {
        setSelectedDiet('none');
      }
    } catch (error) {
      console.error('Error loading profile:', error);
      Alert.alert('Error', 'Failed to load profile data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadProfileData();
  };

  const toggleGoal = (goalId) => {
    setSelectedGoals((prev) =>
      prev.includes(goalId)
        ? prev.filter((g) => g !== goalId)
        : [...prev, goalId]
    );
  };

  const toggleAllergy = (allergyId) => {
    setSelectedAllergies((prev) =>
      prev.includes(allergyId)
        ? prev.filter((a) => a !== allergyId)
        : [...prev, allergyId]
    );
  };

  const savePreferences = async () => {
    try {
      setSaving(true);

      // Combine predefined and custom allergies
      let allAllergies = [...selectedAllergies];
      if (customAllergy.trim()) {
        const customItems = customAllergy.split(',').map(a => a.trim()).filter(a => a);
        allAllergies = [...allAllergies, ...customItems];
      }

      // Get the actual diet type value
      const dietTypeValue = selectedDiet === 'other' ? customDiet : selectedDiet;

      await authAPI.updateDietaryPreferences({
        preferences: selectedGoals,
        allergies: allAllergies,
        dietType: dietTypeValue,
        restrictions: [],
      });

      // Update local profile
      setProfile((prev) => ({
        ...prev,
        nutritionGoals: selectedGoals,
        allergies: allAllergies,
        dietType: dietTypeValue,
      }));

      setGoalsModalVisible(false);
      setAllergiesModalVisible(false);
      setDietModalVisible(false);

      Alert.alert('Saved', 'Your preferences have been updated');
    } catch (error) {
      console.error('Error saving preferences:', error);
      Alert.alert('Error', 'Failed to save preferences');
    } finally {
      setSaving(false);
    }
  };

  const handleLogoutPress = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Logout', style: 'destructive', onPress: onLogout },
      ]
    );
  };

  const renderSettingItem = (title, value, onPress, iconName) => (
    <TouchableOpacity
      style={styles.settingItem}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <LinearGradient
        colors={[colors.white, colors.offWhite]}
        style={styles.settingGradient}
      >
        <View style={styles.settingContent}>
          <View style={styles.settingIconContainer}>
            <Ionicons name={iconName} size={22} color={colors.primaryDark} />
          </View>
          <View style={styles.settingTextContainer}>
            <Text style={styles.settingTitle}>{title}</Text>
            <Text style={styles.settingValue} numberOfLines={1}>
              {value || 'Not set'}
            </Text>
          </View>
        </View>
        <View style={styles.settingArrowContainer}>
          <Text style={styles.settingArrowText}>Edit</Text>
          <Ionicons name="chevron-forward" size={16} color={colors.primaryDark} />
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );

  const renderModal = (visible, setVisible, title, content) => (
    <Modal
      animationType="slide"
      transparent={true}
      visible={visible}
      onRequestClose={() => setVisible(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContainer}>
          <LinearGradient
            colors={[colors.white, colors.offWhite]}
            style={styles.modalGradient}
          >
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{title}</Text>
              <TouchableOpacity
                onPress={() => setVisible(false)}
                style={styles.modalCloseButton}
              >
                <Ionicons name="close" size={20} color={colors.text} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalContent} showsVerticalScrollIndicator={false}>
              {content}
            </ScrollView>

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.modalCancelButton}
                onPress={() => setVisible(false)}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.modalSaveButton}
                onPress={savePreferences}
                disabled={saving}
              >
                <LinearGradient
                  colors={gradients.button}
                  style={styles.modalSaveGradient}
                >
                  {saving ? (
                    <ActivityIndicator color={colors.white} size="small" />
                  ) : (
                    <Text style={styles.modalSaveText}>Save Changes</Text>
                  )}
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </LinearGradient>
        </View>
      </View>
    </Modal>
  );

  if (loading) {
    return (
      <LinearGradient colors={gradients.main} style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primaryDark} />
          <Text style={styles.loadingText}>Loading profile...</Text>
        </View>
      </LinearGradient>
    );
  }

  const goalsDisplay = selectedGoals.length > 0
    ? selectedGoals.map((g) => NUTRITION_GOALS.find((ng) => ng.id === g)?.label || g).join(', ')
    : 'Tap to set your goals';

  // Build allergies display including custom ones
  const allergyLabels = selectedAllergies.map((a) => ALLERGIES.find((al) => al.id === a)?.label || a);
  if (customAllergy.trim()) {
    allergyLabels.push(...customAllergy.split(',').map(a => a.trim()).filter(a => a));
  }
  const allergiesDisplay = allergyLabels.length > 0 ? allergyLabels.join(', ') : 'None';

  // Build diet display including custom
  const dietDisplay = selectedDiet === 'other'
    ? (customDiet || 'Custom diet')
    : (DIET_TYPES.find((d) => d.id === selectedDiet)?.label || 'Not set');

  // Health conditions display
  const healthConditionsDisplay = healthConditions.length > 0
    ? healthConditions.join(', ')
    : 'None specified';

  return (
    <LinearGradient colors={gradients.main} style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollViewContent}
        showsVerticalScrollIndicator={false}
        bounces={true}
        alwaysBounceVertical={true}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.primaryDark}
          />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Profile</Text>
          <Text style={styles.headerSubtitle}>Manage your account and preferences</Text>
        </View>

        {/* Profile Card */}
        <View style={styles.profileCard}>
          <LinearGradient
            colors={gradients.button}
            style={styles.profileGradient}
          >
            <View style={styles.profileAvatar}>
              <Text style={styles.avatarText}>
                {profile?.username?.[0]?.toUpperCase() || 'U'}
              </Text>
            </View>
            <Text style={styles.profileName}>{profile?.username || 'User'}</Text>
            <Text style={styles.profileEmail}>{profile?.email || ''}</Text>

            {/* Stats Row */}
            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{streak?.currentStreak || 0}</Text>
                <Text style={styles.statLabel}>Day Streak</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{badges.length}</Text>
                <Text style={styles.statLabel}>Badges</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{streak?.longestStreak || 0}</Text>
                <Text style={styles.statLabel}>Best Streak</Text>
              </View>
            </View>

            {/* Streak Status */}
            {streak?.streakAtRisk && !streak?.checkedInToday && (
              <View style={styles.streakWarning}>
                <Ionicons name="warning" size={16} color="#f59e0b" />
                <Text style={styles.streakWarningText}>Check in today to keep your streak!</Text>
              </View>
            )}
          </LinearGradient>
        </View>

        {/* Settings Section */}
        <Text style={styles.sectionTitle}>Dietary Preferences</Text>

        {renderSettingItem(
          'Nutrition Goals',
          goalsDisplay,
          () => setGoalsModalVisible(true),
          'flag-outline'
        )}

        {renderSettingItem(
          'Food Allergies',
          allergiesDisplay,
          () => setAllergiesModalVisible(true),
          'warning-outline'
        )}

        {renderSettingItem(
          'Diet Type',
          dietDisplay,
          () => setDietModalVisible(true),
          'nutrition-outline'
        )}

        {/* Health Conditions - Display Only */}
        {healthConditions.length > 0 && (
          <View style={styles.settingItem}>
            <LinearGradient
              colors={[colors.white, colors.offWhite]}
              style={styles.settingGradient}
            >
              <View style={styles.settingContent}>
                <View style={styles.settingIconContainer}>
                  <Ionicons name="medical-outline" size={22} color={colors.primaryDark} />
                </View>
                <View style={styles.settingTextContainer}>
                  <Text style={styles.settingTitle}>Health Conditions</Text>
                  <Text style={styles.settingValue} numberOfLines={2}>
                    {healthConditionsDisplay}
                  </Text>
                </View>
              </View>
            </LinearGradient>
          </View>
        )}

        {/* Account Section */}
        <Text style={styles.sectionTitle}>Account</Text>

        <TouchableOpacity
          style={styles.settingItem}
          onPress={() => Alert.alert('Coming Soon', 'App Settings will be available in a future update')}
          activeOpacity={0.7}
        >
          <LinearGradient
            colors={[colors.white, colors.offWhite]}
            style={styles.settingGradient}
          >
            <View style={styles.settingContent}>
              <View style={styles.settingIconContainer}>
                <Ionicons name="settings-outline" size={22} color={colors.textLight} />
              </View>
              <View style={styles.settingTextContainer}>
                <Text style={styles.settingTitle}>App Settings</Text>
                <Text style={styles.settingValue}>Notifications, theme, privacy</Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={16} color={colors.textMuted} />
          </LinearGradient>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.settingItem}
          onPress={() => Alert.alert('About Remedi', 'Remedi v1.0.0\n\nYour personal nutrition assistant helping you find food resources and natural remedies.\n\nMade with care for your health.')}
          activeOpacity={0.7}
        >
          <LinearGradient
            colors={[colors.white, colors.offWhite]}
            style={styles.settingGradient}
          >
            <View style={styles.settingContent}>
              <View style={styles.settingIconContainer}>
                <Ionicons name="information-circle-outline" size={22} color={colors.textLight} />
              </View>
              <View style={styles.settingTextContainer}>
                <Text style={styles.settingTitle}>About</Text>
                <Text style={styles.settingValue}>Version 1.0.0</Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={16} color={colors.textMuted} />
          </LinearGradient>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.logoutButton}
          onPress={handleLogoutPress}
          activeOpacity={0.7}
        >
          <LinearGradient
            colors={[colors.errorLight, '#fff5f5']}
            style={styles.logoutGradient}
          >
            <Ionicons name="log-out-outline" size={20} color={colors.error} />
            <Text style={styles.logoutText}>Logout</Text>
          </LinearGradient>
        </TouchableOpacity>

      </ScrollView>

      {/* Goals Modal */}
      {renderModal(
        goalsModalVisible,
        setGoalsModalVisible,
        'Select Your Goals',
        <View style={styles.optionsContainer}>
          <Text style={styles.modalDescription}>
            Choose the health goals you want to focus on. We'll personalize your recommendations.
          </Text>
          {NUTRITION_GOALS.map((goal) => (
            <TouchableOpacity
              key={goal.id}
              style={[
                styles.optionItem,
                selectedGoals.includes(goal.id) && styles.optionItemSelected,
              ]}
              onPress={() => toggleGoal(goal.id)}
            >
              <View style={styles.optionLeft}>
                <Ionicons
                  name={goal.icon}
                  size={20}
                  color={selectedGoals.includes(goal.id) ? colors.primaryDark : colors.textLight}
                />
                <Text style={[
                  styles.optionText,
                  selectedGoals.includes(goal.id) && styles.optionTextSelected,
                ]}>
                  {goal.label}
                </Text>
              </View>
              {selectedGoals.includes(goal.id) && (
                <Ionicons name="checkmark-circle" size={22} color={colors.primaryDark} />
              )}
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Allergies Modal */}
      {renderModal(
        allergiesModalVisible,
        setAllergiesModalVisible,
        'Food Allergies',
        <View style={styles.optionsContainer}>
          <Text style={styles.modalDescription}>
            Select any foods you're allergic to. We'll help you avoid them in recommendations.
          </Text>
          {ALLERGIES.map((allergy) => (
            <TouchableOpacity
              key={allergy.id}
              style={[
                styles.optionItem,
                selectedAllergies.includes(allergy.id) && styles.optionItemSelected,
              ]}
              onPress={() => toggleAllergy(allergy.id)}
            >
              <View style={styles.optionLeft}>
                <Ionicons
                  name={allergy.icon}
                  size={20}
                  color={selectedAllergies.includes(allergy.id) ? colors.primaryDark : colors.textLight}
                />
                <Text style={[
                  styles.optionText,
                  selectedAllergies.includes(allergy.id) && styles.optionTextSelected,
                ]}>
                  {allergy.label}
                </Text>
              </View>
              {selectedAllergies.includes(allergy.id) && (
                <Ionicons name="checkmark-circle" size={22} color={colors.primaryDark} />
              )}
            </TouchableOpacity>
          ))}

          {/* Custom Allergy Input */}
          <View style={styles.customInputContainer}>
            <Text style={styles.customInputLabel}>Other allergies (comma separated):</Text>
            <TextInput
              style={styles.customInput}
              value={customAllergy}
              onChangeText={setCustomAllergy}
              placeholder="e.g., Sesame, Mustard, Celery"
              placeholderTextColor={colors.textMuted}
            />
          </View>
        </View>
      )}

      {/* Diet Type Modal */}
      {renderModal(
        dietModalVisible,
        setDietModalVisible,
        'Diet Type',
        <View style={styles.optionsContainer}>
          <Text style={styles.modalDescription}>
            Select your dietary preference. This helps us filter recipe recommendations.
          </Text>
          {DIET_TYPES.map((diet) => (
            <TouchableOpacity
              key={diet.id}
              style={[
                styles.optionItem,
                selectedDiet === diet.id && styles.optionItemSelected,
              ]}
              onPress={() => setSelectedDiet(diet.id)}
            >
              <View style={styles.optionLeft}>
                <Ionicons
                  name={diet.icon}
                  size={20}
                  color={selectedDiet === diet.id ? colors.primaryDark : colors.textLight}
                />
                <Text style={[
                  styles.optionText,
                  selectedDiet === diet.id && styles.optionTextSelected,
                ]}>
                  {diet.label}
                </Text>
              </View>
              {selectedDiet === diet.id && (
                <Ionicons name="checkmark-circle" size={22} color={colors.primaryDark} />
              )}
            </TouchableOpacity>
          ))}

          {/* Custom Diet Input - shown when "Other" is selected */}
          {selectedDiet === 'other' && (
            <View style={styles.customInputContainer}>
              <Text style={styles.customInputLabel}>Specify your diet:</Text>
              <TextInput
                style={styles.customInput}
                value={customDiet}
                onChangeText={setCustomDiet}
                placeholder="e.g., Whole30, FODMAP, Carnivore"
                placeholderTextColor={colors.textMuted}
              />
            </View>
          )}
        </View>
      )}
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: spacing.base,
    fontSize: typography.base,
    color: colors.textLight,
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
  profileCard: {
    marginHorizontal: spacing['2xl'],
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    marginBottom: spacing.xl,
    ...shadows.lg,
  },
  profileGradient: {
    padding: spacing.xl,
    alignItems: 'center',
  },
  profileAvatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.white,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.base,
    ...shadows.md,
  },
  avatarText: {
    fontSize: typography['3xl'],
    fontWeight: '700',
    color: colors.primaryDark,
  },
  profileName: {
    fontSize: typography['2xl'],
    fontWeight: '700',
    color: colors.white,
    marginBottom: spacing.xs,
  },
  profileEmail: {
    fontSize: typography.sm,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: spacing.lg,
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    width: '100%',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: typography['2xl'],
    fontWeight: '700',
    color: colors.white,
  },
  statLabel: {
    fontSize: typography.xs,
    color: 'rgba(255,255,255,0.8)',
    marginTop: spacing.xs,
  },
  statDivider: {
    width: 1,
    backgroundColor: 'rgba(255,255,255,0.3)',
    marginVertical: spacing.xs,
  },
  streakWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.base,
    backgroundColor: 'rgba(255,255,255,0.9)',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.base,
    borderRadius: borderRadius.md,
    gap: spacing.xs,
  },
  streakWarningText: {
    fontSize: typography.sm,
    color: '#d97706',
    fontWeight: '600',
  },
  sectionTitle: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.text,
    marginHorizontal: spacing['2xl'],
    marginBottom: spacing.base,
    marginTop: spacing.base,
  },
  settingItem: {
    marginHorizontal: spacing['2xl'],
    marginBottom: spacing.sm,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.sm,
  },
  settingGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.base,
  },
  settingContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.base,
  },
  settingTextContainer: {
    flex: 1,
  },
  settingTitle: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 2,
  },
  settingValue: {
    fontSize: typography.sm,
    color: colors.textLight,
  },
  settingArrowContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  settingArrowText: {
    fontSize: typography.sm,
    color: colors.primaryDark,
    fontWeight: '600',
  },
  logoutButton: {
    marginHorizontal: spacing['2xl'],
    marginTop: spacing.lg,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.sm,
  },
  logoutGradient: {
    flexDirection: 'row',
    padding: spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  logoutText: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.error,
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: colors.white,
    borderTopLeftRadius: borderRadius['2xl'],
    borderTopRightRadius: borderRadius['2xl'],
    maxHeight: '85%',
    overflow: 'hidden',
  },
  modalGradient: {
    paddingBottom: Platform.OS === 'ios' ? spacing['3xl'] : spacing.xl,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.gray100,
  },
  modalTitle: {
    fontSize: typography.xl,
    fontWeight: '700',
    color: colors.text,
  },
  modalCloseButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.gray100,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    padding: spacing.lg,
    maxHeight: 400,
  },
  modalDescription: {
    fontSize: typography.sm,
    color: colors.textLight,
    marginBottom: spacing.lg,
    lineHeight: typography.sm * 1.5,
  },
  modalActions: {
    flexDirection: 'row',
    padding: spacing.lg,
    gap: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.gray100,
  },
  modalCancelButton: {
    flex: 1,
    backgroundColor: colors.gray100,
    padding: spacing.base,
    borderRadius: borderRadius.lg,
    alignItems: 'center',
  },
  modalCancelText: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.text,
  },
  modalSaveButton: {
    flex: 1,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
  },
  modalSaveGradient: {
    padding: spacing.base,
    alignItems: 'center',
  },
  modalSaveText: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.white,
  },
  optionsContainer: {
    gap: spacing.sm,
  },
  optionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.base,
    backgroundColor: colors.gray50,
    borderRadius: borderRadius.md,
    borderWidth: 2,
    borderColor: colors.gray100,
  },
  optionItemSelected: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primaryDark,
  },
  optionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  optionText: {
    fontSize: typography.base,
    color: colors.text,
    fontWeight: '500',
  },
  optionTextSelected: {
    fontWeight: '700',
    color: colors.primaryDark,
  },
  // Custom input styles
  customInputContainer: {
    marginTop: spacing.lg,
    paddingTop: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.gray100,
  },
  customInputLabel: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  customInput: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.gray200,
    borderRadius: borderRadius.md,
    padding: spacing.base,
    fontSize: typography.base,
    color: colors.text,
  },
});

export default ProfileScreen;
