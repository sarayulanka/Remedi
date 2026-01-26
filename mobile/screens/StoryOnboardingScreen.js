import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Animated,
  Dimensions,
  Platform,
  ScrollView,
  KeyboardAvoidingView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';

const { width, height } = Dimensions.get('window');

const StoryOnboardingScreen = ({ route, navigation }) => {
  const { username, email, password } = route.params;
  
  const [currentStep, setCurrentStep] = useState(0);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;
  
  const [formData, setFormData] = useState({
    fullName: '',
    nutritionGoals: [],
    allergies: [],
    dietType: '',
    customAllergy: '',
    customDiet: '',
  });

  const steps = [
    {
      type: 'welcome',
      emoji: '👋',
      title: 'Welcome to Remedi',
      subtitle: "Your personal nutrition companion",
      message: "We're here to guide you on your journey to better health through the power of nutrition.",
      buttonText: "Let's begin",
    },
    {
      type: 'input',
      emoji: '😊',
      question: "What should we call you?",
      subtitle: "Just your first name is perfect",
      placeholder: "Your name",
      field: 'fullName',
      required: true,
    },
    {
      type: 'choice',
      emoji: '🎯',
      question: "What brings you here today?",
      subtitle: "Select all that resonate with you",
      field: 'nutritionGoals',
      multiSelect: true,
      options: [
        { value: 'Weight Management', emoji: '⚖️', color: '#10b981' },
        { value: 'Better Energy', emoji: '⚡', color: '#f59e0b' },
        { value: 'Improved Digestion', emoji: '🌿', color: '#8fd9a3' },
        { value: 'Stronger Immunity', emoji: '🛡️', color: '#3b82f6' },
        { value: 'Better Sleep', emoji: '😴', color: '#8b5cf6' },
        { value: 'Skin Health', emoji: '✨', color: '#ec4899' },
        { value: 'Heart Health', emoji: '❤️', color: '#ef4444' },
        { value: 'Mental Clarity', emoji: '🧠', color: '#06b6d4' },
      ],
    },
    {
      type: 'choice',
      emoji: '🥗',
      question: "Any food allergies?",
      subtitle: "This helps us keep you safe",
      field: 'allergies',
      multiSelect: true,
      skippable: true,
      hasCustomInput: true,
      customField: 'customAllergy',
      customPlaceholder: 'Type other allergies...',
      options: [
        { value: 'Peanuts', emoji: '🥜' },
        { value: 'Tree Nuts', emoji: '🌰' },
        { value: 'Dairy', emoji: '🥛' },
        { value: 'Eggs', emoji: '🥚' },
        { value: 'Soy', emoji: '🫘' },
        { value: 'Gluten', emoji: '🌾' },
        { value: 'Fish', emoji: '🐟' },
        { value: 'Shellfish', emoji: '🦐' },
      ],
    },
    {
      type: 'choice',
      emoji: '🍽️',
      question: "Do you follow a specific diet?",
      subtitle: "We'll personalize your experience",
      field: 'dietType',
      multiSelect: false,
      skippable: true,
      hasCustomInput: true,
      customField: 'customDiet',
      customPlaceholder: 'Specify your diet...',
      options: [
        { value: 'No Restrictions', emoji: '🍴' },
        { value: 'Vegetarian', emoji: '🥬' },
        { value: 'Vegan', emoji: '🌱' },
        { value: 'Pescatarian', emoji: '🐟' },
        { value: 'Keto', emoji: '🥑' },
        { value: 'Paleo', emoji: '🍖' },
        { value: 'Halal', emoji: '☪️' },
        { value: 'Kosher', emoji: '✡️' },
        { value: 'Other', emoji: '✏️' },
      ],
    },
    {
      type: 'celebration',
      emoji: '🎉',
      title: "You're all set!",
      subtitle: `Welcome aboard, ${formData.fullName || 'friend'}`,
      message: "Your personalized nutrition journey starts now. Let's discover the healing power of food together.",
      buttonText: "Start my journey",
    },
  ];

  const currentStepData = steps[currentStep];

  useEffect(() => {
    // Animate in on mount and step change
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
    ]).start();
  }, [currentStep]);

  const handleNext = () => {
    // Validation
    if (currentStepData.type === 'input' && currentStepData.required) {
      if (!formData[currentStepData.field]?.trim()) {
        return;
      }
    }

    // Animate out
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 0.95,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: -20,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start(() => {
      if (currentStep < steps.length - 1) {
        // Reset animations for next screen
        fadeAnim.setValue(0);
        scaleAnim.setValue(0.95);
        slideAnim.setValue(20);
        setCurrentStep(currentStep + 1);
      } else {
        handleComplete();
      }
    });
  };

  const handleSkip = () => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: -20,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start(() => {
      fadeAnim.setValue(0);
      slideAnim.setValue(20);
      setCurrentStep(currentStep + 1);
    });
  };

  const handleComplete = () => {
    // Merge custom allergies into allergies array
    let finalAllergies = [...(formData.allergies || [])];
    if (formData.customAllergy?.trim()) {
      const customItems = formData.customAllergy.split(',').map(a => a.trim()).filter(a => a);
      finalAllergies = [...finalAllergies, ...customItems];
    }

    // Use custom diet if "Other" was selected
    const finalDietType = formData.dietType === 'Other'
      ? formData.customDiet
      : formData.dietType;

    navigation.navigate('SignupComplete', {
      username,
      email,
      password,
      fullName: formData.fullName,
      nutritionGoals: formData.nutritionGoals,
      allergies: finalAllergies,
      dietType: finalDietType,
    });
  };

  const toggleSelection = (field, value) => {
    if (currentStepData.multiSelect) {
      setFormData((prev) => {
        const currentArray = prev[field] || [];
        if (currentArray.includes(value)) {
          return { ...prev, [field]: currentArray.filter((item) => item !== value) };
        } else {
          return { ...prev, [field]: [...currentArray, value] };
        }
      });
    } else {
      setFormData((prev) => ({ ...prev, [field]: value }));
    }
  };

  const renderStep = () => {
    const animatedStyle = {
      opacity: fadeAnim,
      transform: [
        { scale: scaleAnim },
        { translateY: slideAnim },
      ],
    };

    switch (currentStepData.type) {
      case 'welcome':
      case 'celebration':
        return (
          <Animated.View style={[styles.stepContainer, animatedStyle]}>
            <View style={styles.emojiContainer}>
              <Text style={styles.bigEmoji}>{currentStepData.emoji}</Text>
              <View style={styles.emojiGlow} />
            </View>
            <Text style={styles.title}>{currentStepData.title}</Text>
            <Text style={styles.subtitle}>{currentStepData.subtitle}</Text>
            {currentStepData.message && (
              <Text style={styles.message}>{currentStepData.message}</Text>
            )}
          </Animated.View>
        );

      case 'input':
        return (
          <Animated.View style={[styles.stepContainer, animatedStyle]}>
            <Text style={styles.emoji}>{currentStepData.emoji}</Text>
            <Text style={styles.question}>{currentStepData.question}</Text>
            <Text style={styles.subtitle}>{currentStepData.subtitle}</Text>
            
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                placeholder={currentStepData.placeholder}
                value={formData[currentStepData.field]}
                onChangeText={(text) =>
                  setFormData({ ...formData, [currentStepData.field]: text })
                }
                placeholderTextColor={colors.textMuted}
                autoFocus
                onSubmitEditing={handleNext}
              />
            </View>
          </Animated.View>
        );

      case 'choice':
        const showCustomInput = currentStepData.hasCustomInput && (
          currentStepData.multiSelect ||
          formData[currentStepData.field] === 'Other'
        );
        return (
          <Animated.View style={[styles.stepContainer, animatedStyle]}>
            <Text style={styles.emoji}>{currentStepData.emoji}</Text>
            <Text style={styles.question}>{currentStepData.question}</Text>
            <Text style={styles.subtitle}>{currentStepData.subtitle}</Text>

            <ScrollView
              style={styles.optionsScrollView}
              contentContainerStyle={styles.optionsContainer}
              showsVerticalScrollIndicator={false}
            >
              {currentStepData.options.map((option, index) => {
                const isSelected = currentStepData.multiSelect
                  ? formData[currentStepData.field]?.includes(option.value)
                  : formData[currentStepData.field] === option.value;

                return (
                  <TouchableOpacity
                    key={option.value}
                    style={[
                      styles.optionCard,
                      isSelected && styles.optionCardSelected,
                    ]}
                    onPress={() => toggleSelection(currentStepData.field, option.value)}
                    activeOpacity={0.7}
                  >
                    <LinearGradient
                      colors={isSelected ? [colors.primary, colors.primaryLight] : [colors.white, colors.white]}
                      style={styles.optionGradient}
                    >
                      <View style={styles.optionContent}>
                        <View style={[styles.optionEmojiContainer, isSelected && styles.optionEmojiContainerSelected]}>
                          <Text style={styles.optionEmoji}>{option.emoji}</Text>
                        </View>
                        <Text style={[styles.optionText, isSelected && styles.optionTextSelected]}>
                          {option.value}
                        </Text>
                        {isSelected && (
                          <View style={styles.checkmarkContainer}>
                            <Text style={styles.checkmark}>✓</Text>
                          </View>
                        )}
                      </View>
                    </LinearGradient>
                  </TouchableOpacity>
                );
              })}

              {/* Custom Input Field */}
              {showCustomInput && (
                <View style={styles.customInputWrapper}>
                  <Text style={styles.customInputLabel}>
                    {currentStepData.multiSelect ? 'Add other:' : 'Specify:'}
                  </Text>
                  <TextInput
                    style={styles.customInputField}
                    placeholder={currentStepData.customPlaceholder}
                    placeholderTextColor={colors.textMuted}
                    value={formData[currentStepData.customField]}
                    onChangeText={(text) =>
                      setFormData({ ...formData, [currentStepData.customField]: text })
                    }
                  />
                </View>
              )}
            </ScrollView>
          </Animated.View>
        );

      default:
        return null;
    }
  };

  const canProceed = () => {
    if (currentStepData.type === 'input' && currentStepData.required) {
      return formData[currentStepData.field]?.trim().length > 0;
    }
    return true;
  };

  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <LinearGradient colors={gradients.main} style={styles.container}>
      <KeyboardAvoidingView 
        style={styles.container} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBarBackground}>
            <Animated.View
              style={[
                styles.progressBarFill,
                {
                  width: `${progress}%`,
                },
              ]}
            >
              <LinearGradient
                colors={gradients.button}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.progressGradient}
              />
            </Animated.View>
          </View>
          <Text style={styles.progressText}>
            {currentStep + 1} of {steps.length}
          </Text>
        </View>

        {/* Content */}
        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {renderStep()}
        </ScrollView>

        {/* Buttons */}
        <View style={styles.buttonContainer}>
          {currentStepData.skippable && (
            <TouchableOpacity
              style={styles.skipButton}
              onPress={handleSkip}
              activeOpacity={0.7}
            >
              <Text style={styles.skipText}>Skip for now</Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={[
              styles.nextButton,
              !canProceed() && styles.nextButtonDisabled,
            ]}
            onPress={handleNext}
            disabled={!canProceed()}
            activeOpacity={0.8}
          >
            <LinearGradient
              colors={canProceed() ? gradients.button : [colors.gray200, colors.gray300]}
              style={styles.nextButtonGradient}
            >
              <Text style={[styles.nextButtonText, !canProceed() && styles.nextButtonTextDisabled]}>
                {currentStepData.buttonText || 'Continue'}
              </Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  progressContainer: {
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingHorizontal: spacing['2xl'],
    paddingBottom: spacing.lg,
  },
  progressBarBackground: {
    height: 6,
    backgroundColor: colors.gray100,
    borderRadius: borderRadius.full,
    overflow: 'hidden',
    marginBottom: spacing.sm,
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
    color: colors.textMuted,
    textAlign: 'center',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: spacing['2xl'],
    paddingVertical: spacing.xl,
  },
  stepContainer: {
    alignItems: 'center',
    width: '100%',
  },
  emojiContainer: {
    position: 'relative',
    marginBottom: spacing['3xl'],
  },
  bigEmoji: {
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
  emoji: {
    fontSize: 72,
    marginBottom: spacing.xl,
    textAlign: 'center',
  },
  title: {
    fontSize: typography['4xl'],
    fontWeight: '800',
    color: colors.text,
    textAlign: 'center',
    marginBottom: spacing.md,
    letterSpacing: -0.5,
  },
  question: {
    fontSize: typography['2xl'],
    fontWeight: '700',
    color: colors.text,
    textAlign: 'center',
    marginBottom: spacing.md,
    letterSpacing: -0.3,
  },
  subtitle: {
    fontSize: typography.base,
    color: colors.textLight,
    textAlign: 'center',
    marginBottom: spacing.lg,
    lineHeight: typography.base * 1.5,
  },
  message: {
    fontSize: typography.base,
    color: colors.textLight,
    textAlign: 'center',
    lineHeight: typography.base * 1.6,
    marginTop: spacing.lg,
    paddingHorizontal: spacing.base,
  },
  inputContainer: {
    width: '100%',
    marginTop: spacing.xl,
  },
  input: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.xl,
    padding: spacing.xl,
    fontSize: typography.xl,
    color: colors.text,
    textAlign: 'center',
    fontWeight: '600',
    ...shadows.lg,
    borderWidth: 2,
    borderColor: colors.gray100,
  },
  optionsScrollView: {
    width: '100%',
    maxHeight: height * 0.5,
    marginTop: spacing.lg,
  },
  optionsContainer: {
    paddingBottom: spacing.lg,
  },
  optionCard: {
    marginBottom: spacing.md,
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.md,
  },
  optionCardSelected: {
    ...shadows.lg,
  },
  optionGradient: {
    borderRadius: borderRadius.xl,
  },
  optionContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.lg,
    borderWidth: 2,
    borderColor: 'transparent',
    borderRadius: borderRadius.xl,
  },
  optionEmojiContainer: {
    width: 48,
    height: 48,
    borderRadius: borderRadius.md,
    backgroundColor: colors.gray50,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.base,
  },
  optionEmojiContainerSelected: {
    backgroundColor: colors.white,
  },
  optionEmoji: {
    fontSize: 24,
  },
  optionText: {
    fontSize: typography.base,
    color: colors.text,
    flex: 1,
    fontWeight: '600',
  },
  optionTextSelected: {
    color: colors.white,
    fontWeight: '700',
  },
  checkmarkContainer: {
    width: 24,
    height: 24,
    borderRadius: borderRadius.full,
    backgroundColor: colors.white,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkmark: {
    fontSize: 16,
    color: colors.primaryDark,
    fontWeight: '700',
  },
  buttonContainer: {
    paddingHorizontal: spacing['2xl'],
    paddingBottom: Platform.OS === 'ios' ? spacing['3xl'] : spacing.xl,
    paddingTop: spacing.base,
  },
  skipButton: {
    paddingVertical: spacing.base,
    marginBottom: spacing.sm,
  },
  skipText: {
    fontSize: typography.base,
    color: colors.textLight,
    textAlign: 'center',
    fontWeight: '600',
  },
  nextButton: {
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.lg,
  },
  nextButtonDisabled: {
    opacity: 0.5,
    ...shadows.sm,
  },
  nextButtonGradient: {
    paddingVertical: spacing.lg,
    alignItems: 'center',
  },
  nextButtonText: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.white,
  },
  nextButtonTextDisabled: {
    color: colors.textMuted,
  },
  // Custom input styles
  customInputWrapper: {
    marginTop: spacing.lg,
    paddingTop: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.gray100,
  },
  customInputLabel: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.textLight,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  customInputField: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    fontSize: typography.base,
    color: colors.text,
    textAlign: 'center',
    borderWidth: 1,
    borderColor: colors.gray200,
    ...shadows.sm,
  },
});

export default StoryOnboardingScreen;
