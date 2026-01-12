import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Platform,
  Linking,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as Location from 'expo-location';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';
import { locationAPI } from '../services/api';

const LocationsScreen = () => {
  const [location, setLocation] = useState(null);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTypes, setSelectedTypes] = useState(['food_bank', 'soup_kitchen', 'shelter']);

  const locationTypes = [
    { id: 'food_bank', label: 'Food Banks', emoji: '🏪' },
    { id: 'soup_kitchen', label: 'Kitchens', emoji: '🍲' },
    { id: 'shelter', label: 'Shelters', emoji: '🏠' },
  ];

  useEffect(() => {
    getLocationAndSearch();
  }, []);

  const getLocationAndSearch = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Location permission is required to find nearby locations');
        setLoading(false);
        return;
      }

      const currentLocation = await Location.getCurrentPositionAsync({});
      setLocation(currentLocation.coords);

      const nearbyLocations = await locationAPI.searchLocations(
        currentLocation.coords.latitude,
        currentLocation.coords.longitude,
        5000,
        selectedTypes
      );

      setLocations(nearbyLocations);
    } catch (error) {
      console.error('Error getting location:', error);
      Alert.alert('Error', 'Failed to get your location. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleLocationType = (typeId) => {
    setSelectedTypes(prev => 
      prev.includes(typeId) 
        ? prev.filter(t => t !== typeId)
        : [...prev, typeId]
    );
  };

  const handleSearch = () => {
    if (location && selectedTypes.length > 0) {
      setLoading(true);
      getLocationAndSearch();
    }
  };

  const handleGetDirections = (loc) => {
    const url = Platform.select({
      ios: `maps:0,0?q=${loc.name}@${loc.latitude},${loc.longitude}`,
      android: `geo:0,0?q=${loc.latitude},${loc.longitude}(${loc.name})`,
    });
    Linking.openURL(url);
  };

  const handleSaveLocation = async (loc) => {
    try {
      await locationAPI.saveLocation(loc);
      Alert.alert('Saved! ✓', 'Location saved to your favorites');
    } catch (error) {
      Alert.alert('Error', 'Failed to save location');
    }
  };

  if (loading) {
    return (
      <LinearGradient colors={gradients.main} style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primaryDark} />
          <Text style={styles.loadingText}>Finding locations near you...</Text>
        </View>
      </LinearGradient>
    );
  }

  return (
    <LinearGradient colors={gradients.main} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Find Food</Text>
        <Text style={styles.headerSubtitle}>Nearby shelters, kitchens & food banks</Text>
      </View>

      {/* Filter Section */}
      <View style={styles.filterSection}>
        <Text style={styles.filterLabel}>Show me:</Text>
        <View style={styles.filterButtons}>
          {locationTypes.map((type) => {
            const isSelected = selectedTypes.includes(type.id);
            return (
              <TouchableOpacity
                key={type.id}
                style={[styles.filterChip, isSelected && styles.filterChipSelected]}
                onPress={() => toggleLocationType(type.id)}
                activeOpacity={0.7}
              >
                <LinearGradient
                  colors={isSelected ? gradients.button : [colors.white, colors.white]}
                  style={styles.filterChipGradient}
                >
                  <Text style={styles.filterEmoji}>{type.emoji}</Text>
                  <Text style={[styles.filterText, isSelected && styles.filterTextSelected]}>
                    {type.label}
                  </Text>
                </LinearGradient>
              </TouchableOpacity>
            );
          })}
        </View>

        <TouchableOpacity
          style={styles.searchButton}
          onPress={handleSearch}
          disabled={selectedTypes.length === 0}
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={selectedTypes.length > 0 ? gradients.button : [colors.gray200, colors.gray300]}
            style={styles.searchButtonGradient}
          >
            <Text style={[styles.searchButtonText, selectedTypes.length === 0 && styles.searchButtonTextDisabled]}>
              Search
            </Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>

      {/* Results */}
      <ScrollView
        style={styles.locationsList}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.listHeader}>
          <Text style={styles.listTitle}>
            {locations.length} {locations.length === 1 ? 'location' : 'locations'} found
          </Text>
        </View>

        {locations.map((loc, index) => (
          <View key={index} style={styles.locationCard}>
            <LinearGradient
              colors={[colors.white, colors.offWhite]}
              style={styles.locationGradient}
            >
              <View style={styles.locationContent}>
                <View style={styles.locationIconContainer}>
                  <Text style={styles.locationIcon}>
                    {loc.type === 'shelter' ? '🏠' : loc.type === 'soup_kitchen' ? '🍲' : '🏪'}
                  </Text>
                </View>

                <View style={styles.locationInfo}>
                  <Text style={styles.locationName}>{loc.name}</Text>
                  <Text style={styles.locationType}>
                    {loc.type.replace('_', ' ').toUpperCase()}
                  </Text>
                  {loc.address && (
                    <Text style={styles.locationAddress}>{loc.address}</Text>
                  )}
                  {loc.hours && (
                    <Text style={styles.locationHours}>⏰ {loc.hours}</Text>
                  )}
                  {loc.phone && (
                    <TouchableOpacity onPress={() => Linking.openURL(`tel:${loc.phone}`)}>
                      <Text style={styles.locationPhone}>📞 {loc.phone}</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>

              <View style={styles.locationActions}>
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => handleGetDirections(loc)}
                  activeOpacity={0.8}
                >
                  <LinearGradient
                    colors={gradients.button}
                    style={styles.actionButtonGradient}
                  >
                    <Text style={styles.actionButtonText}>Directions</Text>
                  </LinearGradient>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.saveIconButton}
                  onPress={() => handleSaveLocation(loc)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.saveIcon}>⭐</Text>
                </TouchableOpacity>
              </View>
            </LinearGradient>
          </View>
        ))}

        {locations.length === 0 && (
          <View style={styles.emptyState}>
            <Text style={styles.emptyEmoji}>📍</Text>
            <Text style={styles.emptyTitle}>No locations found nearby</Text>
            <Text style={styles.emptyText}>
              Try adjusting your filters or search radius
            </Text>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.lg,
  },
  loadingText: {
    fontSize: typography.base,
    color: colors.textLight,
    fontWeight: '600',
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
  filterSection: {
    paddingHorizontal: spacing['2xl'],
    marginBottom: spacing.lg,
  },
  filterLabel: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  filterButtons: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.base,
  },
  filterChip: {
    flex: 1,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.sm,
  },
  filterChipSelected: {
    ...shadows.md,
  },
  filterChipGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.sm,
    gap: spacing.xs,
  },
  filterEmoji: {
    fontSize: 20,
  },
  filterText: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.text,
  },
  filterTextSelected: {
    color: colors.white,
  },
  searchButton: {
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.md,
  },
  searchButtonGradient: {
    paddingVertical: spacing.base,
    alignItems: 'center',
  },
  searchButtonText: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.white,
    letterSpacing: 0.3,
  },
  searchButtonTextDisabled: {
    color: colors.textMuted,
  },
  locationsList: {
    flex: 1,
    paddingHorizontal: spacing['2xl'],
  },
  listHeader: {
    marginBottom: spacing.base,
  },
  listTitle: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.text,
  },
  locationCard: {
    marginBottom: spacing.base,
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.lg,
  },
  locationGradient: {
    padding: spacing.base,
  },
  locationContent: {
    flexDirection: 'row',
    marginBottom: spacing.base,
  },
  locationIconContainer: {
    width: 56,
    height: 56,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.base,
    ...shadows.sm,
  },
  locationIcon: {
    fontSize: 28,
  },
  locationInfo: {
    flex: 1,
    gap: spacing.xs,
  },
  locationName: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.text,
  },
  locationType: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.primaryDark,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  locationAddress: {
    fontSize: typography.sm,
    color: colors.textLight,
    lineHeight: typography.sm * 1.4,
  },
  locationHours: {
    fontSize: typography.sm,
    color: colors.textMuted,
  },
  locationPhone: {
    fontSize: typography.sm,
    color: colors.primaryDark,
    fontWeight: '600',
  },
  locationActions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  actionButton: {
    flex: 1,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
    ...shadows.sm,
  },
  actionButtonGradient: {
    paddingVertical: spacing.sm,
    alignItems: 'center',
  },
  actionButtonText: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.white,
  },
  saveIconButton: {
    width: 48,
    height: 48,
    borderRadius: borderRadius.md,
    backgroundColor: colors.white,
    justifyContent: 'center',
    alignItems: 'center',
    ...shadows.sm,
  },
  saveIcon: {
    fontSize: 24,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: spacing['5xl'],
  },
  emptyEmoji: {
    fontSize: 64,
    marginBottom: spacing.lg,
  },
  emptyTitle: {
    fontSize: typography.xl,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  emptyText: {
    fontSize: typography.base,
    color: colors.textLight,
    textAlign: 'center',
    lineHeight: typography.base * 1.5,
  },
  bottomSpacer: {
    height: spacing['2xl'],
  },
});

export default LocationsScreen;
