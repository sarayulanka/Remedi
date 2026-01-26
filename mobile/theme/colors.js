// Premium Color Palette - Green & White Focus
export const colors = {
  // Primary Green Palette - slightly darker for better white text readability
  primary: '#9ae3b3',           // Signature green (slightly darker for readability)
  primaryLight: '#d4f0dc',      // Light mint (slightly darker)
  primaryDark: '#6dc990',       // Darker green (slightly darker)
  primaryDeep: '#4faa6f',       // Deep green (slightly darker)
  primaryRich: '#2d8a5e',       // Rich emerald (slightly darker)
  
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

  // Achievement Colors - Gold accent palette
  gold: '#F59E0B',
  goldLight: '#FCD34D',
  goldDark: '#D97706',
  goldBg: '#FEF3C7',

  // Streak flame colors
  flame: '#f97316',
  flameLight: '#fdba74',
  flameBg: '#fff7ed',

  // Freeze/shield colors
  freeze: '#3B82F6',
  freezeLight: '#93C5FD',
  freezeBg: '#DBEAFE',
  
  // Shadows & Effects
  shadow: 'rgba(0, 0, 0, 0.06)',
  shadowMedium: 'rgba(0, 0, 0, 0.1)',
  shadowHeavy: 'rgba(0, 0, 0, 0.15)',
  glow: 'rgba(109, 201, 144, 0.3)',
};

// Premium Gradients
export const gradients = {
  // Main backgrounds
  main: ['#d4f0dc', '#f0faf2', '#ffffff'],
  mainReverse: ['#ffffff', '#f0faf2', '#d4f0dc'],

  // Buttons - slightly darker for better white text readability
  button: ['#6dc990', '#9ae3b3'],
  buttonHover: ['#4faa6f', '#6dc990'],
  
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
    shadowColor: '#6dc990',
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
