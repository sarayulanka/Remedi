import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  ActivityIndicator,
  Image,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';
import { healthAPI } from '../services/api';

const HealthScreen = () => {
  const [mode, setMode] = useState('image'); // 'image' or 'text'
  const [image, setImage] = useState(null);
  const [textDescription, setTextDescription] = useState('');
  const [userConcerns, setUserConcerns] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const pickImage = async () => {
    const { status} = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Required', 'Camera roll permission is needed');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.7,
      base64: true,
    });

    if (!result.canceled) {
      setImage(result.assets[0]);
      setAnalysis(null);
    }
  };

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Required', 'Camera permission is needed');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      quality: 0.7,
      base64: true,
    });

    if (!result.canceled) {
      setImage(result.assets[0]);
      setAnalysis(null);
    }
  };

  const analyzeHealth = async () => {
    if (mode === 'image' && !image) {
      Alert.alert('No Image', 'Please select or take a photo first');
      return;
    }

    if (mode === 'text' && !textDescription.trim()) {
      Alert.alert('Empty Description', 'Please describe your concern');
      return;
    }

    setLoading(true);
    try {
      const result = await healthAPI.analyzeHealthConcern(
        mode === 'image' ? image?.base64 : null,
        textDescription,
        userConcerns
      );
      setAnalysis(result);
    } catch (error) {
      Alert.alert('Analysis Failed', 'Please try again');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const saveRemedy = async () => {
    if (!analysis) return;

    try {
      await healthAPI.saveRemedy({
        condition: analysis.condition.name,
        conditionExplanation: analysis.condition.explanation,
        remedy: analysis.remedy,
        imageUrl: image?.uri,
      });
      Alert.alert('Saved! ✓', 'Remedy saved to your collection');
    } catch (error) {
      Alert.alert('Error', 'Failed to save remedy');
    }
  };

  const resetForm = () => {
    setImage(null);
    setTextDescription('');
    setUserConcerns('');
    setAnalysis(null);
  };

  return (
    <LinearGradient colors={gradients.main} style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Health Analysis</Text>
          <Text style={styles.headerSubtitle}>
            Get natural food remedies backed by science
          </Text>
        </View>

        {!analysis ? (
          <>
            {/* Mode Selector */}
            <View style={styles.modeSelector}>
              <TouchableOpacity
                style={[styles.modeButton, mode === 'image' && styles.modeButtonActive]}
                onPress={() => setMode('image')}
                activeOpacity={0.8}
              >
                {mode === 'image' && (
                  <LinearGradient
                    colors={gradients.button}
                    style={styles.modeButtonGradient}
                  />
                )}
                <Text style={[styles.modeButtonText, mode === 'image' && styles.modeButtonTextActive]}>
                  📸 Photo
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.modeButton, mode === 'text' && styles.modeButtonActive]}
                onPress={() => setMode('text')}
                activeOpacity={0.8}
              >
                {mode === 'text' && (
                  <LinearGradient
                    colors={gradients.button}
                    style={styles.modeButtonGradient}
                  />
                )}
                <Text style={[styles.modeButtonText, mode === 'text' && styles.modeButtonTextActive]}>
                  💬 Describe
                </Text>
              </TouchableOpacity>
            </View>

            {/* Input Section */}
            {mode === 'image' ? (
              <View style={styles.imageSection}>
                {image ? (
                  <View style={styles.imagePreviewContainer}>
                    <Image source={{ uri: image.uri }} style={styles.imagePreview} />
                    <TouchableOpacity
                      style={styles.removeImageButton}
                      onPress={() => setImage(null)}
                    >
                      <Text style={styles.removeImageText}>✕</Text>
                    </TouchableOpacity>
                  </View>
                ) : (
                  <View style={styles.imagePlaceholder}>
                    <Text style={styles.placeholderEmoji}>📷</Text>
                    <Text style={styles.placeholderText}>No image selected</Text>
                  </View>
                )}

                <View style={styles.imageButtons}>
                  <TouchableOpacity
                    style={styles.imageActionButton}
                    onPress={takePhoto}
                    activeOpacity={0.8}
                  >
                    <LinearGradient
                      colors={[colors.white, colors.offWhite]}
                      style={styles.imageActionGradient}
                    >
                      <Text style={styles.imageActionEmoji}>📸</Text>
                      <Text style={styles.imageActionText}>Take Photo</Text>
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.imageActionButton}
                    onPress={pickImage}
                    activeOpacity={0.8}
                  >
                    <LinearGradient
                      colors={[colors.white, colors.offWhite]}
                      style={styles.imageActionGradient}
                    >
                      <Text style={styles.imageActionEmoji}>🖼️</Text>
                      <Text style={styles.imageActionText}>Choose Photo</Text>
                    </LinearGradient>
                  </TouchableOpacity>
                </View>
              </View>
            ) : (
              <View style={styles.textSection}>
                <View style={styles.textInputCard}>
                  <LinearGradient
                    colors={[colors.white, colors.offWhite]}
                    style={styles.textInputGradient}
                  >
                    <Text style={styles.textInputLabel}>Describe your concern:</Text>
                    <TextInput
                      style={styles.textInput}
                      placeholder="e.g., I have a rash on my arm, or I'm feeling tired lately..."
                      value={textDescription}
                      onChangeText={setTextDescription}
                      multiline
                      numberOfLines={6}
                      textAlignVertical="top"
                      placeholderTextColor={colors.textMuted}
                    />
                  </LinearGradient>
                </View>
              </View>
            )}

            {/* Additional Concerns */}
            <View style={styles.concernsSection}>
              <View style={styles.concernsCard}>
                <LinearGradient
                  colors={[colors.white, colors.offWhite]}
                  style={styles.concernsGradient}
                >
                  <Text style={styles.concernsLabel}>Additional concerns (optional):</Text>
                  <TextInput
                    style={styles.concernsInput}
                    placeholder="Any other symptoms or questions?"
                    value={userConcerns}
                    onChangeText={setUserConcerns}
                    multiline
                    numberOfLines={3}
                    textAlignVertical="top"
                    placeholderTextColor={colors.textMuted}
                  />
                </LinearGradient>
              </View>
            </View>

            {/* Analyze Button */}
            <View style={styles.analyzeButtonContainer}>
              <TouchableOpacity
                style={styles.analyzeButton}
                onPress={analyzeHealth}
                disabled={loading}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={loading ? [colors.gray200, colors.gray300] : gradients.button}
                  style={styles.analyzeButtonGradient}
                >
                  {loading ? (
                    <ActivityIndicator color={colors.white} />
                  ) : (
                    <>
                      <Text style={styles.analyzeButtonEmoji}>🔍</Text>
                      <Text style={styles.analyzeButtonText}>Analyze</Text>
                    </>
                  )}
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </>
        ) : (
          /* Results Section */
          <View style={styles.resultsSection}>
            {/* Condition Explanation */}
            <View style={styles.resultCard}>
              <LinearGradient
                colors={[colors.white, colors.offWhite]}
                style={styles.resultGradient}
              >
                <View style={styles.resultHeader}>
                  <Text style={styles.resultHeaderEmoji}>💡</Text>
                  <Text style={styles.resultHeaderText}>What's Happening</Text>
                </View>
                <Text style={styles.conditionName}>{analysis.condition.name}</Text>
                <Text style={styles.conditionExplanation}>{analysis.condition.explanation}</Text>
              </LinearGradient>
            </View>

            {/* Remedies */}
            <View style={styles.resultCard}>
              <LinearGradient
                colors={[colors.white, colors.offWhite]}
                style={styles.resultGradient}
              >
                <View style={styles.resultHeader}>
                  <Text style={styles.resultHeaderEmoji}>🌿</Text>
                  <Text style={styles.resultHeaderText}>Natural Food Remedies</Text>
                </View>
                <Text style={styles.remedyExplanation}>{analysis.remedy.explanation}</Text>

                <Text style={styles.sectionSubtitle}>Key Nutrients:</Text>
                <View style={styles.nutrientsList}>
                  {analysis.remedy.recommendedNutrients.map((nutrient, index) => (
                    <View key={index} style={styles.nutrientTag}>
                      <Text style={styles.nutrientText}>{nutrient}</Text>
                    </View>
                  ))}
                </View>

                <Text style={styles.sectionSubtitle}>Recommended Foods:</Text>
                {analysis.remedy.specificFoods.slice(0, 5).map((food, index) => (
                  <View key={index} style={styles.foodItem}>
                    <View style={styles.foodBullet} />
                    <View style={styles.foodContent}>
                      <Text style={styles.foodName}>{food.name}</Text>
                      {food.keyNutrients && food.keyNutrients.length > 0 && (
                        <Text style={styles.foodNutrients}>
                          Rich in: {food.keyNutrients.map((n) => n.name).join(', ')}
                        </Text>
                      )}
                    </View>
                  </View>
                ))}
              </LinearGradient>
            </View>

            {/* Disclaimer */}
            <View style={styles.disclaimer}>
              <Text style={styles.disclaimerText}>
                ⚠️ {analysis.disclaimer}
              </Text>
            </View>

            {/* Action Buttons */}
            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={styles.saveButton}
                onPress={saveRemedy}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={gradients.success}
                  style={styles.saveButtonGradient}
                >
                  <Text style={styles.saveButtonText}>⭐ Save Remedy</Text>
                </LinearGradient>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.newAnalysisButton}
                onPress={resetForm}
                activeOpacity={0.8}
              >
                <Text style={styles.newAnalysisButtonText}>New Analysis</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        <View style={styles.bottomSpacer} />
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
    lineHeight: typography.base * 1.5,
  },
  modeSelector: {
    flexDirection: 'row',
    paddingHorizontal: spacing['2xl'],
    marginBottom: spacing.xl,
    gap: spacing.sm,
  },
  modeButton: {
    flex: 1,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.sm,
    backgroundColor: colors.white,
  },
  modeButtonActive: {
    ...shadows.md,
  },
  modeButtonGradient: {
    ...StyleSheet.absoluteFillObject,
  },
  modeButtonText: {
    paddingVertical: spacing.base,
    textAlign: 'center',
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.text,
  },
  modeButtonTextActive: {
    color: colors.white,
    fontWeight: '700',
  },
  imageSection: {
    paddingHorizontal: spacing['2xl'],
    marginBottom: spacing.base,
  },
  imagePreviewContainer: {
    position: 'relative',
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    marginBottom: spacing.base,
    ...shadows.lg,
  },
  imagePreview: {
    width: '100%',
    height: 300,
    borderRadius: borderRadius.xl,
  },
  removeImageButton: {
    position: 'absolute',
    top: spacing.base,
    right: spacing.base,
    width: 36,
    height: 36,
    borderRadius: borderRadius.full,
    backgroundColor: colors.white,
    justifyContent: 'center',
    alignItems: 'center',
    ...shadows.md,
  },
  removeImageText: {
    fontSize: typography.lg,
    color: colors.text,
    fontWeight: 'bold',
  },
  imagePlaceholder: {
    height: 300,
    borderRadius: borderRadius.xl,
    backgroundColor: colors.gray50,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.base,
    borderWidth: 2,
    borderColor: colors.gray200,
    borderStyle: 'dashed',
  },
  placeholderEmoji: {
    fontSize: 64,
    marginBottom: spacing.base,
  },
  placeholderText: {
    fontSize: typography.base,
    color: colors.textMuted,
    fontWeight: '600',
  },
  imageButtons: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  imageActionButton: {
    flex: 1,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.md,
  },
  imageActionGradient: {
    paddingVertical: spacing.base,
    alignItems: 'center',
    gap: spacing.xs,
  },
  imageActionEmoji: {
    fontSize: 24,
  },
  imageActionText: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.text,
  },
  textSection: {
    paddingHorizontal: spacing['2xl'],
    marginBottom: spacing.base,
  },
  textInputCard: {
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.lg,
  },
  textInputGradient: {
    padding: spacing.lg,
  },
  textInputLabel: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  textInput: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.md,
    padding: spacing.base,
    fontSize: typography.base,
    color: colors.text,
    minHeight: 150,
    borderWidth: 2,
    borderColor: colors.gray100,
  },
  concernsSection: {
    paddingHorizontal: spacing['2xl'],
    marginBottom: spacing.base,
  },
  concernsCard: {
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.md,
  },
  concernsGradient: {
    padding: spacing.base,
  },
  concernsLabel: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  concernsInput: {
    backgroundColor: colors.white,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    fontSize: typography.sm,
    color: colors.text,
    minHeight: 80,
    borderWidth: 2,
    borderColor: colors.gray100,
  },
  analyzeButtonContainer: {
    paddingHorizontal: spacing['2xl'],
    marginBottom: spacing.xl,
  },
  analyzeButton: {
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.lg,
  },
  analyzeButtonGradient: {
    paddingVertical: spacing.lg,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.sm,
  },
  analyzeButtonEmoji: {
    fontSize: 20,
  },
  analyzeButtonText: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.white,
    letterSpacing: 0.3,
  },
  resultsSection: {
    paddingHorizontal: spacing['2xl'],
  },
  resultCard: {
    marginBottom: spacing.base,
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.lg,
  },
  resultGradient: {
    padding: spacing.lg,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.base,
    gap: spacing.sm,
  },
  resultHeaderEmoji: {
    fontSize: 24,
  },
  resultHeaderText: {
    fontSize: typography.xl,
    fontWeight: '700',
    color: colors.text,
  },
  conditionName: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.primaryDark,
    marginBottom: spacing.sm,
  },
  conditionExplanation: {
    fontSize: typography.base,
    color: colors.textLight,
    lineHeight: typography.base * 1.6,
  },
  remedyExplanation: {
    fontSize: typography.base,
    color: colors.textLight,
    lineHeight: typography.base * 1.6,
    marginBottom: spacing.base,
  },
  sectionSubtitle: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.text,
    marginTop: spacing.base,
    marginBottom: spacing.sm,
  },
  nutrientsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
    marginBottom: spacing.base,
  },
  nutrientTag: {
    backgroundColor: colors.primaryLight,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
  },
  nutrientText: {
    fontSize: typography.sm,
    color: colors.text,
    fontWeight: '600',
  },
  foodItem: {
    flexDirection: 'row',
    marginBottom: spacing.sm,
    alignItems: 'flex-start',
  },
  foodBullet: {
    width: 6,
    height: 6,
    borderRadius: borderRadius.full,
    backgroundColor: colors.primaryDark,
    marginTop: 8,
    marginRight: spacing.sm,
  },
  foodContent: {
    flex: 1,
  },
  foodName: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  foodNutrients: {
    fontSize: typography.sm,
    color: colors.textLight,
  },
  disclaimer: {
    backgroundColor: colors.warningLight,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
    marginBottom: spacing.base,
  },
  disclaimerText: {
    fontSize: typography.sm,
    color: colors.text,
    lineHeight: typography.sm * 1.5,
  },
  actionButtons: {
    gap: spacing.sm,
    marginBottom: spacing.xl,
  },
  saveButton: {
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.md,
  },
  saveButtonGradient: {
    paddingVertical: spacing.base,
    alignItems: 'center',
  },
  saveButtonText: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.white,
  },
  newAnalysisButton: {
    backgroundColor: colors.white,
    paddingVertical: spacing.base,
    borderRadius: borderRadius.lg,
    alignItems: 'center',
    ...shadows.sm,
  },
  newAnalysisButtonText: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.text,
  },
  bottomSpacer: {
    height: spacing['2xl'],
  },
});

export default HealthScreen;
