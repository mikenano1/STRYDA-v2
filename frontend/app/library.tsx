import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  Image,
} from 'react-native';
import { Colors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';
import Constants from 'expo-constants';
import { useRouter } from 'expo-router';

// Types for the hierarchical product system
interface Brand {
  id: string;
  name: string;
  logo?: string;
  productCount: number;
  categories: string[];
}

interface ProductCategory {
  id: string;
  name: string;
  icon: string;
  productCount: number;
  subcategories?: string[];
}

interface Trade {
  id: string;
  name: string;
  icon: string;
  color: string;
  brands: string[];
}

interface ProductDetails {
  id: string;
  name: string;
  brand: string;
  category: string;
  subcategory?: string;
  specifications: Record<string, string>;
  installGuides: string[];
  warranties: string[];
  complianceCodes: string[];
  images: string[];
  description: string;
}

// Additional types for search functionality
interface KnowledgeStats {
  total_documents: number;
  total_chunks: number;
  documents_by_type: {
    nzbc?: number;
    manufacturer?: number;
    nzs?: number;
    lbp?: number;
    eboss_product?: number;
  };
  recent_documents: Array<{
    title: string;
    type: string;
    processed_at: string;
  }>;
}

interface SearchResult {
  chunk_id: string;
  title: string;
  content: string;
  similarity_score: number;
  metadata: {
    section_title?: string;
    manufacturer?: string;
    tags?: string;
    source_url?: string;
    document_type: string;
    building_codes?: string[];
  };
}

interface ProductCard {
  id: string;
  title: string;
  brand: string;
  category: string;
  description?: string;
  sourceUrl?: string;
  tags: string[];
  buildingCodes: string[];
  specifications: string[];
  type: string;
  score?: number;
  savedAt?: string;
}

type ViewMode = 'trades' | 'brands' | 'brand-detail' | 'category-detail' | 'product-detail';

interface NavigationState {
  mode: ViewMode;
  selectedTrade?: string;
  selectedBrand?: string;
  selectedCategory?: string;
  selectedProduct?: string;
}

const BACKEND_URL = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;

// Type icons mapping
const typeIcons = {
  nzbc: 'doc.text.fill',
  manufacturer: 'building.2.fill',
  nzs: 'checkmark.seal.fill',
  lbp: 'person.badge.shield.checkmark.fill',
  eboss_product: 'cube.box.fill',
};

// Building code color mapping
const buildingCodeColors = {
  G5: '#10B981', // Green
  H1: '#F59E0B', // Amber
  E2: '#3B82F6', // Blue
  B1: '#EF4444', // Red
  F2: '#8B5CF6', // Purple
  C1: '#06B6D4', // Cyan
  G1: '#84CC16', // Lime
  A1: '#F97316', // Orange
  D1: '#EC4899', // Pink
  E1: '#6366F1', // Indigo
  default: '#6B7280', // Gray
};

// Trade categories for filtering
const TRADES: Trade[] = [
  { id: 'all', name: 'All Products', icon: 'square.grid.2x2', color: '#6B7280', brands: [] },
  { id: 'carpentry', name: 'Carpentry', icon: 'hammer.fill', color: '#8B4513', brands: ['James Hardie', 'Carter Holt Harvey'] },
  { id: 'roofing', name: 'Roofing', icon: 'house.fill', color: '#DC2626', brands: ['Dimond', 'Metalcraft', 'Nuralite'] },
  { id: 'plumbing', name: 'Plumbing', icon: 'drop.fill', color: '#2563EB', brands: ['Rehau', 'Metabronze'] },
  { id: 'electrical', name: 'Electrical', icon: 'bolt.fill', color: '#F59E0B', brands: ['Schneider Electric', 'ABB'] },
  { id: 'drainlayer', name: 'Drainage', icon: 'water.waves', color: '#059669', brands: ['Marley', 'Iplex'] },
  { id: 'painting', name: 'Painting', icon: 'paintbrush.fill', color: '#7C3AED', brands: ['Resene', 'Dulux'] },
  { id: 'plastering', name: 'Plastering', icon: 'rectangle.fill', color: '#EC4899', brands: ['GIB', 'Winstone Wallboards'] },
  { id: 'glazing', name: 'Glazing', icon: 'rectangle.portrait', color: '#06B6D4', brands: ['Viridian', 'Metro Glass'] },
  { id: 'insulation', name: 'Insulation', icon: 'shield.fill', color: '#10B981', brands: ['Pink Batts', 'Kingspan'] },
];

// Product type categories
const PRODUCT_TYPES: ProductCategory[] = [
  { id: 'structural', name: 'Structural', icon: 'building.2.fill', productCount: 0 },
  { id: 'cladding', name: 'Cladding', icon: 'rectangle.stack.fill', productCount: 0 },
  { id: 'roofing', name: 'Roofing', icon: 'house.fill', productCount: 0 },
  { id: 'interior', name: 'Interior', icon: 'door.left.hand.closed', productCount: 0 },
  { id: 'exterior', name: 'Exterior', icon: 'house', productCount: 0 },
  { id: 'windows-doors', name: 'Windows & Doors', icon: 'rectangle.portrait.and.arrow.right', productCount: 0 },
  { id: 'hardware', name: 'Hardware', icon: 'wrench.and.screwdriver.fill', productCount: 0 },
  { id: 'insulation', name: 'Insulation', icon: 'shield.fill', productCount: 0 },
];

// Mock brand data - in real app this would come from backend
const SAMPLE_BRANDS: Brand[] = [
  {
    id: 'james-hardie',
    name: 'James Hardie',
    productCount: 11,
    categories: ['Cladding', 'Eaves/Soffits', 'Flooring', 'Pre-Clad', 'Interior'],
  },
  {
    id: 'dimond',
    name: 'Dimond',
    productCount: 32,
    categories: ['Roofing', 'Wall Cladding', 'Spouting', 'Accessories'],
  },
  {
    id: 'vantage',
    name: 'VANTAGE',
    productCount: 62,
    categories: ['Windows', 'Doors', 'Hardware', 'Accessories'],
  },
  {
    id: 'altherm',
    name: 'Altherm',
    productCount: 51,
    categories: ['Windows', 'Sliding Doors', 'Hinged Doors', 'Hardware'],
  },
  {
    id: 'resene',
    name: 'Resene',
    productCount: 29,
    categories: ['Interior Paint', 'Exterior Paint', 'Primers', 'Specialty Coatings'],
  },
  {
    id: 'kingspan',
    name: 'Kingspan',
    productCount: 14,
    categories: ['Wall Insulation', 'Roof Insulation', 'Underfloor', 'Specialty'],
  },
];

export default function LibraryScreen() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [navigation, setNavigation] = useState<NavigationState>({ mode: 'trades' });
  const [selectedFilterType, setSelectedFilterType] = useState<'trades' | 'types'>('trades');
  const [brands, setBrands] = useState<Brand[]>(SAMPLE_BRANDS);

  const navigateTo = (newNavigation: NavigationState) => {
    setNavigation(newNavigation);
  };

  const getBreadcrumbs = (): string[] => {
    const crumbs = ['Products'];
    
    if (navigation.selectedTrade && navigation.selectedTrade !== 'all') {
      const trade = TRADES.find(t => t.id === navigation.selectedTrade);
      if (trade) crumbs.push(trade.name);
    }
    
    if (navigation.selectedBrand) {
      const brand = brands.find(b => b.id === navigation.selectedBrand);
      if (brand) crumbs.push(brand.name);
    }
    
    if (navigation.selectedCategory) {
      crumbs.push(navigation.selectedCategory);
    }
    
    return crumbs;
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <View style={styles.titleContainer}>
        <Text style={styles.title}>Products</Text>
        <Text style={styles.subtitle}>
          {brands.reduce((sum, brand) => sum + brand.productCount, 0)} NZ building products
        </Text>
      </View>

      {/* Breadcrumbs */}
      {navigation.mode !== 'trades' && (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.breadcrumbs}>
          {getBreadcrumbs().map((crumb, index) => (
            <View key={index} style={styles.breadcrumbContainer}>
              {index > 0 && <Text style={styles.breadcrumbSeparator}>›</Text>}
              <TouchableOpacity
                onPress={() => {
                  if (index === 0) navigateTo({ mode: 'trades' });
                  // Add more navigation logic for other breadcrumb levels
                }}
              >
                <Text style={[
                  styles.breadcrumbText,
                  index === getBreadcrumbs().length - 1 && styles.breadcrumbTextActive
                ]}>
                  {crumb}
                </Text>
              </TouchableOpacity>
            </View>
          ))}
        </ScrollView>
      )}

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <IconSymbol name="magnifyingglass" size={16} color={Colors.dark.icon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search brands or products..."
            placeholderTextColor={Colors.dark.placeholder}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>
      </View>
    </View>
  );

  const renderTradesView = () => (
    <View style={styles.content}>
      {/* Filter Type Toggle */}
      <View style={styles.filterToggle}>
        <TouchableOpacity
          style={[styles.filterToggleButton, selectedFilterType === 'trades' && styles.filterToggleButtonActive]}
          onPress={() => setSelectedFilterType('trades')}
        >
          <Text style={[styles.filterToggleText, selectedFilterType === 'trades' && styles.filterToggleTextActive]}>
            By Trade
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterToggleButton, selectedFilterType === 'types' && styles.filterToggleButtonActive]}
          onPress={() => setSelectedFilterType('types')}
        >
          <Text style={[styles.filterToggleText, selectedFilterType === 'types' && styles.filterToggleTextActive]}>
            By Product Type
          </Text>
        </TouchableOpacity>
      </View>

      {/* Categories Grid */}
      <ScrollView style={styles.categoriesContainer} showsVerticalScrollIndicator={false}>
        <View style={styles.categoriesGrid}>
          {(selectedFilterType === 'trades' ? TRADES : PRODUCT_TYPES).map((category) => (
            <TouchableOpacity
              key={category.id}
              style={[styles.categoryCard, { borderLeftColor: 'color' in category ? category.color : Colors.dark.tint }]}
              onPress={() => {
                if (selectedFilterType === 'trades') {
                  navigateTo({ 
                    mode: 'brands', 
                    selectedTrade: category.id 
                  });
                } else {
                  navigateTo({ 
                    mode: 'brands', 
                    selectedCategory: category.id 
                  });
                }
              }}
            >
              <View style={styles.categoryIconContainer}>
                <IconSymbol 
                  name={category.icon} 
                  size={32} 
                  color={'color' in category ? category.color : Colors.dark.tint} 
                />
              </View>
              <Text style={styles.categoryName}>{category.name}</Text>
              {'productCount' in category && (
                <Text style={styles.categoryCount}>{category.productCount} products</Text>
              )}
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );

  const renderBrandsView = () => {
    // Filter brands based on selected trade or category
    let filteredBrands = brands;
    
    if (navigation.selectedTrade && navigation.selectedTrade !== 'all') {
      const selectedTrade = TRADES.find(t => t.id === navigation.selectedTrade);
      if (selectedTrade?.brands.length > 0) {
        filteredBrands = brands.filter(brand => 
          selectedTrade.brands.some(tradeBrand => 
            brand.name.toLowerCase().includes(tradeBrand.toLowerCase())
          )
        );
      }
    }

    // Sort alphabetically
    filteredBrands.sort((a, b) => a.name.localeCompare(b.name));

    return (
      <View style={styles.content}>
        <ScrollView style={styles.brandsContainer} showsVerticalScrollIndicator={false}>
          <View style={styles.brandsGrid}>
            {filteredBrands.map((brand) => (
              <TouchableOpacity
                key={brand.id}
                style={styles.brandCard}
                onPress={() => navigateTo({ 
                  ...navigation,
                  mode: 'brand-detail', 
                  selectedBrand: brand.id 
                })}
              >
                <View style={styles.brandLogoContainer}>
                  {/* Placeholder for brand logo */}
                  <View style={styles.brandLogoPlaceholder}>
                    <Text style={styles.brandLogoText}>
                      {brand.name.split(' ').map(word => word[0]).join('').toUpperCase()}
                    </Text>
                  </View>
                </View>
                <View style={styles.brandInfo}>
                  <Text style={styles.brandName}>{brand.name}</Text>
                  <Text style={styles.brandProductCount}>
                    {brand.productCount} products
                  </Text>
                  <View style={styles.brandCategories}>
                    {brand.categories.slice(0, 2).map((category, index) => (
                      <View key={index} style={styles.categoryChip}>
                        <Text style={styles.categoryChipText}>{category}</Text>
                      </View>
                    ))}
                    {brand.categories.length > 2 && (
                      <Text style={styles.moreCategoriesText}>
                        +{brand.categories.length - 2} more
                      </Text>
                    )}
                  </View>
                </View>
                <IconSymbol name="chevron.right" size={20} color={Colors.dark.icon} />
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </View>
    );
  };

  const renderBrandDetailView = () => {
    const selectedBrand = brands.find(b => b.id === navigation.selectedBrand);
    if (!selectedBrand) return null;

    return (
      <View style={styles.content}>
        {/* Brand Header */}
        <View style={styles.brandHeader}>
          <View style={styles.brandHeaderLogo}>
            <View style={styles.brandLogoPlaceholder}>
              <Text style={styles.brandLogoText}>
                {selectedBrand.name.split(' ').map(word => word[0]).join('').toUpperCase()}
              </Text>
            </View>
          </View>
          <View style={styles.brandHeaderInfo}>
            <Text style={styles.brandHeaderName}>{selectedBrand.name}</Text>
            <Text style={styles.brandHeaderCount}>
              {selectedBrand.productCount} products in {selectedBrand.categories.length} categories
            </Text>
          </View>
        </View>

        {/* Product Categories */}
        <ScrollView style={styles.brandCategoriesContainer} showsVerticalScrollIndicator={false}>
          <Text style={styles.sectionTitle}>Product Categories</Text>
          {selectedBrand.categories.map((category, index) => (
            <TouchableOpacity
              key={index}
              style={styles.productCategoryCard}
              onPress={() => navigateTo({
                ...navigation,
                mode: 'category-detail',
                selectedCategory: category
              })}
            >
              <View style={styles.categoryIconContainer}>
                <IconSymbol 
                  name="folder.fill" 
                  size={24} 
                  color={Colors.dark.tint} 
                />
              </View>
              <View style={styles.categoryInfo}>
                <Text style={styles.categoryTitle}>{category}</Text>
                <Text style={styles.categorySubtitle}>
                  View all {selectedBrand.name} {category.toLowerCase()} products
                </Text>
              </View>
              <IconSymbol name="chevron.right" size={20} color={Colors.dark.icon} />
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {renderHeader()}
      
      {navigation.mode === 'trades' && renderTradesView()}
      {navigation.mode === 'brands' && renderBrandsView()}
      {navigation.mode === 'brand-detail' && renderBrandDetailView()}
      
      {/* TODO: Add category-detail and product-detail views */}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.dark.background,
  },
  statsHeader: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 8,
  },
  statsTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.dark.text,
    marginBottom: 4,
  },
  statsSubtitle: {
    fontSize: 14,
    color: Colors.dark.icon,
  },
  searchContainer: {
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 12,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.dark.inputBackground,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: Colors.dark.text,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
  },
  loadingText: {
    fontSize: 16,
    color: Colors.dark.icon,
    marginTop: 16,
  },
  filtersContainer: {
    paddingLeft: 20,
    marginBottom: 20,
  },
  filtersContent: {
    paddingRight: 20,
    gap: 8,
  },
  filterTab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: Colors.dark.surface,
    borderWidth: 1,
    borderColor: Colors.dark.border,
    gap: 6,
  },
  filterTabActive: {
    backgroundColor: Colors.dark.tint,
    borderColor: Colors.dark.tint,
  },
  filterText: {
    fontSize: 14,
    color: Colors.dark.text,
    fontWeight: '500',
  },
  filterTextActive: {
    color: Colors.dark.background,
  },
  countBadge: {
    backgroundColor: Colors.dark.inputBackground,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    minWidth: 20,
    alignItems: 'center',
  },
  countBadgeActive: {
    backgroundColor: Colors.dark.background + '40',
  },
  countText: {
    fontSize: 11,
    color: Colors.dark.text,
    fontWeight: '600',
  },
  countTextActive: {
    color: Colors.dark.background,
  },
  advancedFilterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: Colors.dark.surface,
    borderWidth: 1,
    borderColor: Colors.dark.border,
    gap: 6,
  },
  advancedFilterButtonActive: {
    backgroundColor: Colors.dark.tint,
    borderColor: Colors.dark.tint,
  },
  advancedFilterText: {
    fontSize: 14,
    color: Colors.dark.text,
    fontWeight: '500',
  },
  advancedFilterTextActive: {
    color: Colors.dark.background,
  },
  advancedFiltersPanel: {
    backgroundColor: Colors.dark.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.dark.border,
    paddingVertical: 16,
  },
  advancedFiltersScroll: {
    paddingLeft: 20,
  },
  advancedFiltersContent: {
    flexDirection: 'row',
    gap: 24,
    paddingRight: 20,
  },
  filterSection: {
    minWidth: 200,
  },
  filterSectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.dark.text,
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  filterChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    backgroundColor: Colors.dark.inputBackground,
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  filterChipActive: {
    backgroundColor: Colors.dark.tint,
    borderColor: Colors.dark.tint,
  },
  filterChipText: {
    fontSize: 12,
    color: Colors.dark.text,
    fontWeight: '500',
  },
  filterChipTextActive: {
    color: Colors.dark.background,
    fontWeight: '600',
  },
  clearFiltersButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: Colors.dark.inputBackground,
    borderWidth: 1,
    borderColor: Colors.dark.border,
    alignSelf: 'flex-start',
  },
  clearFiltersText: {
    fontSize: 12,
    color: Colors.dark.icon,
    fontWeight: '500',
  },
  libraryList: {
    flex: 1,
    paddingHorizontal: 20,
  },
  productCard: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.dark.border,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  productHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  productTitleContainer: {
    flex: 1,
    marginRight: 12,
  },
  productTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.dark.text,
    lineHeight: 24,
    marginBottom: 8,
  },
  productBrandContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  productBrand: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.dark.tint,
  },
  productCategory: {
    fontSize: 12,
    color: Colors.dark.icon,
    textTransform: 'uppercase',
    fontWeight: '500',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  productDescription: {
    fontSize: 14,
    color: Colors.dark.text,
    lineHeight: 20,
    marginBottom: 16,
  },
  specificationsContainer: {
    marginBottom: 16,
  },
  specificationsTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.dark.text,
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  specificationsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  specificationChip: {
    backgroundColor: Colors.dark.tint + '15',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.dark.tint + '30',
  },
  specificationText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.dark.tint,
  },
  productFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  productActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  favoriteButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.dark.inputBackground,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  categoryTag: {
    backgroundColor: Colors.dark.inputBackground,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  categoryTagText: {
    fontSize: 11,
    color: Colors.dark.text,
    fontWeight: '500',
  },
  // Legacy styles for compatibility
  libraryItem: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  itemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  itemTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.text,
    flex: 1,
    lineHeight: 22,
  },
  scoreBadge: {
    backgroundColor: Colors.dark.tint + '20',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  scoreText: {
    fontSize: 12,
    color: Colors.dark.tint,
    fontWeight: '600',
  },
  itemSnippet: {
    fontSize: 14,
    color: Colors.dark.icon,
    lineHeight: 20,
    marginBottom: 12,
  },
  itemFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    flex: 1,
    marginRight: 12,
  },
  tag: {
    backgroundColor: Colors.dark.surfaceSecondary,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  tagText: {
    fontSize: 12,
    color: Colors.dark.text,
    fontWeight: '500',
  },
  moreTagsText: {
    fontSize: 12,
    color: Colors.dark.placeholder,
    fontStyle: 'italic',
  },
  savedAt: {
    fontSize: 12,
    color: Colors.dark.placeholder,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.dark.text,
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: Colors.dark.icon,
    textAlign: 'center',
    lineHeight: 20,
  },
});