import { Animated, Easing } from 'react-native';

/**
 * Fade in animation
 * @param {Animated.Value} animatedValue - The animated value to control
 * @param {number} duration - Duration in milliseconds
 * @param {number} delay - Delay before starting in milliseconds
 */
export const fadeIn = (animatedValue, duration = 600, delay = 0) => {
  return Animated.timing(animatedValue, {
    toValue: 1,
    duration,
    delay,
    easing: Easing.out(Easing.cubic),
    useNativeDriver: true,
  });
};

/**
 * Fade out animation
 * @param {Animated.Value} animatedValue - The animated value to control
 * @param {number} duration - Duration in milliseconds
 */
export const fadeOut = (animatedValue, duration = 400) => {
  return Animated.timing(animatedValue, {
    toValue: 0,
    duration,
    easing: Easing.in(Easing.cubic),
    useNativeDriver: true,
  });
};

/**
 * Slide in from bottom animation
 * @param {Animated.Value} animatedValue - The animated value to control
 * @param {number} duration - Duration in milliseconds
 */
export const slideInFromBottom = (animatedValue, duration = 500) => {
  return Animated.spring(animatedValue, {
    toValue: 0,
    tension: 65,
    friction: 10,
    useNativeDriver: true,
  });
};

/**
 * Scale animation (bounce effect)
 * @param {Animated.Value} animatedValue - The animated value to control
 * @param {number} toValue - Target scale value
 * @param {number} duration - Duration in milliseconds
 */
export const scaleAnimation = (animatedValue, toValue = 1, duration = 400) => {
  return Animated.spring(animatedValue, {
    toValue,
    tension: 100,
    friction: 7,
    useNativeDriver: true,
  });
};

/**
 * Pulse animation (for buttons, badges)
 * @param {Animated.Value} animatedValue - The animated value to control
 */
export const pulse = (animatedValue) => {
  return Animated.sequence([
    Animated.timing(animatedValue, {
      toValue: 1.1,
      duration: 200,
      easing: Easing.out(Easing.ease),
      useNativeDriver: true,
    }),
    Animated.timing(animatedValue, {
      toValue: 1,
      duration: 200,
      easing: Easing.in(Easing.ease),
      useNativeDriver: true,
    }),
  ]);
};

/**
 * Stagger animation for lists
 * @param {Array<Animated.Value>} animatedValues - Array of animated values
 * @param {number} staggerDelay - Delay between each item in milliseconds
 */
export const staggerFadeIn = (animatedValues, staggerDelay = 100) => {
  return Animated.stagger(
    staggerDelay,
    animatedValues.map((value) => fadeIn(value, 500))
  );
};

/**
 * Shake animation (for errors)
 * @param {Animated.Value} animatedValue - The animated value to control
 */
export const shake = (animatedValue) => {
  return Animated.sequence([
    Animated.timing(animatedValue, {
      toValue: 10,
      duration: 50,
      useNativeDriver: true,
    }),
    Animated.timing(animatedValue, {
      toValue: -10,
      duration: 50,
      useNativeDriver: true,
    }),
    Animated.timing(animatedValue, {
      toValue: 10,
      duration: 50,
      useNativeDriver: true,
    }),
    Animated.timing(animatedValue, {
      toValue: 0,
      duration: 50,
      useNativeDriver: true,
    }),
  ]);
};

/**
 * Progress bar animation
 * @param {Animated.Value} animatedValue - The animated value to control
 * @param {number} toValue - Target progress (0-1)
 * @param {number} duration - Duration in milliseconds
 */
export const progressAnimation = (animatedValue, toValue, duration = 800) => {
  return Animated.timing(animatedValue, {
    toValue,
    duration,
    easing: Easing.out(Easing.cubic),
    useNativeDriver: false, // Progress bars need layout animations
  });
};

/**
 * Rotate animation (for loading spinners)
 * @param {Animated.Value} animatedValue - The animated value to control
 */
export const rotate = (animatedValue) => {
  return Animated.loop(
    Animated.timing(animatedValue, {
      toValue: 1,
      duration: 1000,
      easing: Easing.linear,
      useNativeDriver: true,
    })
  );
};

/**
 * Slide transition between screens
 * @param {Animated.Value} fadeValue - Fade animated value
 * @param {Animated.Value} slideValue - Slide animated value
 * @param {string} direction - 'left' or 'right'
 */
export const slideTransition = (fadeValue, slideValue, direction = 'left') => {
  const slideStart = direction === 'left' ? 50 : -50;
  
  slideValue.setValue(slideStart);
  fadeValue.setValue(0);

  return Animated.parallel([
    fadeIn(fadeValue, 400),
    Animated.timing(slideValue, {
      toValue: 0,
      duration: 400,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }),
  ]);
};

export default {
  fadeIn,
  fadeOut,
  slideInFromBottom,
  scaleAnimation,
  pulse,
  staggerFadeIn,
  shake,
  progressAnimation,
  rotate,
  slideTransition,
};
