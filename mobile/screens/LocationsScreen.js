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
  RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { colors, gradients, shadows, typography, spacing, borderRadius } from '../theme/colors';
import { locationAPI } from '../services/api';

const LocationsScreen = () => {
  const [location, setLocation] = useState(null);
  const [locations, setLocations] = useState([]);
  const [savedLocations, setSavedLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTypes, setSelectedTypes] = useState(['food_bank', 'soup_kitchen', 'shelter']);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [showSaved, setShowSaved] = useState(false);

  const locationTypes = [
    { id: 'food_bank', label: 'Food Banks', icon: 'storefront-outline' },
    { id: 'soup_kitchen', label: 'Kitchens', icon: 'restaurant-outline' },
    { id: 'shelter', label: 'Shelters', icon: 'home-outline' },
  ];

  useEffect(() => {
    getLocationAndSearch();
    loadSavedLocations();
  }, []);

  const loadSavedLocations = async () => {
    try {
      const saved = await locationAPI.getSavedLocations();
      setSavedLocations(saved || []);
    } catch (error) {
      console.error('Error loading saved locations:', error);
    }
  };

  const getLocationAndSearch = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setPermissionDenied(true);
        setLoading(false);
        return;
      }
      setPermissionDenied(false);

      const currentLocation = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      setLocation(currentLocation.coords);

      await searchLocations(currentLocation.coords);
    } catch (error) {
      console.error('Error getting location:', error);
      Alert.alert(
        'Location Error',
        'Unable to get your location. Please check your location settings and try again.',
        [{ text: 'OK' }]
      );
      setLoading(false);
    }
  };

  const searchLocations = async (coords) => {
    try {
      const nearbyLocations = await locationAPI.searchLocations(
        coords.latitude,
        coords.longitude,
        10000, // 10km radius for better coverage
        selectedTypes
      );

      setLocations(nearbyLocations || []);

      // Show info message if we got fallback locations
      const hasFallback = nearbyLocations?.some(loc => loc.is_fallback);
      if (hasFallback && nearbyLocations.length > 0) {
        // Subtle notification that these are general resources
        console.log('Using community resources with fallback data');
      }
    } catch (apiError) {
      console.error('API Error:', apiError);
      Alert.alert(
        'Search Notice',
        'We found some community resources for you. For more specific local results, try calling 211.',
        [{ text: 'OK' }]
      );
      setLocations([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const toggleLocationType = (typeId) => {
    setSelectedTypes(prev =>
      prev.includes(typeId)
        ? prev.filter(t => t !== typeId)
        : [...prev, typeId]
    );
  };

  const handleSearch = async () => {
    if (location && selectedTypes.length > 0) {
      setLoading(true);
      await searchLocations(location);
    } else if (selectedTypes.length === 0) {
      Alert.alert('Select Type', 'Please select at least one location type');
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    if (location) {
      await searchLocations(location);
    } else {
      await getLocationAndSearch();
    }
    await loadSavedLocations();
  };

  const handleGetDirections = (loc) => {
    const scheme = Platform.select({ ios: 'maps:', android: 'geo:' });
    const url = Platform.select({
      ios: `maps:0,0?q=${encodeURIComponent(loc.name)}@${loc.latitude},${loc.longitude}`,
      android: `geo:0,0?q=${loc.latitude},${loc.longitude}(${encodeURIComponent(loc.name)})`,
    });
    Linking.openURL(url).catch(() => {
      // Fallback to Google Maps
      Linking.openURL(`https://www.google.com/maps/search/?api=1&query=${loc.latitude},${loc.longitude}`);
    });
  };

  const handleCall = (phone) => {
    if (phone) {
      Linking.openURL(`tel:${phone.replace(/\D/g, '')}`);
    }
  };

  const handleOpenWebsite = (website) => {
    if (website) {
      let url = website;
      if (!url.startsWith('http')) {
        url = 'https://' + url;
      }
      Linking.openURL(url);
    }
  };

  const handleSaveLocation = async (loc) => {
    try {
      await locationAPI.saveLocation(loc);
      Alert.alert('Saved!', 'Location saved to your favorites');
      loadSavedLocations();
    } catch (error) {
      Alert.alert('Error', 'Failed to save location');
    }
  };

  const handleDeleteSavedLocation = async (locationId) => {
    try {
      await locationAPI.deleteSavedLocation(locationId);
      Alert.alert('Removed', 'Location removed from favorites');
      loadSavedLocations();
    } catch (error) {
      Alert.alert('Error', 'Failed to remove location');
    }
  };

  const isLocationSaved = (locId) => {
    return savedLocations.some(saved =>
      saved.name === locId || saved.locationId === locId
    );
  };

  const getTypeIcon = (type) => {
    switch(type) {
      case 'shelter': return 'home';
      case 'soup_kitchen': return 'restaurant';
      case 'food_bank': return 'storefront';
      case 'community_center': return 'people';
      default: return 'heart';
    }
  };

  const getTypeColor = (type) => {
    switch(type) {
      case 'shelter': return '#8b5cf6';
      case 'soup_kitchen': return '#f59e0b';
      case 'food_bank': return '#10b981';
      case 'community_center': return '#3b82f6';
      default: return colors.primaryDark;
    }
  };

  const renderLocationCard = (loc, index, isSavedView = false) => (
    <View key={`${loc.id || loc.locationId}-${index}`} style={styles.locationCard}>
      <LinearGradient
        colors={[colors.white, colors.offWhite]}
        style={styles.locationGradient}
      >
        <View style={styles.locationContent}>
          <View style={[styles.locationIconContainer, { backgroundColor: `${getTypeColor(loc.type)}20` }]}>
            <Ionicons
              name={getTypeIcon(loc.type)}
              size={26}
              color={getTypeColor(loc.type)}
            />
          </View>

          <View style={styles.locationInfo}>
            <Text style={styles.locationName} numberOfLines={2}>{loc.name}</Text>
            <View style={styles.typeRow}>
              <View style={[styles.typeBadge, { backgroundColor: `${getTypeColor(loc.type)}20` }]}>
                <Text style={[styles.locationType, { color: getTypeColor(loc.type) }]}>
                  {(loc.type || '').replace(/_/g, ' ').toUpperCase()}
                </Text>
              </View>
              {loc.distance_km && (
                <Text style={styles.distanceText}>
                  {loc.distance_km < 1 ? `${Math.round(loc.distance_km * 1000)}m` : `${loc.distance_km}km`} away
                </Text>
              )}
            </View>
            {loc.address && loc.address !== 'Address not available' && (
              <Text style={styles.locationAddress} numberOfLines={2}>{loc.address}</Text>
            )}
            {loc.description && (
              <Text style={styles.locationDescription} numberOfLines={2}>{loc.description}</Text>
            )}
            {loc.hours && (
              <View style={styles.locationDetail}>
                <Ionicons name="time-outline" size={14} color={colors.textLight} />
                <Text style={styles.locationHours}>{loc.hours}</Text>
              </View>
            )}
            {loc.phone && (
              <TouchableOpacity style={styles.locationDetail} onPress={() => handleCall(loc.phone)}>
                <Ionicons name="call-outline" size={14} color={colors.primaryDark} />
                <Text style={styles.locationPhone}>{loc.phone}</Text>
              </TouchableOpacity>
            )}
            {loc.website && (
              <TouchableOpacity style={styles.locationDetail} onPress={() => handleOpenWebsite(loc.website)}>
                <Ionicons name="globe-outline" size={14} color={colors.info} />
                <Text style={styles.locationWebsite} numberOfLines={1}>Visit Website</Text>
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
              <Ionicons name="navigate" size={16} color={colors.white} />
              <Text style={styles.actionButtonText}>Directions</Text>
            </LinearGradient>
          </TouchableOpacity>

          {loc.phone && (
            <TouchableOpacity
              style={styles.callButton}
              onPress={() => handleCall(loc.phone)}
              activeOpacity={0.7}
            >
              <Ionicons name="call" size={18} color={colors.primaryDark} />
            </TouchableOpacity>
          )}

          {isSavedView ? (
            <TouchableOpacity
              style={styles.deleteButton}
              onPress={() => handleDeleteSavedLocation(loc.locationId)}
              activeOpacity={0.7}
            >
              <Ionicons name="trash-outline" size={18} color={colors.error} />
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[styles.saveIconButton, isLocationSaved(loc.name) && styles.savedButton]}
              onPress={() => handleSaveLocation(loc)}
              activeOpacity={0.7}
            >
              <Ionicons
                name={isLocationSaved(loc.name) ? "bookmark" : "bookmark-outline"}
                size={18}
                color={isLocationSaved(loc.name) ? colors.primaryDark : colors.textMuted}
              />
            </TouchableOpacity>
          )}
        </View>

        {loc.is_fallback && (
          <View style={styles.fallbackBanner}>
            <Ionicons name="information-circle" size={14} color={colors.info} />
            <Text style={styles.fallbackText}>Call to confirm availability</Text>
          </View>
        )}
      </LinearGradient>
    </View>
  );

  if (loading) {
    return (
      <LinearGradient colors={gradients.main} style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primaryDark} />
          <Text style={styles.loadingText}>Finding locations near you...</Text>
          <Text style={styles.loadingSubtext}>This may take a moment</Text>
        </View>
      </LinearGradient>
    );
  }

  if (permissionDenied) {
    return (
      <LinearGradient colors={gradients.main} style={styles.container}>
        <View style={styles.permissionContainer}>
          <View style={styles.permissionCard}>
            <LinearGradient
              colors={[colors.white, colors.offWhite]}
              style={styles.permissionGradient}
            >
              <View style={styles.permissionIconContainer}>
                <Ionicons name="location" size={40} color={colors.primaryDark} />
              </View>
              <Text style={styles.permissionTitle}>Location Access Needed</Text>
              <Text style={styles.permissionText}>
                To find nearby food banks, shelters, and kitchens, we need access to your location.
              </Text>
              <TouchableOpacity
                style={styles.permissionButton}
                onPress={getLocationAndSearch}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={gradients.button}
                  style={styles.permissionButtonGradient}
                >
                  <Text style={styles.permissionButtonText}>Allow Location</Text>
                </LinearGradient>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.openSettingsButton}
                onPress={() => Linking.openSettings()}
                activeOpacity={0.7}
              >
                <Text style={styles.openSettingsText}>Open Settings</Text>
              </TouchableOpacity>
            </LinearGradient>
          </View>
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

      {/* Tab Selector */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, !showSaved && styles.tabActive]}
          onPress={() => setShowSaved(false)}
        >
          <Text style={[styles.tabText, !showSaved && styles.tabTextActive]}>Nearby</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, showSaved && styles.tabActive]}
          onPress={() => setShowSaved(true)}
        >
          <Text style={[styles.tabText, showSaved && styles.tabTextActive]}>
            Saved ({savedLocations.length})
          </Text>
        </TouchableOpacity>
      </View>

      {!showSaved && (
        <>
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
                      <Ionicons
                        name={type.icon}
                        size={16}
                        color={isSelected ? colors.white : colors.text}
                      />
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
                <Ionicons name="search" size={18} color={selectedTypes.length > 0 ? colors.white : colors.textMuted} />
                <Text style={[styles.searchButtonText, selectedTypes.length === 0 && styles.searchButtonTextDisabled]}>
                  Search Area
                </Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </>
      )}

      {/* Results */}
      <ScrollView
        style={styles.locationsList}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.primaryDark}
          />
        }
      >
        {showSaved ? (
          <>
            <View style={styles.listHeader}>
              <Text style={styles.listTitle}>
                {savedLocations.length} saved {savedLocations.length === 1 ? 'location' : 'locations'}
              </Text>
            </View>

            {savedLocations.length === 0 ? (
              <View style={styles.emptyState}>
                <View style={styles.emptyIconContainer}>
                  <Ionicons name="bookmark-outline" size={48} color={colors.textMuted} />
                </View>
                <Text style={styles.emptyTitle}>No saved locations</Text>
                <Text style={styles.emptyText}>
                  Tap the bookmark icon on any location to save it for quick access
                </Text>
              </View>
            ) : (
              savedLocations.map((loc, index) => renderLocationCard(loc, index, true))
            )}
          </>
        ) : (
          <>
            <View style={styles.listHeader}>
              <Text style={styles.listTitle}>
                {locations.length} {locations.length === 1 ? 'location' : 'locations'} found
              </Text>
            </View>

            {locations.map((loc, index) => renderLocationCard(loc, index, false))}

            {locations.length === 0 && (
              <View style={styles.emptyState}>
                <View style={styles.emptyIconContainer}>
                  <Ionicons name="location-outline" size={48} color={colors.textMuted} />
                </View>
                <Text style={styles.emptyTitle}>No locations found nearby</Text>
                <Text style={styles.emptyText}>
                  Try adjusting your filters or increasing the search area. You can also call 211 for local resources.
                </Text>
                <TouchableOpacity
                  style={styles.call211Button}
                  onPress={() => handleCall('211')}
                  activeOpacity={0.8}
                >
                  <LinearGradient colors={gradients.button} style={styles.call211Gradient}>
                    <Ionicons name="call" size={18} color={colors.white} />
                    <Text style={styles.call211Text}>Call 211 for Help</Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            )}
          </>
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
    gap: spacing.sm,
  },
  loadingText: {
    fontSize: typography.base,
    color: colors.textLight,
    fontWeight: '600',
  },
  loadingSubtext: {
    fontSize: typography.sm,
    color: colors.textMuted,
  },
  header: {
    paddingHorizontal: spacing['2xl'],
    paddingTop: Platform.OS === 'ios' ? 70 : 50,
    paddingBottom: spacing.base,
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
  tabContainer: {
    flexDirection: 'row',
    marginHorizontal: spacing['2xl'],
    marginBottom: spacing.base,
    backgroundColor: colors.gray100,
    borderRadius: borderRadius.lg,
    padding: spacing.xs,
  },
  tab: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    borderRadius: borderRadius.md,
  },
  tabActive: {
    backgroundColor: colors.white,
    ...shadows.sm,
  },
  tabText: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.textMuted,
  },
  tabTextActive: {
    color: colors.primaryDark,
  },
  filterSection: {
    paddingHorizontal: spacing['2xl'],
    marginBottom: spacing.base,
  },
  filterLabel: {
    fontSize: typography.sm,
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
    paddingHorizontal: spacing.xs,
    gap: spacing.xs,
  },
  filterText: {
    fontSize: typography.xs,
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
    flexDirection: 'row',
    paddingVertical: spacing.base,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
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
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.base,
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
  typeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  typeBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
  },
  locationType: {
    fontSize: typography.xs,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  distanceText: {
    fontSize: typography.xs,
    color: colors.textMuted,
    fontWeight: '500',
  },
  locationAddress: {
    fontSize: typography.sm,
    color: colors.textLight,
    lineHeight: typography.sm * 1.4,
  },
  locationDescription: {
    fontSize: typography.sm,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  locationDetail: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
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
  locationWebsite: {
    fontSize: typography.sm,
    color: colors.info,
    fontWeight: '500',
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
    flexDirection: 'row',
    paddingVertical: spacing.sm,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
  },
  actionButtonText: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.white,
  },
  callButton: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
  },
  saveIconButton: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    backgroundColor: colors.white,
    justifyContent: 'center',
    alignItems: 'center',
    ...shadows.sm,
  },
  savedButton: {
    backgroundColor: colors.primaryLight,
  },
  deleteButton: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    backgroundColor: colors.errorLight,
    justifyContent: 'center',
    alignItems: 'center',
  },
  fallbackBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginTop: spacing.sm,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.gray100,
  },
  fallbackText: {
    fontSize: typography.xs,
    color: colors.info,
    fontStyle: 'italic',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: spacing['3xl'],
  },
  emptyIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.gray100,
    justifyContent: 'center',
    alignItems: 'center',
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
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.lg,
  },
  call211Button: {
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.md,
  },
  call211Gradient: {
    flexDirection: 'row',
    paddingVertical: spacing.base,
    paddingHorizontal: spacing.xl,
    alignItems: 'center',
    gap: spacing.sm,
  },
  call211Text: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.white,
  },
  bottomSpacer: {
    height: spacing['2xl'],
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: spacing['2xl'],
  },
  permissionCard: {
    width: '100%',
    borderRadius: borderRadius['2xl'],
    overflow: 'hidden',
    ...shadows.lg,
  },
  permissionGradient: {
    padding: spacing['2xl'],
    alignItems: 'center',
  },
  permissionIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  permissionTitle: {
    fontSize: typography['2xl'],
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.base,
    textAlign: 'center',
  },
  permissionText: {
    fontSize: typography.base,
    color: colors.textLight,
    textAlign: 'center',
    lineHeight: typography.base * 1.6,
    marginBottom: spacing.xl,
  },
  permissionButton: {
    width: '100%',
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    ...shadows.md,
    marginBottom: spacing.base,
  },
  permissionButtonGradient: {
    paddingVertical: spacing.lg,
    alignItems: 'center',
  },
  permissionButtonText: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.white,
  },
  openSettingsButton: {
    paddingVertical: spacing.base,
  },
  openSettingsText: {
    fontSize: typography.base,
    color: colors.primaryDark,
    fontWeight: '600',
  },
});

export default LocationsScreen;
