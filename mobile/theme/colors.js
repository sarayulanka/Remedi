// Premium Color Palette - Green & White Focus
export const colors = {
  // Primary Green Palette - keeping your original green but enhanced
  primary: '#bdf0cb',           // Your signature light green
  primaryLight: '#e8f8eb',      // Very light mint
  primaryDark: '#8fd9a3',       // Your darker green
  primaryDeep: '#5fb87f',       // Even deeper green
  primaryRich: '#3d9970',       // Rich emerald
  
  // Whites & Backgrounds
  white: '#ffffff',
  offWhite: '#fafcfb',
  cream: '#f8fff9',
  background: '#f8fff9',
  
  // Grays - Premium neutral palette
  gray50: '#f9fafb',
  gray100: '#f3f4f6',
  gray200: '#e5e7eb',
  gray300: '#d1d5db',
  gray: '#dfe6e9',
  grayLight: '#f1f3f5',
  grayDark: '#636e72',
  
  // Text
  text: '#2d3436',
  textLight: '#636e72',
  textMuted: '#95a5a6',
  
  // Semantic Colors
  success: '#00b894',
  successLight: '#d1fae5',
  warning: '#fdcb6e',
  warningLight: '#fef3c7',
  error: '#d63031',
  errorLight: '#fee2e2',
  info: '#3b82f6',
  infoLight: '#dbeafe',
  
  // Shadows & Effects
  shadow: 'rgba(0, 0, 0, 0.06)',
  shadowMedium: 'rgba(0, 0, 0, 0.1)',
  shadowHeavy: 'rgba(0, 0, 0, 0.15)',
  glow: 'rgba(143, 217, 163, 0.3)',
};

// Premium Gradients
export const gradients = {
  // Main backgrounds
  main: ['#e8f8eb', '#f8fff9', '#ffffff'],
  mainReverse: ['#ffffff', '#f8fff9', '#e8f8eb'],
  
  // Buttons - your signature green
  button: ['#8fd9a3', '#bdf0cb'],
  buttonHover: ['#5fb87f', '#8fd9a3'],
  
  // Cards
  card: ['#ffffff', '#f8fff9'],
  cardElevated: ['#ffffff', '#ffffff'],
  
  // Premium effects
  premium: ['#bdf0cb', '#e8f8eb', '#ffffff'],
  success: ['#00b894', '#00d2a0'],
  
  // Overlays
  overlay: ['rgba(255, 255, 255, 0)', 'rgba(255, 255, 255, 0.98)'],
  shimmer: ['rgba(255, 255, 255, 0)', 'rgba(255, 255, 255, 0.8)', 'rgba(255, 255, 255, 0)'],
};

// Premium Shadows
export const shadows = {
  xs: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 4,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 8,
  },
  xl: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.12,
    shadowRadius: 24,
    elevation: 12,
  },
  glow: {
    shadowColor: '#8fd9a3',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 6,
  },
};

// Typography
export const typography = {
  xs: 12,
  sm: 14,
  base: 16,
  lg: 18,
  xl: 20,
  '2xl': 24,
  '3xl': 30,
  '4xl': 36,
  '5xl': 48,
  '6xl': 60,
  '7xl': 72,
};

// Spacing
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  '2xl': 32,
  '3xl': 40,
  '4xl': 48,
  '5xl': 64,
};

// Border Radius
export const borderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  '2xl': 24,
  '3xl': 28,
  full: 9999,
};

export default {
  colors,
  gradients,
  shadows,
  typography,
  spacing,
  borderRadius,
};
