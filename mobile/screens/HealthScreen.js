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
  Linking,
  Modal,
  TouchableWithoutFeedback,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';
import { healthAPI } from '../services/api';

const { width: screenWidth } = Dimensions.get('window');

// Food images mapping for common healthy foods
const FOOD_IMAGES = {
  'salmon': 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=300',
  'spinach': 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=300',
  'eggs': 'https://images.unsplash.com/photo-1582169296194-e4d644c48063?w=300',
  'yogurt': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=300',
  'sweet potato': 'https://images.unsplash.com/photo-1596097635121-14b63b7a0c19?w=300',
  'avocado': 'https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=300',
  'almonds': 'https://images.unsplash.com/photo-1508061253366-f7da158b6d46?w=300',
  'berries': 'https://images.unsplash.com/photo-1488330890490-a4ab9fa5d4a2?w=300',
  'blueberries': 'https://images.unsplash.com/photo-1498557850523-fd3d118b962e?w=300',
  'ginger': 'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=300',
  'turmeric': 'https://images.unsplash.com/photo-1615485290259-1acb7ec94f5e?w=300',
  'oats': 'https://images.unsplash.com/photo-1517673400267-0251440c45dc?w=300',
  'beans': 'https://images.unsplash.com/photo-1551463851-68e6bde54b33?w=300',
  'dark chocolate': 'https://images.unsplash.com/photo-1553530666-ba11a90bb8b3?w=300',
  'citrus': 'https://images.unsplash.com/photo-1582979512210-99b6a53386f9?w=300',
  'oranges': 'https://images.unsplash.com/photo-1582979512210-99b6a53386f9?w=300',
  'leafy greens': 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=300',
  'kale': 'https://images.unsplash.com/photo-1524179091875-bf99a9a6af57?w=300',
  'walnuts': 'https://images.unsplash.com/photo-1563635006903-5dd2d5e91b5c?w=300',
  'banana': 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=300',
  'broccoli': 'https://images.unsplash.com/photo-1459411552884-841db9b3cc2a?w=300',
  'carrots': 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=300',
  'tomatoes': 'https://images.unsplash.com/photo-1561136594-7f68413baa99?w=300',
  'chicken': 'https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=300',
  'fish': 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=300',
  'garlic': 'https://images.unsplash.com/photo-1540148426945-6cf22a6b2f6a?w=300',
  'honey': 'https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=300',
  'quinoa': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300',
  'brown rice': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300',
  'lentils': 'https://images.unsplash.com/photo-1585996746416-8c3b1d1f3a45?w=300',
  'mushrooms': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=300',
  'bell pepper': 'https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=300',
  'olive oil': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300',
  'green tea': 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=300',
  'default': 'https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=300',
};

// Food to recipe mappings with full directions
const FOOD_RECIPES = {
  'salmon': {
    title: 'Herb-Crusted Baked Salmon',
    image: 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400',
    readyInMinutes: 25,
    servings: 4,
    keyIngredient: 'salmon',
    description: 'Wild-caught salmon baked with fresh dill, lemon, and garlic. Rich in omega-3 fatty acids.',
    instructions: '1. Preheat oven to 400°F (200°C).\n\n2. Place salmon fillets on a lined baking sheet.\n\n3. Mix 2 tbsp olive oil, 2 cloves minced garlic, 2 tbsp fresh dill (chopped), salt, and pepper.\n\n4. Brush the herb mixture generously over the salmon.\n\n5. Top with thin lemon slices.\n\n6. Bake for 15-20 minutes until salmon flakes easily with a fork.\n\n7. Let rest for 2 minutes and serve with your choice of vegetables.',
    source: 'Remedi Kitchen',
    nutrients: [{ name: 'Omega-3', amount: 2260, unit: 'mg' }, { name: 'Protein', amount: 25, unit: 'g' }],
  },
  'spinach': {
    title: 'Garlic Sauteed Spinach',
    image: 'https://images.unsplash.com/photo-1574316071802-0d684efa7bf5?w=400',
    readyInMinutes: 10,
    servings: 2,
    keyIngredient: 'spinach',
    description: 'Quick and nutritious spinach sauteed with garlic and topped with toasted pine nuts.',
    instructions: '1. Toast 2 tbsp pine nuts in a dry pan over medium heat until golden (2-3 minutes). Set aside.\n\n2. Heat 2 tbsp olive oil in a large pan over medium heat.\n\n3. Add 3 cloves minced garlic and saute for 30 seconds until fragrant.\n\n4. Add 6 cups fresh spinach and toss constantly until just wilted (2-3 minutes).\n\n5. Season with salt, pepper, and a squeeze of fresh lemon juice.\n\n6. Transfer to a serving dish and top with toasted pine nuts.\n\n7. Serve immediately as a side dish.',
    source: 'Remedi Kitchen',
    nutrients: [{ name: 'Iron', amount: 3.6, unit: 'mg' }, { name: 'Vitamin K', amount: 483, unit: 'mcg' }],
  },
  'eggs': {
    title: 'Vegetable Frittata',
    image: 'https://images.unsplash.com/photo-1510693206972-df098062cb71?w=400',
    readyInMinutes: 30,
    servings: 4,
    keyIngredient: 'eggs',
    description: 'Protein-packed frittata loaded with colorful vegetables.',
    instructions: '1. Preheat oven to 375°F (190°C).\n\n2. Whisk 8 large eggs with 1/4 cup milk, salt, and pepper in a bowl.\n\n3. Heat 2 tbsp olive oil in an oven-safe skillet over medium heat.\n\n4. Saute 1 diced bell pepper, 1/2 diced onion, and 1 cup spinach until softened (5 minutes).\n\n5. Pour egg mixture over the vegetables and stir gently.\n\n6. Cook on stovetop until edges start to set (3-4 minutes).\n\n7. Transfer skillet to oven and bake for 15-20 minutes until center is set.\n\n8. Let cool 5 minutes before slicing into wedges.',
    source: 'Remedi Kitchen',
    nutrients: [{ name: 'Protein', amount: 18, unit: 'g' }, { name: 'Vitamin D', amount: 4, unit: 'mcg' }],
  },
  'avocado': {
    title: 'Loaded Avocado Toast',
    image: 'https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=400',
    readyInMinutes: 10,
    servings: 2,
    keyIngredient: 'avocado',
    description: 'Creamy avocado on whole grain toast with everything bagel seasoning and optional toppings.',
    instructions: '1. Toast 2 slices of whole grain bread until golden and crispy.\n\n2. Cut 1 ripe avocado in half and remove the pit.\n\n3. Scoop avocado flesh onto each toast slice.\n\n4. Mash with a fork to your desired consistency (chunky or smooth).\n\n5. Season with salt, pepper, and a squeeze of fresh lime juice.\n\n6. Sprinkle generously with everything bagel seasoning.\n\n7. Optional toppings: cherry tomatoes, poached egg, red pepper flakes, or microgreens.\n\n8. Serve immediately for best texture.',
    source: 'Remedi Kitchen',
    nutrients: [{ name: 'Healthy Fats', amount: 15, unit: 'g' }, { name: 'Fiber', amount: 7, unit: 'g' }],
  },
  'berries': {
    title: 'Antioxidant Berry Smoothie Bowl',
    image: 'https://images.unsplash.com/photo-1590301157890-4810ed352733?w=400',
    readyInMinutes: 10,
    servings: 1,
    keyIngredient: 'berries',
    description: 'Thick and creamy smoothie bowl packed with antioxidant-rich berries.',
    instructions: '1. Add 1 cup frozen mixed berries to a blender.\n\n2. Add 1/2 frozen banana for creaminess.\n\n3. Pour in 1/4 cup almond milk (just enough to blend).\n\n4. Blend until thick and smooth - should be thicker than a regular smoothie.\n\n5. Pour into a bowl.\n\n6. Top with fresh berries, sliced banana, and granola.\n\n7. Add 1 tbsp chia seeds and a drizzle of honey.\n\n8. Enjoy immediately before it melts!',
    source: 'Remedi Kitchen',
    nutrients: [{ name: 'Antioxidants', amount: 9000, unit: 'ORAC' }, { name: 'Vitamin C', amount: 28, unit: 'mg' }],
  },
  'yogurt': {
    title: 'Probiotic Power Parfait',
    image: 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400',
    readyInMinutes: 5,
    servings: 1,
    keyIngredient: 'yogurt',
    description: 'Layered Greek yogurt with fresh berries, granola, and honey for gut health.',
    instructions: '1. Choose a tall glass or mason jar for layering.\n\n2. Add 1/3 cup Greek yogurt to the bottom.\n\n3. Add a layer of fresh mixed berries.\n\n4. Sprinkle 2 tbsp granola on top.\n\n5. Repeat the layers: yogurt, berries, granola.\n\n6. Drizzle 1 tbsp honey on top.\n\n7. Add a few extra berries for garnish.\n\n8. Serve immediately or refrigerate up to 4 hours.',
    source: 'Remedi Kitchen',
    nutrients: [{ name: 'Protein', amount: 15, unit: 'g' }, { name: 'Probiotics', amount: 100, unit: 'million CFU' }],
  },
  'ginger': {
    title: 'Ginger-Turmeric Healing Soup',
    image: 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400',
    readyInMinutes: 30,
    servings: 4,
    keyIngredient: 'ginger',
    description: 'Warming anti-inflammatory soup with fresh ginger and turmeric.',
    instructions: '1. Heat 2 tbsp olive oil in a large pot over medium heat.\n\n2. Saute 1 diced onion until soft (5 minutes).\n\n3. Add 2 tbsp freshly grated ginger and 1 tsp turmeric powder. Stir for 1 minute.\n\n4. Add 4 cups vegetable broth and bring to a boil.\n\n5. Add 2 diced carrots and simmer for 15 minutes.\n\n6. Stir in 1/2 cup coconut milk and simmer 5 more minutes.\n\n7. Season with salt, pepper, and fresh lime juice.\n\n8. Garnish with fresh cilantro and serve warm.',
    source: 'Remedi Kitchen',
    nutrients: [{ name: 'Anti-inflammatory compounds', amount: 500, unit: 'mg' }],
  },
  'oats': {
    title: 'Overnight Oats with Chia',
    image: 'https://images.unsplash.com/photo-1517673400267-0251440c45dc?w=400',
    readyInMinutes: 5,
    servings: 1,
    keyIngredient: 'oats',
    description: 'No-cook oatmeal prepared overnight for a quick nutritious breakfast.',
    instructions: '1. In a jar or container, combine 1/2 cup rolled oats with 1/2 cup milk.\n\n2. Add 1 tbsp chia seeds for extra fiber and omega-3s.\n\n3. Stir in 1 tbsp maple syrup or honey.\n\n4. Add a pinch of cinnamon for flavor.\n\n5. Stir everything well to combine.\n\n6. Cover and refrigerate overnight (at least 6 hours).\n\n7. In the morning, stir and add more milk if needed.\n\n8. Top with fresh fruit, nuts, and a drizzle of nut butter.',
    source: 'Remedi Kitchen',
    nutrients: [{ name: 'Fiber', amount: 8, unit: 'g' }, { name: 'Complex Carbs', amount: 27, unit: 'g' }],
  },
  'broccoli': {
    title: 'Roasted Garlic Broccoli',
    image: 'https://images.unsplash.com/photo-1459411552884-841db9b3cc2a?w=400',
    readyInMinutes: 25,
    servings: 4,
    keyIngredient: 'broccoli',
    description: 'Crispy roasted broccoli with garlic, lemon, and parmesan.',
    instructions: '1. Preheat oven to 425°F (220°C).\n\n2. Cut 2 heads of broccoli into florets.\n\n3. Toss with 3 tbsp olive oil, 4 minced garlic cloves, salt, and pepper.\n\n4. Spread in a single layer on a baking sheet.\n\n5. Roast for 20-25 minutes until edges are crispy and browned.\n\n6. Remove from oven and squeeze fresh lemon juice over top.\n\n7. Sprinkle with 2 tbsp grated parmesan cheese.\n\n8. Serve hot as a side dish.',
    source: 'Remedi Kitchen',
    nutrients: [{ name: 'Vitamin C', amount: 135, unit: 'mg' }, { name: 'Fiber', amount: 5, unit: 'g' }],
  },
  'almonds': {
    title: 'Almond-Crusted Chicken',
    image: 'https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?w=400',
    readyInMinutes: 35,
    servings: 4,
    keyIngredient: 'almonds',
    description: 'Tender chicken breasts with a crunchy, nutritious almond coating.',
    instructions: '1. Preheat oven to 400°F (200°C).\n\n2. Pulse 1 cup raw almonds in a food processor until finely ground.\n\n3. Mix ground almonds with 1 tsp dried herbs, salt, and pepper.\n\n4. Season 4 chicken breasts with salt and pepper.\n\n5. Dip each chicken breast in beaten egg.\n\n6. Press almond mixture firmly onto both sides.\n\n7. Place on a lined baking sheet and bake 25-30 minutes until internal temp reaches 165°F.\n\n8. Let rest 5 minutes before serving.',
    source: 'Remedi Kitchen',
    nutrients: [{ name: 'Protein', amount: 35, unit: 'g' }, { name: 'Vitamin E', amount: 7, unit: 'mg' }],
  },
  'default': {
    title: 'Nutritious Power Bowl',
    image: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400',
    readyInMinutes: 20,
    servings: 2,
    keyIngredient: 'mixed vegetables',
    description: 'A colorful bowl packed with nutrient-dense ingredients.',
    instructions: '1. Cook 1 cup quinoa according to package directions.\n\n2. While quinoa cooks, roast your favorite vegetables at 400°F for 15 minutes.\n\n3. Prepare a simple dressing: whisk 2 tbsp olive oil, 1 tbsp lemon juice, salt, and pepper.\n\n4. Divide quinoa between two bowls.\n\n5. Arrange roasted vegetables on top.\n\n6. Add any protein of your choice (chickpeas, tofu, or grilled chicken).\n\n7. Drizzle with dressing.\n\n8. Top with avocado slices and seeds.',
    source: 'Remedi Kitchen',
    nutrients: [{ name: 'Fiber', amount: 12, unit: 'g' }, { name: 'Protein', amount: 15, unit: 'g' }],
  },
};

// Helper function to get food image
const getFoodImage = (foodName) => {
  const lowerName = foodName.toLowerCase();
  for (const [key, url] of Object.entries(FOOD_IMAGES)) {
    if (lowerName.includes(key) || key.includes(lowerName.split(' ')[0])) {
      return url;
    }
  }
  return FOOD_IMAGES.default;
};

// Helper function to get recipe for a food
const getRecipeForFood = (foodName) => {
  const lowerName = foodName.toLowerCase();
  for (const [key, recipe] of Object.entries(FOOD_RECIPES)) {
    if (lowerName.includes(key) || key.includes(lowerName.split(' ')[0])) {
      return recipe;
    }
  }
  return FOOD_RECIPES.default;
};

const HealthScreen = () => {
  const [mode, setMode] = useState('image');
  const [image, setImage] = useState(null);
  const [textDescription, setTextDescription] = useState('');
  const [userConcerns, setUserConcerns] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  // Modal states
  const [selectedNutrient, setSelectedNutrient] = useState(null);
  const [nutrientModalVisible, setNutrientModalVisible] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [recipeModalVisible, setRecipeModalVisible] = useState(false);

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
      transparent={true}
      animationType="slide"
      onRequestClose={() => setRecipeModalVisible(false)}
    >
      <TouchableWithoutFeedback onPress={() => setRecipeModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <TouchableWithoutFeedback onPress={(e) => e.stopPropagation()}>
            <View style={styles.recipeModalContent}>
              <LinearGradient
                colors={[colors.white, colors.offWhite]}
                style={styles.recipeModalGradient}
              >
                <TouchableOpacity
                  onPress={() => setRecipeModalVisible(false)}
                  style={styles.recipeCloseButton}
                >
                  <Ionicons name="close" size={24} color={colors.text} />
                </TouchableOpacity>

                {selectedRecipe?.image && (
                  <Image
                    source={{ uri: selectedRecipe.image }}
                    style={styles.recipeModalImage}
                    resizeMode="cover"
                  />
                )}

                <ScrollView
                  style={styles.recipeModalScroll}
                  showsVerticalScrollIndicator={false}
                >
                  <Text style={styles.recipeModalTitle}>{selectedRecipe?.title}</Text>

                  <View style={styles.recipeModalMetaRow}>
                    {selectedRecipe?.readyInMinutes && (
                      <View style={styles.recipeModalMeta}>
                        <Text style={styles.recipeModalMetaLabel}>Prep Time</Text>
                        <Text style={styles.recipeModalMetaValue}>{selectedRecipe.readyInMinutes} min</Text>
                      </View>
                    )}
                    {selectedRecipe?.servings && (
                      <View style={styles.recipeModalMeta}>
                        <Text style={styles.recipeModalMetaLabel}>Servings</Text>
                        <Text style={styles.recipeModalMetaValue}>{selectedRecipe.servings}</Text>
                      </View>
                    )}
                    {selectedRecipe?.keyIngredient && (
                      <View style={styles.recipeModalMeta}>
                        <Text style={styles.recipeModalMetaLabel}>Key Ingredient</Text>
                        <Text style={styles.recipeModalMetaValue}>{selectedRecipe.keyIngredient}</Text>
                      </View>
                    )}
                  </View>

                  {selectedRecipe?.description && (
                    <View style={styles.recipeModalSection}>
                      <Text style={styles.recipeModalSectionTitle}>About</Text>
                      <Text style={styles.recipeModalDescription}>{selectedRecipe.description}</Text>
                    </View>
                  )}

                  <View style={styles.recipeModalSection}>
                    <Text style={styles.recipeModalSectionTitle}>Directions</Text>
                    {selectedRecipe?.instructions ? (
                      <Text style={styles.recipeModalInstructions}>{selectedRecipe.instructions}</Text>
                    ) : (
                      <Text style={styles.recipeModalInstructions}>
                        1. Prepare all your ingredients according to the recipe requirements.{'\n\n'}
                        2. Follow standard cooking techniques for this dish type.{'\n\n'}
                        3. Season to taste with salt, pepper, and your favorite herbs.{'\n\n'}
                        4. Serve warm and enjoy your nutritious meal!
                      </Text>
                    )}
                  </View>

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

                  <View style={styles.recipeModalSourceContainer}>
                    <Text style={styles.recipeModalSource}>
                      Source: {selectedRecipe?.source || 'Remedi Kitchen'}
                    </Text>
                  </View>

                  {selectedRecipe?.sourceUrl && (
                    <TouchableOpacity
                      style={styles.viewFullRecipeButton}
                      onPress={() => openLink(selectedRecipe.sourceUrl)}
                    >
                      <Text style={styles.viewFullRecipeText}>View Full Recipe Online</Text>
                    </TouchableOpacity>
                  )}

                  <View style={{ height: spacing.xl }} />
                </ScrollView>
              </LinearGradient>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );

  const renderRecipeCard = (recipe, index) => (
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
        {recipe.image && (
          <Image
            source={{ uri: recipe.image }}
            style={styles.recipeImage}
            resizeMode="cover"
          />
        )}
        <View style={styles.recipeContent}>
          <Text style={styles.recipeTitle}>{recipe.title}</Text>
          <View style={styles.recipeMetaRow}>
            {recipe.readyInMinutes && (
              <View style={styles.recipeMeta}>
                <Text style={styles.recipeMetaIcon}>&#9719;</Text>
                <Text style={styles.recipeMetaText}>{recipe.readyInMinutes} min</Text>
              </View>
            )}
            {recipe.servings && (
              <View style={styles.recipeMeta}>
                <Text style={styles.recipeMetaIcon}>&#127860;</Text>
                <Text style={styles.recipeMetaText}>{recipe.servings} servings</Text>
              </View>
            )}
          </View>
          {recipe.description && (
            <Text style={styles.recipeDescription} numberOfLines={2}>
              {recipe.description}
            </Text>
          )}
          {recipe.keyIngredient && (
            <View style={styles.keyIngredientBadge}>
              <Text style={styles.keyIngredientText}>Made with {recipe.keyIngredient}</Text>
            </View>
          )}
          <View style={styles.recipeButton}>
            <Text style={styles.recipeButtonText}>Tap for Directions</Text>
          </View>
          <Text style={styles.recipeSource}>Source: {recipe.source}</Text>
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );

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

            {/* Recommended Foods - Scrollable with Images */}
            <View style={styles.foodsSection}>
              <View style={styles.foodsSectionHeader}>
                <Text style={styles.foodsSectionTitle}>Recommended Foods</Text>
                <Text style={styles.foodsSectionSubtitle}>Tap a food to see a recipe</Text>
              </View>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.foodsScroll}
              >
                {analysis.remedy.specificFoods.slice(0, 8).map((food, index) => {
                  const recipe = getRecipeForFood(food.name);
                  return (
                    <TouchableOpacity
                      key={index}
                      style={styles.foodCard}
                      onPress={() => handleRecipePress(recipe)}
                      activeOpacity={0.9}
                    >
                      <LinearGradient
                        colors={[colors.white, colors.offWhite]}
                        style={styles.foodCardGradient}
                      >
                        <Image
                          source={{ uri: getFoodImage(food.name) }}
                          style={styles.foodCardImage}
                          resizeMode="cover"
                        />
                        <View style={styles.foodCardContent}>
                          <Text style={styles.foodCardName} numberOfLines={2}>{food.name}</Text>
                          {food.keyNutrients && food.keyNutrients.length > 0 && (
                            <Text style={styles.foodCardNutrients} numberOfLines={1}>
                              {food.keyNutrients.map((n) => n.name).join(', ')}
                            </Text>
                          )}
                          <View style={styles.foodCardRecipeBadge}>
                            <Text style={styles.foodCardRecipeText}>View Recipe</Text>
                          </View>
                        </View>
                      </LinearGradient>
                    </TouchableOpacity>
                  );
                })}
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
                  {analysis.remedy.recipes.map((recipe, index) => renderRecipeCard(recipe, index))}
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

        <View style={styles.bottomSpacer} />
      </ScrollView>

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
  recipeButton: {
    backgroundColor: colors.primaryDark,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.base,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  recipeButtonText: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.white,
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
  bottomSpacer: {
    height: spacing['2xl'],
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
    backgroundColor: colors.primaryLight,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
    alignSelf: 'flex-start',
    marginBottom: spacing.sm,
  },
  keyIngredientText: {
    fontSize: typography.xs,
    color: colors.primaryDark,
    fontWeight: '600',
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
  // Recipe Modal
  recipeModalContent: {
    width: screenWidth - 32,
    maxHeight: '85%',
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.lg,
  },
  recipeModalGradient: {
    flex: 1,
  },
  recipeCloseButton: {
    position: 'absolute',
    top: spacing.base,
    right: spacing.base,
    width: 36,
    height: 36,
    borderRadius: borderRadius.full,
    backgroundColor: colors.white,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
    ...shadows.md,
  },
  recipeModalImage: {
    width: '100%',
    height: 200,
  },
  recipeModalScroll: {
    padding: spacing.lg,
    flex: 1,
  },
  recipeModalTitle: {
    fontSize: typography['2xl'],
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.base,
  },
  recipeModalMetaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.base,
    marginBottom: spacing.lg,
  },
  recipeModalMeta: {
    backgroundColor: colors.gray50,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.md,
  },
  recipeModalMetaLabel: {
    fontSize: typography.xs,
    color: colors.textMuted,
  },
  recipeModalMetaValue: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.text,
  },
  recipeModalSection: {
    marginBottom: spacing.lg,
  },
  recipeModalSectionTitle: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.primaryDark,
    marginBottom: spacing.sm,
  },
  recipeModalDescription: {
    fontSize: typography.base,
    color: colors.textLight,
    lineHeight: typography.base * 1.5,
  },
  recipeModalInstructions: {
    fontSize: typography.base,
    color: colors.text,
    lineHeight: typography.base * 1.8,
  },
  recipeNutrientsList: {
    gap: spacing.xs,
  },
  recipeNutrientItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing.xs,
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
    marginTop: spacing.sm,
    marginBottom: spacing.base,
  },
  recipeModalSource: {
    fontSize: typography.xs,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  viewFullRecipeButton: {
    backgroundColor: colors.primaryDark,
    paddingVertical: spacing.base,
    borderRadius: borderRadius.lg,
    alignItems: 'center',
    marginBottom: spacing.base,
  },
  viewFullRecipeText: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.white,
  },
});

export default HealthScreen;
