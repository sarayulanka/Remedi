import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  Animated,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';

const { width, height } = Dimensions.get('window');

// Confetti particle component
const ConfettiParticle = ({ delay, startX }) => {
  const translateY = useRef(new Animated.Value(-20)).current;
  const translateX = useRef(new Animated.Value(0)).current;
  const rotate = useRef(new Animated.Value(0)).current;
  const opacity = useRef(new Animated.Value(1)).current;

  const particleColors = [colors.gold, colors.goldLight, colors.primaryDark, colors.flame, '#ec4899'];
  const color = particleColors[Math.floor(Math.random() * particleColors.length)];
  const size = 6 + Math.random() * 6;

  useEffect(() => {
    const animation = Animated.sequence([
      Animated.delay(delay),
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: height * 0.6,
          duration: 2500 + Math.random() * 1000,
          useNativeDriver: true,
        }),
        Animated.timing(translateX, {
          toValue: (Math.random() - 0.5) * 100,
          duration: 2500,
          useNativeDriver: true,
        }),
        Animated.timing(rotate, {
          toValue: Math.random() * 4,
          duration: 2500,
          useNativeDriver: true,
        }),
        Animated.sequence([
          Animated.delay(1800),
          Animated.timing(opacity, {
            toValue: 0,
            duration: 700,
            useNativeDriver: true,
          }),
        ]),
      ]),
    ]);

    animation.start();

    // Cleanup: stop animation when component unmounts to prevent memory leaks
    return () => {
      animation.stop();
    };
  }, [delay, translateY, translateX, rotate, opacity]);

  return (
    <Animated.View
      style={[
        styles.confetti,
        {
          left: startX,
          width: size,
          height: size,
          backgroundColor: color,
          borderRadius: Math.random() > 0.5 ? size / 2 : 2,
          transform: [
            { translateY },
            { translateX },
            {
              rotate: rotate.interpolate({
                inputRange: [0, 4],
                outputRange: ['0deg', '1440deg'],
              }),
            },
          ],
          opacity,
        },
      ]}
    />
  );
};

const CelebrationModal = ({
  visible,
  onClose,
  type = 'milestone', // 'milestone', 'badge', 'freeze', 'streak'
  title,
  subtitle,
  xpEarned,
  icon,
  iconColor,
}) => {
  const scaleAnim = useRef(new Animated.Value(0)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.spring(scaleAnim, {
          toValue: 1,
          tension: 50,
          friction: 7,
          useNativeDriver: true,
        }),
        Animated.timing(opacityAnim, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      scaleAnim.setValue(0);
      opacityAnim.setValue(0);
    }
  }, [visible]);

  const getIconConfig = () => {
    switch (type) {
      case 'milestone':
        return { name: icon || 'trophy', color: iconColor || colors.gold };
      case 'badge':
        return { name: icon || 'ribbon', color: iconColor || colors.primaryDark };
      case 'freeze':
        return { name: 'shield-checkmark', color: colors.freeze };
      case 'streak':
        return { name: 'flame', color: colors.flame };
      default:
        return { name: 'star', color: colors.gold };
    }
  };

  const iconConfig = getIconConfig();

  // Generate confetti particles
  const confettiParticles = [];
  for (let i = 0; i < 30; i++) {
    confettiParticles.push(
      <ConfettiParticle
        key={i}
        delay={i * 50}
        startX={Math.random() * width}
      />
    );
  }

  return (
    <Modal
      visible={visible}
      transparent
      animationType="none"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        {/* Confetti */}
        {visible && confettiParticles}

        <Animated.View
          style={[
            styles.modalContainer,
            {
              transform: [{ scale: scaleAnim }],
              opacity: opacityAnim,
            },
          ]}
        >
          <LinearGradient
            colors={[colors.white, colors.primaryLight]}
            style={styles.modalContent}
          >
            {/* Icon */}
            <View style={[styles.iconContainer, { backgroundColor: `${iconConfig.color}15` }]}>
              <View style={[styles.iconInner, { backgroundColor: `${iconConfig.color}25` }]}>
                <Ionicons name={iconConfig.name} size={48} color={iconConfig.color} />
              </View>
            </View>

            {/* Title */}
            <Text style={styles.title}>{title || 'Achievement Unlocked!'}</Text>

            {/* Subtitle */}
            {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}

            {/* XP Badge */}
            {xpEarned && (
              <View style={styles.xpBadge}>
                <Ionicons name="star" size={16} color={colors.gold} />
                <Text style={styles.xpText}>+{xpEarned} XP</Text>
              </View>
            )}

            {/* Continue Button */}
            <TouchableOpacity
              style={styles.continueButton}
              onPress={onClose}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={gradients.button}
                style={styles.continueButtonGradient}
              >
                <Text style={styles.continueButtonText}>Continue</Text>
              </LinearGradient>
            </TouchableOpacity>
          </LinearGradient>
        </Animated.View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  confetti: {
    position: 'absolute',
    top: 0,
  },
  modalContainer: {
    width: width * 0.85,
    maxWidth: 340,
  },
  modalContent: {
    borderRadius: borderRadius['2xl'],
    padding: spacing['2xl'],
    alignItems: 'center',
    ...shadows.xl,
  },
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  iconInner: {
    width: 96,
    height: 96,
    borderRadius: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: typography['2xl'],
    fontWeight: '800',
    color: colors.text,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  subtitle: {
    fontSize: typography.base,
    color: colors.textLight,
    textAlign: 'center',
    marginBottom: spacing.lg,
    lineHeight: typography.base * 1.5,
  },
  xpBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.goldBg,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.full,
    marginBottom: spacing.xl,
    gap: spacing.xs,
  },
  xpText: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.goldDark,
  },
  continueButton: {
    width: '100%',
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.md,
  },
  continueButtonGradient: {
    paddingVertical: spacing.base,
    alignItems: 'center',
  },
  continueButtonText: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.white,
    letterSpacing: 0.3,
  },
});

export default CelebrationModal;
