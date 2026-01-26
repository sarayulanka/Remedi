import React, { useState, useEffect, useCallback } from 'react';
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
  Linking,
  Modal,
  TouchableWithoutFeedback,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';
import { healthAPI, imageAPI, authAPI } from '../services/api';

const { width: screenWidth } = Dimensions.get('window');

// In-memory cache for food images during the session
const foodImageCache = {};

// Async function to fetch food image from API - NO hardcoded fallbacks
// Each food gets its own unique, dynamically searched image
const fetchFoodImage = async (foodName) => {
  if (!foodName) return null;

  const cacheKey = foodName.toLowerCase().trim();

  // Check cache first
  if (foodImageCache[cacheKey]) {
    return foodImageCache[cacheKey];
  }

  try {
    const response = await imageAPI.getFoodImage(foodName, 'medium');
    if (response.imageUrl) {
      foodImageCache[cacheKey] = response.imageUrl;
      return response.imageUrl;
    }
    return null;
  } catch (error) {
    console.log('Error fetching food image:', error);
    return null;
  }
};

// Clean recipe step text by removing redundant prefixes like "Step 1:", "1.", etc.
const cleanStepText = (step) => {
  if (!step || typeof step !== 'string') return step;

  // Remove common step prefixes: "Step 1:", "STEP 1.", "1.", "1)", "1 -", etc.
  let cleaned = step.replace(/^(?:step\s*)?\d+[\s]*[:.)\-]\s*/i, '');

  // Remove bullet points and dashes at start
  cleaned = cleaned.replace(/^[\-•*]\s*/, '');

  // Trim whitespace
  cleaned = cleaned.trim();

  // Capitalize first letter
  if (cleaned.length > 0) {
    cleaned = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
  }

  return cleaned;
};

// FoodImage component that handles async image loading
// Uses searchTerm for API lookup - each food gets its own unique image
const FoodImage = ({ foodName, searchTerm, style, resizeMode = 'cover' }) => {
  // Use searchTerm for image lookup if provided, otherwise use foodName
  const lookupName = searchTerm || foodName;
  const [imageUrl, setImageUrl] = useState(foodImageCache[lookupName?.toLowerCase().trim()] || null);
  const [loading, setLoading] = useState(!foodImageCache[lookupName?.toLowerCase().trim()]);

  useEffect(() => {
    let mounted = true;

    const loadImage = async () => {
      if (!lookupName) return;

      const cacheKey = lookupName.toLowerCase().trim();
      if (foodImageCache[cacheKey]) {
        setImageUrl(foodImageCache[cacheKey]);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const url = await fetchFoodImage(lookupName);
        if (mounted && url) {
          setImageUrl(url);
        }
      } catch (error) {
        console.log('Error loading image:', error);
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadImage();

    return () => {
      mounted = false;
    };
  }, [lookupName]);

  // Show loading placeholder while fetching
  if (loading || !imageUrl) {
    return (
      <View style={[style, { backgroundColor: colors.offWhite, justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="small" color={colors.primary} />
      </View>
    );
  }

  return (
    <Image
      source={{ uri: imageUrl }}
      style={style}
      resizeMode={resizeMode}
    />
  );
};

// Helper function to get cached food image
const getFoodImage = (foodName) => {
  if (!foodName) return null;
  const cacheKey = foodName.toLowerCase().trim();
  return foodImageCache[cacheKey] || null;
};

// Helper function to extract the core food word for deduplication
const getCoreFood = (foodName) => {
  if (!foodName) return '';

  let simplified = foodName.toLowerCase().trim();

  // Remove common suffixes that create duplicates
  const suffixesToRemove = [
    'isolate', 'concentrate', 'powder', 'extract', 'supplement',
    'protein', 'flour', 'meal', 'flakes', 'chips', 'pieces',
    'raw', 'cooked', 'fresh', 'frozen', 'canned', 'dried',
    'whole', 'ground', 'sliced', 'diced', 'chopped', 'shredded',
    'organic', 'natural', 'pure', 'fortified', 'enriched',
  ];

  // Remove common prefixes
  const prefixesToRemove = [
    'whole', 'skim', 'low-fat', 'lowfat', 'fat-free', 'fatfree',
    'organic', 'fresh', 'frozen', 'canned', 'dried', 'raw', 'cooked',
    'wild', 'farm-raised', 'grass-fed', 'free-range', 'pasture-raised',
    'dark', 'light', 'white', 'brown', 'black', 'red', 'green', 'yellow',
    'roasted', 'grilled', 'baked', 'fried', 'steamed', 'boiled',
    'greek', 'regular', 'traditional', 'classic', 'homemade',
    'atlantic', 'pacific', 'alaskan', 'norwegian',
  ];

  // Remove prefixes
  for (const prefix of prefixesToRemove) {
    simplified = simplified.replace(new RegExp(`^${prefix}\\s+`, 'i'), '');
  }

  // Remove suffixes
  for (const suffix of suffixesToRemove) {
    simplified = simplified.replace(new RegExp(`\\s+${suffix}$`, 'i'), '');
    simplified = simplified.replace(new RegExp(`\\s+${suffix}\\s+`, 'gi'), ' ');
  }

  // Clean up extra spaces and get first 2 words (the core food)
  simplified = simplified.replace(/\s+/g, ' ').trim();
  const words = simplified.split(' ');

  // Return just the first 1-2 significant words
  return words.slice(0, 2).join(' ');
};

// Helper function to deduplicate foods - catches similar items
const deduplicateFoods = (foods) => {
  if (!foods || !Array.isArray(foods)) return [];

  const seen = new Map(); // Map core food -> full food object
  const uniqueFoods = [];

  for (const food of foods) {
    // Use displayName for deduplication (cleaner names from AI)
    const nameToCheck = food.displayName || food.name || '';
    const coreFood = getCoreFood(nameToCheck);

    if (!coreFood) continue;

    // Check if we've seen this core food or something very similar
    let isDuplicate = false;
    for (const [seenCore] of seen) {
      // Check if one contains the other (catches "soy protein" vs "soy protein isolate")
      if (seenCore.includes(coreFood) || coreFood.includes(seenCore)) {
        isDuplicate = true;
        break;
      }
      // Check if they share the same first word (main ingredient)
      const seenFirstWord = seenCore.split(' ')[0];
      const currentFirstWord = coreFood.split(' ')[0];
      if (seenFirstWord === currentFirstWord && seenFirstWord.length > 3) {
        isDuplicate = true;
        break;
      }
    }

    if (!isDuplicate) {
      seen.set(coreFood, food);
      uniqueFoods.push(food);
    }
  }

  return uniqueFoods;
};

// Diet type restrictions mapping - what keywords to exclude for each diet
const DIET_RESTRICTIONS = {
  vegetarian: ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'meat', 'bacon', 'ham', 'sausage', 'fish', 'seafood', 'salmon', 'tuna', 'shrimp', 'crab'],
  vegan: ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'meat', 'bacon', 'ham', 'sausage', 'fish', 'seafood', 'salmon', 'tuna', 'milk', 'cheese', 'yogurt', 'butter', 'cream', 'egg', 'honey', 'dairy'],
  pescatarian: ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'meat', 'bacon', 'ham', 'sausage'],
  keto: ['bread', 'pasta', 'rice', 'potato', 'sugar', 'corn', 'cereal', 'oat', 'wheat'],
  paleo: ['bread', 'pasta', 'rice', 'cereal', 'oat', 'wheat', 'dairy', 'milk', 'cheese', 'legume', 'bean', 'peanut', 'soy'],
  halal: ['pork', 'bacon', 'ham', 'lard'],
  kosher: ['pork', 'bacon', 'ham', 'shellfish', 'shrimp', 'crab', 'lobster'],
};

// Common allergen keywords
const ALLERGEN_KEYWORDS = {
  peanuts: ['peanut', 'groundnut'],
  'tree nuts': ['almond', 'walnut', 'cashew', 'pecan', 'pistachio', 'hazelnut', 'macadamia'],
  dairy: ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'lactose', 'whey'],
  eggs: ['egg', 'albumin', 'mayonnaise'],
  soy: ['soy', 'soya', 'tofu', 'tempeh', 'edamame'],
  gluten: ['wheat', 'barley', 'rye', 'bread', 'pasta', 'flour'],
  fish: ['fish', 'salmon', 'tuna', 'cod', 'tilapia', 'halibut', 'anchovy', 'sardine'],
  shellfish: ['shrimp', 'crab', 'lobster', 'clam', 'mussel', 'oyster', 'scallop'],
};

// Helper function to check if a recipe is compatible with user's dietary preferences
const isRecipeCompatible = (recipe, dietType, allergies) => {
  if (!recipe) return false;

  // Build text to search from recipe title and ingredients
  let recipeText = (recipe.title || '').toLowerCase();
  if (recipe.keyIngredient) {
    recipeText += ' ' + recipe.keyIngredient.toLowerCase();
  }
  if (recipe.ingredients && Array.isArray(recipe.ingredients)) {
    recipeText += ' ' + recipe.ingredients.map(i => String(i).toLowerCase()).join(' ');
  }
  if (recipe.description) {
    recipeText += ' ' + recipe.description.toLowerCase();
  }

  // Check explicit restrictedDiets property (from TheMealDB API)
  if (dietType && recipe.restrictedDiets) {
    const normalizedDiet = dietType.toLowerCase().trim();
    if (recipe.restrictedDiets.some(d => normalizedDiet.includes(d.toLowerCase()))) {
      return false;
    }
  }

  // Check diet type against recipe text (for external API recipes)
  if (dietType) {
    const normalizedDiet = dietType.toLowerCase().trim();
    const restrictions = DIET_RESTRICTIONS[normalizedDiet] || [];
    for (const keyword of restrictions) {
      if (recipeText.includes(keyword)) {
        return false;
      }
    }
  }

  // Check explicit containsAllergens property (from TheMealDB API)
  if (allergies && allergies.length > 0 && recipe.containsAllergens) {
    const normalizedAllergies = allergies.map(a => a.toLowerCase().trim());
    for (const allergen of recipe.containsAllergens) {
      const normalizedAllergen = allergen.toLowerCase();
      if (normalizedAllergies.some(a =>
        a.includes(normalizedAllergen) || normalizedAllergen.includes(a)
      )) {
        return false;
      }
    }
  }

  // Check allergens against recipe text (for external API recipes)
  if (allergies && allergies.length > 0) {
    const normalizedAllergies = allergies.map(a => a.toLowerCase().trim());
    for (const allergy of normalizedAllergies) {
      // Check direct match
      if (recipeText.includes(allergy)) {
        return false;
      }
      // Check mapped keywords
      const allergenKeywords = ALLERGEN_KEYWORDS[allergy] || [];
      for (const keyword of allergenKeywords) {
        if (recipeText.includes(keyword)) {
          return false;
        }
      }
    }
  }

  return true;
};

const HealthScreen = () => {
  const [mode, setMode] = useState('image');
  const [image, setImage] = useState(null);
  const [textDescription, setTextDescription] = useState('');
  const [userConcerns, setUserConcerns] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  // User dietary preferences
  const [userAllergies, setUserAllergies] = useState([]);
  const [userDietType, setUserDietType] = useState('');

  // Modal states
  const [selectedNutrient, setSelectedNutrient] = useState(null);
  const [nutrientModalVisible, setNutrientModalVisible] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [recipeModalVisible, setRecipeModalVisible] = useState(false);
  const [selectedFood, setSelectedFood] = useState(null);
  const [foodInfoModalVisible, setFoodInfoModalVisible] = useState(false);

  // Fetch user preferences on mount
  useEffect(() => {
    const fetchUserPreferences = async () => {
      try {
        const profile = await authAPI.getProfile();
        const prefs = profile.dietaryPreferences || {};
        setUserAllergies(prefs.allergies || profile.allergies || []);
        setUserDietType(prefs.dietType || profile.dietType || '');
      } catch (error) {
        console.log('Could not fetch user preferences:', error);
      }
    };
    fetchUserPreferences();
  }, []);

  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
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
        userConcerns,
        userAllergies,
        userDietType
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
      Alert.alert('Saved!', 'Remedy saved to your collection');
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

  const openLink = (url) => {
    Linking.openURL(url).catch((err) => console.error('Error opening link:', err));
  };

  const handleNutrientPress = (nutrient) => {
    const explanation = analysis?.remedy?.nutrientExplanations?.[nutrient] ||
      `${nutrient} is an important nutrient that supports your body's healing process for this condition.`;
    setSelectedNutrient({ name: nutrient, explanation });
    setNutrientModalVisible(true);
  };

  const handleRecipePress = (recipe) => {
    setSelectedRecipe(recipe);
    setRecipeModalVisible(true);
  };

  const handleFoodInfoPress = (food) => {
    setSelectedFood(food);
    setFoodInfoModalVisible(true);
  };

  const renderFoodInfoModal = () => (
    <Modal
      visible={foodInfoModalVisible}
      transparent={true}
      animationType="fade"
      onRequestClose={() => setFoodInfoModalVisible(false)}
    >
      <TouchableWithoutFeedback onPress={() => setFoodInfoModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <TouchableWithoutFeedback onPress={(e) => e.stopPropagation()}>
            <View style={styles.foodInfoModalContent}>
              <LinearGradient
                colors={[colors.white, colors.offWhite]}
                style={styles.foodInfoModalGradient}
              >
                {/* Header with food image */}
                <View style={styles.foodInfoHeader}>
                  <FoodImage
                    foodName={selectedFood?.displayName || selectedFood?.name}
                    searchTerm={selectedFood?.imageSearchTerm}
                    style={styles.foodInfoImage}
                    resizeMode="cover"
                  />
                  <TouchableOpacity
                    onPress={() => setFoodInfoModalVisible(false)}
                    style={styles.foodInfoCloseButton}
                  >
                    <Ionicons name="close" size={20} color={colors.white} />
                  </TouchableOpacity>
                </View>

                {/* Food name - show full name, not truncated */}
                <Text style={styles.foodInfoTitle}>
                  {selectedFood?.displayName || selectedFood?.name}
                </Text>

                {/* Show original FDA name if different from display name */}
                {selectedFood?.name && selectedFood?.displayName &&
                 selectedFood.name !== selectedFood.displayName && (
                  <Text style={styles.foodInfoSubtitle}>
                    {selectedFood.name}
                  </Text>
                )}

                {/* Tip from AI */}
                {selectedFood?.tip && (
                  <View style={styles.foodInfoTipContainer}>
                    <Ionicons name="bulb-outline" size={16} color={colors.primaryDark} />
                    <Text style={styles.foodInfoTip}>{selectedFood.tip}</Text>
                  </View>
                )}

                {/* Key nutrients */}
                {selectedFood?.keyNutrients && selectedFood.keyNutrients.length > 0 && (
                  <View style={styles.foodInfoNutrientsSection}>
                    <Text style={styles.foodInfoSectionTitle}>Key Nutrients</Text>
                    <View style={styles.foodInfoNutrientsList}>
                      {selectedFood.keyNutrients.map((nutrient, idx) => (
                        <View key={idx} style={styles.foodInfoNutrientItem}>
                          <Text style={styles.foodInfoNutrientName}>{nutrient.name}</Text>
                          <Text style={styles.foodInfoNutrientValue}>
                            {Math.round(nutrient.amount * 10) / 10} {nutrient.unit}
                          </Text>
                        </View>
                      ))}
                    </View>
                  </View>
                )}

                {/* FDA source badge */}
                <View style={styles.foodInfoSourceBadge}>
                  <Ionicons name="shield-checkmark-outline" size={12} color={colors.textMuted} />
                  <Text style={styles.foodInfoSourceText}>FDA FoodData Central</Text>
                </View>
              </LinearGradient>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );

  const renderNutrientModal = () => (
    <Modal
      visible={nutrientModalVisible}
      transparent={true}
      animationType="fade"
      onRequestClose={() => setNutrientModalVisible(false)}
    >
      <TouchableWithoutFeedback onPress={() => setNutrientModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <TouchableWithoutFeedback onPress={(e) => e.stopPropagation()}>
            <View style={styles.nutrientModalContent}>
              <LinearGradient
                colors={[colors.white, colors.offWhite]}
                style={styles.nutrientModalGradient}
              >
                <View style={styles.modalHeader}>
                  <Text style={styles.nutrientModalTitle}>{selectedNutrient?.name}</Text>
                  <TouchableOpacity
                    onPress={() => setNutrientModalVisible(false)}
                    style={styles.closeButton}
                  >
                    <Ionicons name="close" size={24} color={colors.text} />
                  </TouchableOpacity>
                </View>
                <View style={styles.nutrientModalDivider} />
                <Text style={styles.nutrientModalSubtitle}>
                  How this nutrient helps your condition:
                </Text>
                <ScrollView style={styles.nutrientModalScroll} showsVerticalScrollIndicator={false}>
                  <Text style={styles.nutrientModalExplanation}>
                    {selectedNutrient?.explanation}
                  </Text>
                </ScrollView>
                <View style={styles.modalSourceBadge}>
                  <Text style={styles.modalSourceText}>Source: FDA / NIH Research</Text>
                </View>
              </LinearGradient>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );

  const renderRecipeModal = () => (
    <Modal
      visible={recipeModalVisible}
      transparent={false}
      animationType="slide"
      onRequestClose={() => setRecipeModalVisible(false)}
    >
      <View style={styles.recipeModalContainer}>
        <LinearGradient
          colors={[colors.white, colors.offWhite]}
          style={styles.recipeModalGradient}
        >
          {/* Header with close button */}
          <View style={styles.recipeModalHeader}>
            <TouchableOpacity
              onPress={() => setRecipeModalVisible(false)}
              style={styles.recipeCloseButton}
            >
              <Ionicons name="close" size={24} color={colors.text} />
            </TouchableOpacity>
            <Text style={styles.recipeModalHeaderTitle}>Recipe Details</Text>
            <View style={{ width: 36 }} />
          </View>

          <ScrollView
            style={styles.recipeModalScroll}
            contentContainerStyle={styles.recipeModalScrollContent}
            showsVerticalScrollIndicator={true}
            bounces={true}
          >
            {/* Recipe Image - Always show with relevant image */}
            {selectedRecipe && (() => {
              const imageInfo = getRecipeImage(selectedRecipe);
              if (imageInfo.type === 'static') {
                return (
                  <Image
                    source={{ uri: imageInfo.url }}
                    style={styles.recipeModalImage}
                    resizeMode="cover"
                  />
                );
              } else {
                return (
                  <FoodImage
                    foodName={imageInfo.foodName}
                    style={styles.recipeModalImage}
                    resizeMode="cover"
                  />
                );
              }
            })()}

            {/* Recipe Title */}
            <Text style={styles.recipeModalTitle}>{selectedRecipe?.title}</Text>

            {/* Meta Info */}
            <View style={styles.recipeModalMetaRow}>
              {selectedRecipe?.readyInMinutes && (
                <View style={styles.recipeModalMeta}>
                  <Ionicons name="time-outline" size={16} color={colors.primaryDark} />
                  <Text style={styles.recipeModalMetaValue}>{selectedRecipe.readyInMinutes} min</Text>
                </View>
              )}
              {selectedRecipe?.servings && (
                <View style={styles.recipeModalMeta}>
                  <Ionicons name="people-outline" size={16} color={colors.primaryDark} />
                  <Text style={styles.recipeModalMetaValue}>{selectedRecipe.servings} servings</Text>
                </View>
              )}
              {selectedRecipe?.keyIngredient && (
                <View style={styles.recipeModalMeta}>
                  <Ionicons name="leaf-outline" size={16} color={colors.primaryDark} />
                  <Text style={styles.recipeModalMetaValue}>{selectedRecipe.keyIngredient}</Text>
                </View>
              )}
            </View>

            {/* Description/Summary */}
            {(selectedRecipe?.description || selectedRecipe?.summary) && (
              <View style={styles.recipeModalSection}>
                <Text style={styles.recipeModalSectionTitle}>About This Recipe</Text>
                <Text style={styles.recipeModalDescription}>
                  {selectedRecipe.description || selectedRecipe.summary}
                </Text>
              </View>
            )}

            {/* Ingredients Section */}
            {selectedRecipe?.ingredients && selectedRecipe.ingredients.length > 0 && (
              <View style={styles.recipeModalSection}>
                <View style={styles.recipeModalSectionHeader}>
                  <Ionicons name="basket-outline" size={20} color={colors.primaryDark} />
                  <Text style={styles.recipeModalSectionTitle}>Ingredients</Text>
                </View>
                <View style={styles.ingredientsList}>
                  {selectedRecipe.ingredients.map((ing, idx) => (
                    <View key={idx} style={styles.ingredientItem}>
                      <View style={styles.ingredientBullet} />
                      <Text style={styles.ingredientText}>
                        <Text style={styles.ingredientAmount}>
                          {ing.amount}{ing.unit ? ` ${ing.unit}` : ''}{' '}
                        </Text>
                        <Text style={styles.ingredientName}>{ing.name}</Text>
                      </Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* Directions - Main section */}
            <View style={styles.recipeModalDirectionsSection}>
              <View style={styles.recipeModalDirectionsHeader}>
                <Ionicons name="restaurant-outline" size={20} color={colors.primaryDark} />
                <Text style={styles.recipeModalDirectionsTitle}>Directions</Text>
              </View>
              <View style={styles.recipeModalDirectionsContent}>
                {/* Instructions as array (from TheMealDB) */}
                {selectedRecipe?.instructions && Array.isArray(selectedRecipe.instructions) ? (
                  selectedRecipe.instructions.map((step, idx) => (
                    <View key={idx} style={styles.recipeStepItem}>
                      <View style={styles.recipeStepNumber}>
                        <Text style={styles.recipeStepNumberText}>{idx + 1}</Text>
                      </View>
                      <Text style={styles.recipeStepText}>{cleanStepText(step)}</Text>
                    </View>
                  ))
                ) : selectedRecipe?.instructions && typeof selectedRecipe.instructions === 'string' ? (
                  /* Instructions as string */
                  <Text style={styles.recipeModalInstructions}>{cleanStepText(selectedRecipe.instructions)}</Text>
                ) : selectedRecipe?.analyzedInstructions && selectedRecipe.analyzedInstructions.length > 0 ? (
                  /* Spoonacular format (legacy support) */
                  selectedRecipe.analyzedInstructions[0]?.steps?.map((step, idx) => (
                    <View key={idx} style={styles.recipeStepItem}>
                      <View style={styles.recipeStepNumber}>
                        <Text style={styles.recipeStepNumberText}>{idx + 1}</Text>
                      </View>
                      <Text style={styles.recipeStepText}>{cleanStepText(step.step)}</Text>
                    </View>
                  ))
                ) : (
                  <Text style={styles.recipeModalInstructions}>
                    See source for full instructions.
                  </Text>
                )}
              </View>
            </View>

            {/* Nutrition Highlights */}
            {selectedRecipe?.nutrients && selectedRecipe.nutrients.length > 0 && (
              <View style={styles.recipeModalSection}>
                <Text style={styles.recipeModalSectionTitle}>Nutrition Highlights</Text>
                <View style={styles.recipeNutrientsList}>
                  {selectedRecipe.nutrients.map((n, idx) => (
                    <View key={idx} style={styles.recipeNutrientItem}>
                      <Text style={styles.recipeNutrientName}>{n.name}</Text>
                      <Text style={styles.recipeNutrientAmount}>
                        {Math.round(n.amount)} {n.unit}
                      </Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* Source */}
            <View style={styles.recipeModalSourceContainer}>
              <Text style={styles.recipeModalSource}>
                Source: {selectedRecipe?.source || selectedRecipe?.sourceName || 'Remedi Kitchen'}
              </Text>
            </View>

            {/* View Full Recipe Button */}
            {(selectedRecipe?.sourceUrl || selectedRecipe?.spoonacularSourceUrl) && (
              <TouchableOpacity
                style={styles.viewFullRecipeButton}
                onPress={() => openLink(selectedRecipe.sourceUrl || selectedRecipe.spoonacularSourceUrl)}
              >
                <LinearGradient
                  colors={gradients.button}
                  style={styles.viewFullRecipeGradient}
                >
                  <Ionicons name="open-outline" size={18} color={colors.white} />
                  <Text style={styles.viewFullRecipeText}>View Full Recipe Online</Text>
                </LinearGradient>
              </TouchableOpacity>
            )}

            <View style={{ height: 40 }} />
          </ScrollView>
        </LinearGradient>
      </View>
    </Modal>
  );

  // Get recipe image - try multiple sources
  const getRecipeImage = (recipe) => {
    if (recipe.image) return { type: 'static', url: recipe.image };
    if (recipe.imageUrl) return { type: 'static', url: recipe.imageUrl };
    // Use dynamic fetch from API - every recipe gets a unique image
    const searchName = recipe.keyIngredient || recipe.title || 'healthy meal';
    return { type: 'dynamic', foodName: searchName };
  };

  const renderRecipeCard = (recipe, index) => {
    const imageInfo = getRecipeImage(recipe);

    return (
      <TouchableOpacity
        key={index}
        style={styles.recipeCard}
        onPress={() => handleRecipePress(recipe)}
        activeOpacity={0.9}
      >
        <LinearGradient
          colors={[colors.white, colors.offWhite]}
          style={styles.recipeGradient}
        >
          {imageInfo.type === 'static' ? (
            <Image
              source={{ uri: imageInfo.url }}
              style={styles.recipeImage}
              resizeMode="cover"
            />
          ) : (
            <FoodImage
              foodName={imageInfo.foodName}
              style={styles.recipeImage}
              resizeMode="cover"
            />
          )}
          <View style={styles.recipeContent}>
            <Text style={styles.recipeTitle} numberOfLines={2}>{recipe.title}</Text>
            <View style={styles.recipeMetaRow}>
              {recipe.readyInMinutes && (
                <View style={styles.recipeMeta}>
                  <Ionicons name="time-outline" size={14} color={colors.textMuted} />
                  <Text style={styles.recipeMetaText}>{recipe.readyInMinutes} min</Text>
                </View>
              )}
              {recipe.servings && (
                <View style={styles.recipeMeta}>
                  <Ionicons name="people-outline" size={14} color={colors.textMuted} />
                  <Text style={styles.recipeMetaText}>{recipe.servings}</Text>
                </View>
              )}
            </View>
            {(recipe.description || recipe.summary) && (
              <Text style={styles.recipeDescription} numberOfLines={2}>
                {recipe.description || recipe.summary?.replace(/<[^>]*>/g, '').substring(0, 100)}
              </Text>
            )}
            {recipe.keyIngredient && (
              <View style={styles.keyIngredientBadge}>
                <Ionicons name="leaf-outline" size={12} color={colors.primaryDark} />
                <Text style={styles.keyIngredientText}>{recipe.keyIngredient}</Text>
              </View>
            )}
            <View style={styles.recipeButton}>
              <Text style={styles.recipeButtonText}>View Recipe</Text>
              <Ionicons name="arrow-forward" size={14} color={colors.white} />
            </View>
          </View>
        </LinearGradient>
      </TouchableOpacity>
    );
  };

  return (
    <LinearGradient colors={gradients.main} style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollViewContent}
        showsVerticalScrollIndicator={false}
        bounces={true}
        alwaysBounceVertical={true}
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
                  Photo
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
                  Describe
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
                      <Ionicons name="close" size={18} color={colors.white} />
                    </TouchableOpacity>
                  </View>
                ) : (
                  <View style={styles.imagePlaceholder}>
                    <Ionicons name="camera-outline" size={48} color={colors.textMuted} />
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
                      <Ionicons name="camera" size={20} color={colors.primaryDark} />
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
                      <Ionicons name="images" size={20} color={colors.primaryDark} />
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
                    <Text style={styles.analyzeButtonText}>Analyze</Text>
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
                  <View style={styles.resultHeaderIcon}>
                    <Ionicons name="bulb-outline" size={20} color={colors.primaryDark} />
                  </View>
                  <Text style={styles.resultHeaderText}>What's Happening</Text>
                </View>
                <Text style={styles.conditionName}>{analysis.condition.name}</Text>
                <Text style={styles.conditionExplanation}>{analysis.condition.explanation}</Text>
              </LinearGradient>
            </View>

            {/* Key Nutrients */}
            <View style={styles.resultCard}>
              <LinearGradient
                colors={[colors.white, colors.offWhite]}
                style={styles.resultGradient}
              >
                <View style={styles.resultHeader}>
                  <View style={styles.resultHeaderIcon}>
                    <Ionicons name="nutrition-outline" size={20} color={colors.primaryDark} />
                  </View>
                  <Text style={styles.resultHeaderText}>Key Nutrients for You</Text>
                </View>
                <Text style={styles.nutrientHint}>Tap a nutrient to learn how it helps</Text>
                <View style={styles.nutrientsList}>
                  {analysis.remedy.recommendedNutrients.map((nutrient, index) => (
                    <TouchableOpacity
                      key={index}
                      style={styles.nutrientTag}
                      onPress={() => handleNutrientPress(nutrient)}
                      activeOpacity={0.7}
                    >
                      <Text style={styles.nutrientText}>{nutrient}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </LinearGradient>
            </View>

            {/* Recommended Foods - Simple cards with info icons */}
            <View style={styles.foodsSection}>
              <View style={styles.foodsSectionHeader}>
                <Text style={styles.foodsSectionTitle}>Recommended Foods</Text>
                <Text style={styles.foodsSectionSubtitle}>Foods that can help your condition</Text>
              </View>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.foodsScroll}
              >
                {deduplicateFoods(analysis.remedy.specificFoods).slice(0, 8).map((food, index) => (
                  <View key={index} style={styles.foodCardSimple}>
                    <LinearGradient
                      colors={[colors.white, colors.offWhite]}
                      style={styles.foodCardSimpleGradient}
                    >
                      {/* Food Image */}
                      <View style={styles.foodCardImageContainer}>
                        <FoodImage
                          foodName={food.displayName || food.name}
                          searchTerm={food.imageSearchTerm}
                          style={styles.foodCardImageSimple}
                          resizeMode="cover"
                        />
                        {/* Info icon button */}
                        <TouchableOpacity
                          style={styles.foodInfoIconButton}
                          onPress={() => handleFoodInfoPress(food)}
                          activeOpacity={0.8}
                        >
                          <Ionicons name="information-circle" size={22} color={colors.white} />
                        </TouchableOpacity>
                      </View>
                      {/* Food name - use displayName from AI cleanup */}
                      <View style={styles.foodCardNameContainer}>
                        <Text style={styles.foodCardNameSimple} numberOfLines={2}>
                          {food.displayName || food.name}
                        </Text>
                      </View>
                    </LinearGradient>
                  </View>
                ))}
              </ScrollView>
            </View>

            {/* Recipes Section */}
            {analysis.remedy.recipes && analysis.remedy.recipes.length > 0 && (
              <View style={styles.recipesSection}>
                <Text style={styles.sectionTitle}>Healthy Recipes</Text>
                <Text style={styles.sectionSubtitleText}>
                  Try these nutritious recipes rich in the nutrients you need
                </Text>
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={styles.recipesScroll}
                >
                  {analysis.remedy.recipes
                    .filter(recipe => isRecipeCompatible(recipe, userDietType, userAllergies))
                    .map((recipe, index) => renderRecipeCard(recipe, index))}
                </ScrollView>
              </View>
            )}

            {/* Sources & Citations */}
            {analysis.sources && (
              <View style={styles.resultCard}>
                <LinearGradient
                  colors={[colors.white, colors.offWhite]}
                  style={styles.resultGradient}
                >
                  <View style={styles.resultHeader}>
                    <View style={styles.resultHeaderIcon}>
                      <Ionicons name="document-text-outline" size={20} color={colors.primaryDark} />
                    </View>
                    <Text style={styles.resultHeaderText}>Data Sources</Text>
                  </View>
                  <Text style={styles.sourcesIntro}>
                    This information is based on data from trusted sources:
                  </Text>
                  {analysis.sources.citations && analysis.sources.citations.map((citation, index) => (
                    <TouchableOpacity
                      key={index}
                      style={styles.citationItem}
                      onPress={() => openLink(citation.url)}
                      activeOpacity={0.7}
                    >
                      <View style={styles.citationBullet} />
                      <View style={styles.citationContent}>
                        <Text style={styles.citationName}>{citation.name}</Text>
                        <Text style={styles.citationDescription}>{citation.description}</Text>
                        <Text style={styles.citationUrl}>{citation.url}</Text>
                      </View>
                    </TouchableOpacity>
                  ))}
                </LinearGradient>
              </View>
            )}

            {/* Disclaimer */}
            <View style={styles.disclaimer}>
              <Text style={styles.disclaimerText}>
                {analysis.disclaimer}
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
                  <Text style={styles.saveButtonText}>Save Remedy</Text>
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

      </ScrollView>

      {/* Food Info Modal */}
      {renderFoodInfoModal()}

      {/* Nutrient Explanation Modal */}
      {renderNutrientModal()}

      {/* Recipe Detail Modal */}
      {renderRecipeModal()}
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
  imageActionText: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.text,
    marginTop: spacing.xs,
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
  resultHeaderIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.sm,
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
  sectionTitle: {
    fontSize: typography['2xl'],
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.xs,
    paddingHorizontal: spacing['2xl'],
  },
  sectionSubtitleText: {
    fontSize: typography.sm,
    color: colors.textLight,
    marginBottom: spacing.base,
    paddingHorizontal: spacing['2xl'],
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
  // Foods Section Styles
  foodsSection: {
    marginBottom: spacing.lg,
  },
  foodsSectionHeader: {
    paddingHorizontal: spacing['2xl'],
    marginBottom: spacing.base,
  },
  foodsSectionTitle: {
    fontSize: typography['2xl'],
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  foodsSectionSubtitle: {
    fontSize: typography.sm,
    color: colors.textLight,
  },
  foodsScroll: {
    paddingHorizontal: spacing['2xl'],
    gap: spacing.base,
  },
  foodCard: {
    width: 160,
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.md,
    marginRight: spacing.base,
  },
  foodCardGradient: {
    borderRadius: borderRadius.xl,
  },
  foodCardImage: {
    width: '100%',
    height: 120,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
  },
  foodCardContent: {
    padding: spacing.sm,
  },
  foodCardName: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  foodCardNutrients: {
    fontSize: typography.xs,
    color: colors.textLight,
    marginBottom: spacing.sm,
  },
  foodCardRecipeBadge: {
    backgroundColor: colors.primaryDark,
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
    borderRadius: borderRadius.sm,
    alignItems: 'center',
  },
  foodCardRecipeText: {
    fontSize: typography.xs,
    fontWeight: '600',
    color: colors.white,
  },
  // Simplified Food Card Styles
  foodCardSimple: {
    width: 130,
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.md,
    marginRight: spacing.base,
  },
  foodCardSimpleGradient: {
    borderRadius: borderRadius.xl,
  },
  foodCardImageContainer: {
    position: 'relative',
  },
  foodCardImageSimple: {
    width: '100%',
    height: 110,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
  },
  foodInfoIconButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  foodCardNameContainer: {
    padding: spacing.sm,
    paddingTop: spacing.xs,
  },
  foodCardNameSimple: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.text,
    textAlign: 'center',
    lineHeight: typography.sm * 1.3,
  },
  // Food Info Modal Styles
  foodInfoModalContent: {
    width: screenWidth - 60,
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.lg,
  },
  foodInfoModalGradient: {
    paddingBottom: spacing.lg,
  },
  foodInfoHeader: {
    position: 'relative',
  },
  foodInfoImage: {
    width: '100%',
    height: 160,
  },
  foodInfoCloseButton: {
    position: 'absolute',
    top: 12,
    right: 12,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  foodInfoTitle: {
    fontSize: typography.xl,
    fontWeight: '700',
    color: colors.text,
    textAlign: 'center',
    marginTop: spacing.base,
    marginBottom: spacing.xs,
    paddingHorizontal: spacing.lg,
  },
  foodInfoSubtitle: {
    fontSize: typography.sm,
    fontWeight: '400',
    color: colors.textLight,
    textAlign: 'center',
    marginBottom: spacing.sm,
    paddingHorizontal: spacing.lg,
    fontStyle: 'italic',
  },
  foodInfoTipContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.primaryLight,
    marginHorizontal: spacing.lg,
    padding: spacing.sm,
    borderRadius: borderRadius.md,
    gap: spacing.xs,
    marginBottom: spacing.base,
  },
  foodInfoTip: {
    flex: 1,
    fontSize: typography.sm,
    color: colors.text,
    lineHeight: typography.sm * 1.4,
  },
  foodInfoNutrientsSection: {
    paddingHorizontal: spacing.lg,
    marginBottom: spacing.sm,
  },
  foodInfoSectionTitle: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.textMuted,
    marginBottom: spacing.xs,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  foodInfoNutrientsList: {
    backgroundColor: colors.gray50,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
  },
  foodInfoNutrientItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: colors.gray100,
  },
  foodInfoNutrientName: {
    fontSize: typography.sm,
    color: colors.text,
  },
  foodInfoNutrientValue: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.primaryDark,
  },
  foodInfoSourceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    marginTop: spacing.sm,
  },
  foodInfoSourceText: {
    fontSize: typography.xs,
    color: colors.textMuted,
  },
  recipesSection: {
    marginBottom: spacing.lg,
  },
  recipesScroll: {
    paddingHorizontal: spacing['2xl'],
    gap: spacing.base,
  },
  recipeCard: {
    width: 280,
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.lg,
  },
  recipeGradient: {
    borderRadius: borderRadius.xl,
  },
  recipeImage: {
    width: '100%',
    height: 160,
  },
  recipeContent: {
    padding: spacing.base,
  },
  recipeTitle: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  recipeMetaRow: {
    flexDirection: 'row',
    gap: spacing.base,
    marginBottom: spacing.sm,
  },
  recipeMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  recipeMetaIcon: {
    fontSize: typography.sm,
    color: colors.textMuted,
  },
  recipeMetaText: {
    fontSize: typography.sm,
    color: colors.textMuted,
  },
  recipeDescription: {
    fontSize: typography.sm,
    color: colors.textLight,
    lineHeight: typography.sm * 1.4,
    marginBottom: spacing.sm,
  },
  recipeSource: {
    fontSize: typography.xs,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  sourcesIntro: {
    fontSize: typography.sm,
    color: colors.textLight,
    marginBottom: spacing.base,
  },
  citationItem: {
    flexDirection: 'row',
    marginBottom: spacing.base,
    alignItems: 'flex-start',
  },
  citationBullet: {
    width: 6,
    height: 6,
    borderRadius: borderRadius.full,
    backgroundColor: colors.info,
    marginTop: 8,
    marginRight: spacing.sm,
  },
  citationContent: {
    flex: 1,
  },
  citationName: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  citationDescription: {
    fontSize: typography.sm,
    color: colors.textLight,
    marginBottom: spacing.xs,
  },
  citationUrl: {
    fontSize: typography.xs,
    color: colors.info,
    textDecorationLine: 'underline',
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
  // Nutrient hint
  nutrientHint: {
    fontSize: typography.xs,
    color: colors.textMuted,
    fontStyle: 'italic',
    marginBottom: spacing.sm,
  },
  // Key ingredient badge on recipe cards
  keyIngredientBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryLight,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
    alignSelf: 'flex-start',
    marginBottom: spacing.sm,
    gap: 4,
  },
  keyIngredientText: {
    fontSize: typography.xs,
    color: colors.primaryDark,
    fontWeight: '600',
  },
  recipeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primaryDark,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.base,
    borderRadius: borderRadius.md,
    gap: spacing.xs,
  },
  recipeButtonText: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.white,
  },
  // Modal Overlay
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  // Nutrient Modal
  nutrientModalContent: {
    width: screenWidth - 48,
    maxHeight: '70%',
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.lg,
  },
  nutrientModalGradient: {
    padding: spacing.lg,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  nutrientModalTitle: {
    fontSize: typography['2xl'],
    fontWeight: '800',
    color: colors.primaryDark,
    flex: 1,
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: borderRadius.full,
    backgroundColor: colors.gray100,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.textLight,
  },
  nutrientModalDivider: {
    height: 2,
    backgroundColor: colors.primaryLight,
    marginVertical: spacing.base,
    borderRadius: 1,
  },
  nutrientModalSubtitle: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  nutrientModalScroll: {
    maxHeight: 200,
  },
  nutrientModalExplanation: {
    fontSize: typography.base,
    color: colors.textLight,
    lineHeight: typography.base * 1.6,
  },
  modalSourceBadge: {
    marginTop: spacing.base,
    backgroundColor: colors.gray50,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
    alignSelf: 'flex-start',
  },
  modalSourceText: {
    fontSize: typography.xs,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  // Recipe Modal - Full Screen
  recipeModalContainer: {
    flex: 1,
    backgroundColor: colors.white,
  },
  recipeModalGradient: {
    flex: 1,
  },
  recipeModalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.base,
    paddingTop: Platform.OS === 'ios' ? 50 : 16,
    paddingBottom: spacing.base,
    borderBottomWidth: 1,
    borderBottomColor: colors.gray100,
    backgroundColor: colors.white,
  },
  recipeModalHeaderTitle: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.text,
  },
  recipeCloseButton: {
    width: 36,
    height: 36,
    borderRadius: borderRadius.full,
    backgroundColor: colors.gray100,
    justifyContent: 'center',
    alignItems: 'center',
  },
  recipeModalScroll: {
    flex: 1,
  },
  recipeModalScrollContent: {
    paddingBottom: 40,
  },
  recipeModalImage: {
    width: '100%',
    height: 220,
  },
  recipeModalTitle: {
    fontSize: typography['2xl'],
    fontWeight: '800',
    color: colors.text,
    marginTop: spacing.lg,
    marginBottom: spacing.base,
    paddingHorizontal: spacing.lg,
  },
  recipeModalMetaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.lg,
    paddingHorizontal: spacing.lg,
  },
  recipeModalMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryLight,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
    gap: spacing.xs,
  },
  recipeModalMetaLabel: {
    fontSize: typography.xs,
    color: colors.textMuted,
  },
  recipeModalMetaValue: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.primaryDark,
  },
  recipeModalSection: {
    marginBottom: spacing.lg,
    paddingHorizontal: spacing.lg,
  },
  recipeModalSectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  recipeModalSectionTitle: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.primaryDark,
  },
  recipeModalDescription: {
    fontSize: typography.base,
    color: colors.textLight,
    lineHeight: typography.base * 1.5,
  },
  ingredientsList: {
    backgroundColor: colors.offWhite,
    borderRadius: borderRadius.lg,
    padding: spacing.base,
  },
  ingredientItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  ingredientBullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.primary,
    marginTop: 7,
    marginRight: spacing.sm,
  },
  ingredientText: {
    flex: 1,
    fontSize: typography.base,
    lineHeight: typography.base * 1.4,
  },
  ingredientAmount: {
    fontWeight: '600',
    color: colors.primaryDark,
  },
  ingredientName: {
    color: colors.text,
  },
  // Directions Section - Prominent styling
  recipeModalDirectionsSection: {
    marginBottom: spacing.lg,
    paddingHorizontal: spacing.lg,
  },
  recipeModalDirectionsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.base,
  },
  recipeModalDirectionsTitle: {
    fontSize: typography.xl,
    fontWeight: '700',
    color: colors.primaryDark,
  },
  recipeModalDirectionsContent: {
    backgroundColor: colors.gray50,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
  },
  recipeModalInstructions: {
    fontSize: typography.base,
    color: colors.text,
    lineHeight: typography.base * 1.8,
  },
  recipeStepItem: {
    flexDirection: 'row',
    marginBottom: spacing.base,
  },
  recipeStepNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.primaryDark,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.sm,
    marginTop: 2,
  },
  recipeStepNumberText: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.white,
  },
  recipeStepText: {
    flex: 1,
    fontSize: typography.base,
    color: colors.text,
    lineHeight: typography.base * 1.6,
  },
  recipeNoInstructionsNote: {
    marginTop: spacing.base,
    fontSize: typography.sm,
    fontStyle: 'italic',
    color: colors.textMuted,
  },
  recipeNutrientsList: {
    gap: spacing.xs,
  },
  recipeNutrientItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.gray100,
  },
  recipeNutrientName: {
    fontSize: typography.sm,
    color: colors.text,
  },
  recipeNutrientAmount: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.primaryDark,
  },
  recipeModalSourceContainer: {
    paddingHorizontal: spacing.lg,
    marginBottom: spacing.base,
  },
  recipeModalSource: {
    fontSize: typography.xs,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  viewFullRecipeButton: {
    marginHorizontal: spacing.lg,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    marginBottom: spacing.base,
  },
  viewFullRecipeGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.base,
    gap: spacing.sm,
  },
  viewFullRecipeText: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.white,
  },
});

export default HealthScreen;
