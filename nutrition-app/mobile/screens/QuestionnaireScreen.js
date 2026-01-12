import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, gradients } from '../theme/colors';

const QuestionnaireScreen = ({ route, navigation }) => {
  const { username, email, password } = route.params;
  
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    fullName: '',
    age: '',
    gender: '',
    location: '',
    nutritionGoals: [],
    healthConditions: [],
    allergies: [],
    dietType: '',
  });

  const totalSteps = 5;

  // Predefined options
  const genderOptions = ['Male', 'Female', 'Non-binary', 'Prefer not to say'];
  
  const goalOptions = [
    'Weight Management',
    'Better Energy',
    'Improved Digestion',
    'Stronger Immunity',
    'Better Sleep',
    'Skin Health',
    'Heart Health',
    'Mental Clarity',
  ];

  const healthConditionOptions = [
    'Diabetes',
    'High Blood Pressure',
    'High Cholesterol',
    'Digestive Issues',
    'Skin Conditions',
    'Allergies',
    'None',
  ];

  const allergyOptions = [
    'Peanuts',
    'Tree Nuts',
    'Milk/Dairy',
    'Eggs',
    'Soy',
    'Wheat/Gluten',
    'Fish',
    'Shellfish',
    'None',
  ];

  const dietTypeOptions = [
    'No Restrictions',
    'Vegetarian',
    'Vegan',
    'Pescatarian',
    'Keto',
    'Paleo',
    'Halal',
    'Kosher',
  ];

  const toggleSelection = (field, value) => {
    setFormData((prev) => {
      const currentArray = prev[field];
      if (currentArray.includes(value)) {
        return { ...prev, [field]: currentArray.filter((item) => item !== value) };
      } else {
        return { ...prev, [field]: [...currentArray, value] };
      }
    });
  };

  const handleNext = () => {
    // Validation for each step
    if (currentStep === 1 && !formData.fullName.trim()) {
      Alert.alert('Required', 'Please enter your name');
      return;
    }
    if (currentStep === 2 && !formData.gender) {
      Alert.alert('Required', 'Please select your gender');
      return;
    }

    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    // Navigate to signup with all collected data
    navigation.navigate('SignupComplete', {
      username,
      email,
      password,
      ...formData,
      age: formData.age ? parseInt(formData.age) : null,
    });
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Let's get to know you! 👋</Text>
            <Text style={styles.stepSubtitle}>What's your name?</Text>
            
            <TextInput
              style={styles.input}
              placeholder="Full Name"
              value={formData.fullName}
              onChangeText={(text) => setFormData({ ...formData, fullName: text })}
              placeholderTextColor={colors.textLight}
            />

            <Text style={styles.stepSubtitle}>How old are you?</Text>
            <TextInput
              style={styles.input}
              placeholder="Age (optional)"
              value={formData.age}
              onChangeText={(text) => setFormData({ ...formData, age: text })}
              keyboardType="numeric"
              placeholderTextColor={colors.textLight}
            />

            <Text style={styles.stepSubtitle}>Where are you located?</Text>
            <TextInput
              style={styles.input}
              placeholder="City, State (optional)"
              value={formData.location}
              onChangeText={(text) => setFormData({ ...formData, location: text })}
              placeholderTextColor={colors.textLight}
            />
          </View>
        );

      case 2:
        return (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>About You 🧑‍⚕️</Text>
            <Text style={styles.stepSubtitle}>What's your gender?</Text>
            
            <View style={styles.optionsGrid}>
              {genderOptions.map((option) => (
                <TouchableOpacity
                  key={option}
                  style={[
                    styles.optionButton,
                    formData.gender === option && styles.optionButtonSelected,
                  ]}
                  onPress={() => setFormData({ ...formData, gender: option })}
                >
                  <Text
                    style={[
                      styles.optionText,
                      formData.gender === option && styles.optionTextSelected,
                    ]}
                  >
                    {option}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        );

      case 3:
        return (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Your Goals 🎯</Text>
            <Text style={styles.stepSubtitle}>
              What do you want to achieve? (Select all that apply)
            </Text>
            
            <ScrollView style={styles.optionsScroll}>
              {goalOptions.map((option) => (
                <TouchableOpacity
                  key={option}
                  style={[
                    styles.checkboxOption,
                    formData.nutritionGoals.includes(option) && styles.checkboxOptionSelected,
                  ]}
                  onPress={() => toggleSelection('nutritionGoals', option)}
                >
                  <View style={styles.checkbox}>
                    {formData.nutritionGoals.includes(option) && (
                      <Text style={styles.checkmark}>✓</Text>
                    )}
                  </View>
                  <Text
                    style={[
                      styles.checkboxText,
                      formData.nutritionGoals.includes(option) && styles.checkboxTextSelected,
                    ]}
                  >
                    {option}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        );

      case 4:
        return (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Health Information 🏥</Text>
            <Text style={styles.stepSubtitle}>
              Do you have any health conditions? (Select all that apply)
            </Text>
            
            <ScrollView style={styles.optionsScroll}>
              {healthConditionOptions.map((option) => (
                <TouchableOpacity
                  key={option}
                  style={[
                    styles.checkboxOption,
                    formData.healthConditions.includes(option) && styles.checkboxOptionSelected,
                  ]}
                  onPress={() => toggleSelection('healthConditions', option)}
                >
                  <View style={styles.checkbox}>
                    {formData.healthConditions.includes(option) && (
                      <Text style={styles.checkmark}>✓</Text>
                    )}
                  </View>
                  <Text
                    style={[
                      styles.checkboxText,
                      formData.healthConditions.includes(option) && styles.checkboxTextSelected,
                    ]}
                  >
                    {option}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        );

      case 5:
        return (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Dietary Preferences 🥗</Text>
            
            <Text style={styles.stepSubtitle}>Any food allergies?</Text>
            <ScrollView style={styles.optionsScrollShort}>
              {allergyOptions.map((option) => (
                <TouchableOpacity
                  key={option}
                  style={[
                    styles.checkboxOption,
                    formData.allergies.includes(option) && styles.checkboxOptionSelected,
                  ]}
                  onPress={() => toggleSelection('allergies', option)}
                >
                  <View style={styles.checkbox}>
                    {formData.allergies.includes(option) && (
                      <Text style={styles.checkmark}>✓</Text>
                    )}
                  </View>
                  <Text
                    style={[
                      styles.checkboxText,
                      formData.allergies.includes(option) && styles.checkboxTextSelected,
                    ]}
                  >
                    {option}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            <Text style={styles.stepSubtitle}>Dietary restrictions?</Text>
            <View style={styles.optionsGrid}>
              {dietTypeOptions.map((option) => (
                <TouchableOpacity
                  key={option}
                  style={[
                    styles.optionButton,
                    formData.dietType === option && styles.optionButtonSelected,
                  ]}
                  onPress={() => setFormData({ ...formData, dietType: option })}
                >
                  <Text
                    style={[
                      styles.optionText,
                      formData.dietType === option && styles.optionTextSelected,
                    ]}
                  >
                    {option}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        );

      default:
        return null;
    }
  };

  return (
    <LinearGradient colors={gradients.main} style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${(currentStep / totalSteps) * 100}%` },
              ]}
            />
          </View>
          <Text style={styles.progressText}>
            Step {currentStep} of {totalSteps}
          </Text>
        </View>

        {/* Step Content */}
        {renderStep()}

        {/* Navigation Buttons */}
        <View style={styles.buttonContainer}>
          {currentStep > 1 && (
            <TouchableOpacity style={styles.backButton} onPress={handleBack}>
              <Text style={styles.backButtonText}>Back</Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={[styles.nextButton, currentStep === 1 && styles.nextButtonFull]}
            onPress={handleNext}
          >
            <LinearGradient colors={gradients.button} style={styles.nextButtonGradient}>
              <Text style={styles.nextButtonText}>
                {currentStep === totalSteps ? 'Complete' : 'Next'}
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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingTop: 60,
  },
  progressContainer: {
    marginBottom: 30,
  },
  progressBar: {
    height: 8,
    backgroundColor: colors.grayLight,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 10,
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.primaryDark,
    borderRadius: 4,
  },
  progressText: {
    fontSize: 14,
    color: colors.textLight,
    textAlign: 'center',
  },
  stepContainer: {
    marginBottom: 30,
  },
  stepTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 10,
  },
  stepSubtitle: {
    fontSize: 16,
    color: colors.textLight,
    marginBottom: 20,
    marginTop: 15,
  },
  input: {
    backgroundColor: colors.white,
    borderRadius: 12,
    padding: 15,
    fontSize: 16,
    color: colors.text,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  optionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  optionButton: {
    backgroundColor: colors.white,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 25,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  optionButtonSelected: {
    backgroundColor: colors.primaryDark,
  },
  optionText: {
    fontSize: 14,
    color: colors.text,
    fontWeight: '600',
  },
  optionTextSelected: {
    color: colors.white,
  },
  optionsScroll: {
    maxHeight: 300,
  },
  optionsScrollShort: {
    maxHeight: 200,
  },
  checkboxOption: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    padding: 15,
    borderRadius: 12,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  checkboxOptionSelected: {
    backgroundColor: colors.primary,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: colors.primaryDark,
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkmark: {
    fontSize: 16,
    color: colors.primaryDark,
    fontWeight: 'bold',
  },
  checkboxText: {
    fontSize: 16,
    color: colors.text,
    flex: 1,
  },
  checkboxTextSelected: {
    fontWeight: '600',
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 20,
    marginBottom: 40,
  },
  backButton: {
    flex: 1,
    backgroundColor: colors.grayLight,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
  },
  nextButton: {
    flex: 1,
    borderRadius: 12,
    overflow: 'hidden',
  },
  nextButtonFull: {
    flex: 2,
  },
  nextButtonGradient: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  nextButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.white,
  },
});

export default QuestionnaireScreen;
