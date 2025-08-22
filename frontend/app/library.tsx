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

type ViewMode = 'trades' | 'brands' | 'brand-detail' | 'category-detail' | 'product-detail';

interface NavigationState {
  mode: ViewMode;
  selectedTrade?: string;
  selectedBrand?: string;
  selectedCategory?: string;
  selectedProduct?: string;
}

const BACKEND_URL = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;

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

export default function LibraryScreen() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [knowledgeStats, setKnowledgeStats] = useState<KnowledgeStats | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  
  // Advanced filtering states
  const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedBuildingCodes, setSelectedBuildingCodes] = useState<string[]>([]);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  
  // Favorites functionality
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  
  // Load favorites from storage on mount
  useEffect(() => {
    loadFavorites();
  }, []);
  
  const loadFavorites = async () => {
    try {
      const { AsyncStorage } = await import('@react-native-async-storage/async-storage');
      const storedFavorites = await AsyncStorage.getItem('library_favorites');
      if (storedFavorites) {
        setFavorites(new Set(JSON.parse(storedFavorites)));
      }
    } catch (error) {
      console.error('Error loading favorites:', error);
    }
  };
  
  const toggleFavorite = async (productId: string) => {
    try {
      const newFavorites = new Set(favorites);
      if (newFavorites.has(productId)) {
        newFavorites.delete(productId);
      } else {
        newFavorites.add(productId);
      }
      
      setFavorites(newFavorites);
      
      // Save to AsyncStorage
      const { AsyncStorage } = await import('@react-native-async-storage/async-storage');
      await AsyncStorage.setItem('library_favorites', JSON.stringify([...newFavorites]));
    } catch (error) {
      console.error('Error saving favorite:', error);
    }
  };

  const filters = [
    { id: 'all', label: 'All', count: knowledgeStats?.total_documents || 0 },
    { id: 'favorites', label: 'Favorites', count: favorites.size },
    { id: 'nzbc', label: 'Building Code', count: knowledgeStats?.documents_by_type?.nzbc || 0 },
    { id: 'manufacturer', label: 'Manufacturers', count: knowledgeStats?.documents_by_type?.manufacturer || 0 },
    { id: 'nzs', label: 'NZ Standards', count: knowledgeStats?.documents_by_type?.nzs || 0 },
    { id: 'eboss_product', label: 'Products', count: knowledgeStats?.documents_by_type?.eboss_product || 0 },
  ];

  // Available filter options (these would be populated from backend)
  const availableBrands = [
    'VANTAGE', 'Altherm', 'James Hardie', 'Dimond', 'Resene', 'Kingspan', 
    'GIB', 'Pink Batts', 'FIRST Windows', 'Metalcraft', 'Brickworks'
  ];
  
  const availableCategories = [
    'Windows And Doors', 'Wall Cladding', 'Roofing And Decking', 'Insulation',
    'Glazing', 'Hardware', 'Structural', 'Fire Safety', 'HVAC', 'Plumbing'
  ];
  
  const availableBuildingCodes = [
    'G5', 'H1', 'E2', 'B1', 'F2', 'C1', 'G1', 'A1', 'D1', 'E1'
  ];

  // Load knowledge base stats on component mount
  useEffect(() => {
    loadKnowledgeStats();
  }, []);

  // Search when query changes
  useEffect(() => {
    if (searchQuery.length > 2) {
      performSearch();
    } else {
      setSearchResults([]);
    }
  }, [searchQuery, selectedFilter]);

  const loadKnowledgeStats = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/knowledge/stats`);
      if (response.ok) {
        const stats = await response.json();
        setKnowledgeStats(stats);
      }
    } catch (error) {
      console.error('Error loading knowledge stats:', error);
      Alert.alert('Error', 'Failed to load knowledge base statistics');
    } finally {
      setLoading(false);
    }
  };

  const performSearch = async () => {
    try {
      setSearching(true);
      const searchPayload = {
        query: searchQuery,
        document_types: selectedFilter === 'all' ? undefined : [selectedFilter],
        limit: 20,
        enable_query_processing: true
      };

      const response = await fetch(`${BACKEND_URL}/api/knowledge/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchPayload)
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.results || []);
      } else {
        throw new Error('Search request failed');
      }
    } catch (error) {
      console.error('Error performing search:', error);
      Alert.alert('Error', 'Failed to search knowledge base');
    } finally {
      setSearching(false);
    }
  };

  const convertSearchResultToCard = (result: SearchResult): ProductCard => {
    const { metadata } = result;
    
    // Clean up EBOSS product titles - remove redundant "EBOSS Product:" and "– EBOSS" parts
    let cleanTitle = metadata.section_title || result.title || 'Unknown Product';
    
    // Remove "EBOSS Product: " prefix
    cleanTitle = cleanTitle.replace(/^EBOSS Product:\s*/, '');
    
    // Extract title and brand - format: "Product Name by Brand – EBOSS - Brand"
    const titleMatch = cleanTitle.match(/^(.+?)\s+by\s+(.+?)\s+–\s+EBOSS/);
    
    let productTitle: string;
    let brand: string;
    
    if (titleMatch) {
      productTitle = titleMatch[1].trim();
      brand = titleMatch[2].trim();
    } else {
      // Fallback parsing for other formats
      productTitle = cleanTitle.split(' by ')[0] || cleanTitle;
      brand = metadata.manufacturer || 'Unknown Brand';
    }
    
    // Extract categories from tags (remove non-meaningful tags)
    const tagArray = metadata.tags?.split(',') || [];
    const categories = tagArray
      .map(tag => tag.trim())
      .filter(tag => 
        !['product', 'eboss', 'nz_building', 'document'].includes(tag.toLowerCase())
      );
    
    // Extract building codes and specifications from content
    const buildingCodes = extractBuildingCodes(result.content, metadata);
    const specifications = extractSpecifications(result.content);
    
    return {
      id: result.chunk_id,
      title: productTitle,
      brand: brand,
      category: categories[0]?.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'General',
      description: result.content.substring(0, 200) + '...',
      sourceUrl: metadata.source_url,
      tags: categories,
      buildingCodes,
      specifications,
      type: metadata.document_type as any,
      score: result.similarity_score,
    };
  };
  
  const extractSpecifications = (content: string): string[] => {
    const specs: string[] = [];
    
    // Extract R-values
    const rValues = content.match(/R[-\s]?(\d+\.?\d*)/gi);
    if (rValues) {
      specs.push(...rValues.map(rv => rv.toUpperCase()));
    }
    
    // Extract dimensions
    const dimensions = content.match(/\d+\s*(?:mm|m|kg|kW)\b/gi);
    if (dimensions) {
      specs.push(...dimensions.slice(0, 3));
    }
    
    // Extract performance ratings
    const ratings = content.match(/\b(?:IP\d+|Class\s+\w+|Grade\s+\w+)\b/gi);
    if (ratings) {
      specs.push(...ratings.slice(0, 2));
    }
    
    return [...new Set(specs)].slice(0, 4);
  };

  const formatTimeAgo = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return '1 day ago';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  };

  const getDisplayData = (): ProductCard[] => {
    if (searchQuery.length > 2) {
      return searchResults.map(result => convertSearchResultToCard(result));
    }
    
    if (selectedFilter === 'favorites' && favorites.size > 0) {
      // Show favorite products by searching for them
      // For now, return empty array - in a real app we'd store favorite metadata
      return [];
    }
    
    if (knowledgeStats?.recent_documents) {
      return knowledgeStats.recent_documents
        .filter(doc => selectedFilter === 'all' || doc.type === selectedFilter)
        .map(doc => ({
          id: doc.title,
          type: doc.type as any,
          title: doc.title,
          brand: extractBrandFromTitle(doc.title) || 'Unknown',
          category: getCategoryFromType(doc.type),
          description: 'Recent document from knowledge base',
          tags: extractBuildingCodes(doc.title, {}),
          buildingCodes: extractBuildingCodes(doc.title, {}),
          specifications: [],
          savedAt: formatTimeAgo(doc.processed_at)
        }));
    }
    
    return [];
  };

  const extractBrandFromTitle = (title: string): string | null => {
    // Extract brand from EBOSS product titles
    const ebossMatch = title.match(/by (.+?) – EBOSS/);
    if (ebossMatch) return ebossMatch[1];
    
    // Extract from other document types
    const brandMatch = title.match(/\b(James Hardie|GIB|Resene|Pink Batts|Kingspan|Dimond|VANTAGE|Altherm)\b/i);
    return brandMatch?.[1] || null;
  };

  const getCategoryFromType = (type: string): string => {
    const categoryMap = {
      'nzbc': 'Building Code',
      'manufacturer': 'Manufacturer Guide',
      'nzs': 'NZ Standard',
      'lbp': 'Licensed Building Practitioner',
      'eboss_product': 'Product'
    };
    return categoryMap[type as keyof typeof categoryMap] || 'General';
  };

  const openProductDetails = (product: ProductCard) => {
    // Navigate to chat with product-specific query
    const productQuery = `Tell me about ${product.brand} ${product.title} - specifications, installation requirements, and Building Code compliance`;
    
    router.push({
      pathname: '/chat',
      params: { message: productQuery }
    });
  };

  const extractBuildingCodes = (content: string, metadata: any): string[] => {
    const codes = [];
    
    // From metadata first
    if (metadata.building_codes) {
      codes.push(...metadata.building_codes);
    }
    
    // Extract from content
    const codeMatches = content.match(/\b([ABCDEFGH]\d+(?:\.\d+)*)\b/g);
    if (codeMatches) {
      codes.push(...codeMatches);
    }
    
    return [...new Set(codes)]; // Remove duplicates
  };

  const displayItems = getDisplayData();

  return (
    <View style={styles.container}>
      {/* Header with stats */}
      {knowledgeStats && (
        <View style={styles.statsHeader}>
          <Text style={styles.statsTitle}>Knowledge Base</Text>
          <Text style={styles.statsSubtitle}>
            {knowledgeStats.total_documents.toLocaleString()} documents • {knowledgeStats.total_chunks.toLocaleString()} sections
          </Text>
        </View>
      )}

      {/* Search bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <IconSymbol name="magnifyingglass" size={16} color={Colors.dark.icon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search Building Code, products, standards..."
            placeholderTextColor={Colors.dark.placeholder}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searching && <ActivityIndicator size="small" color={Colors.dark.tint} />}
        </View>
      </View>

      {/* Filter tabs */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        style={styles.filtersContainer}
        contentContainerStyle={styles.filtersContent}
      >
        {filters.map((filter) => (
          <TouchableOpacity
            key={filter.id}
            style={[
              styles.filterTab,
              selectedFilter === filter.id && styles.filterTabActive
            ]}
            onPress={() => setSelectedFilter(filter.id)}
          >
            <Text style={[
              styles.filterText,
              selectedFilter === filter.id && styles.filterTextActive
            ]}>
              {filter.label}
            </Text>
            {filter.count > 0 && (
              <View style={[
                styles.countBadge,
                selectedFilter === filter.id && styles.countBadgeActive
              ]}>
                <Text style={[
                  styles.countText,
                  selectedFilter === filter.id && styles.countTextActive
                ]}>
                  {filter.count > 999 ? '999+' : filter.count}
                </Text>
              </View>
            )}
          </TouchableOpacity>
        ))}
        
        {/* Advanced Filters Toggle */}
        <TouchableOpacity
          style={[
            styles.advancedFilterButton,
            showAdvancedFilters && styles.advancedFilterButtonActive
          ]}
          onPress={() => setShowAdvancedFilters(!showAdvancedFilters)}
        >
          <IconSymbol 
            name="slider.horizontal.3" 
            size={16} 
            color={showAdvancedFilters ? Colors.dark.background : Colors.dark.text} 
          />
          <Text style={[
            styles.advancedFilterText,
            showAdvancedFilters && styles.advancedFilterTextActive
          ]}>
            Filters
          </Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Advanced Filters Panel */}
      {showAdvancedFilters && (
        <View style={styles.advancedFiltersPanel}>
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            style={styles.advancedFiltersScroll}
          >
            <View style={styles.advancedFiltersContent}>
              {/* Brand Filters */}
              <View style={styles.filterSection}>
                <Text style={styles.filterSectionTitle}>Brands</Text>
                <View style={styles.filterChips}>
                  {availableBrands.map((brand) => (
                    <TouchableOpacity
                      key={brand}
                      style={[
                        styles.filterChip,
                        selectedBrands.includes(brand) && styles.filterChipActive
                      ]}
                      onPress={() => {
                        setSelectedBrands(prev => 
                          prev.includes(brand) 
                            ? prev.filter(b => b !== brand)
                            : [...prev, brand]
                        );
                      }}
                    >
                      <Text style={[
                        styles.filterChipText,
                        selectedBrands.includes(brand) && styles.filterChipTextActive
                      ]}>
                        {brand}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {/* Category Filters */}
              <View style={styles.filterSection}>
                <Text style={styles.filterSectionTitle}>Categories</Text>
                <View style={styles.filterChips}>
                  {availableCategories.map((category) => (
                    <TouchableOpacity
                      key={category}
                      style={[
                        styles.filterChip,
                        selectedCategories.includes(category) && styles.filterChipActive
                      ]}
                      onPress={() => {
                        setSelectedCategories(prev => 
                          prev.includes(category) 
                            ? prev.filter(c => c !== category)
                            : [...prev, category]
                        );
                      }}
                    >
                      <Text style={[
                        styles.filterChipText,
                        selectedCategories.includes(category) && styles.filterChipTextActive
                      ]}>
                        {category}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {/* Building Code Filters */}
              <View style={styles.filterSection}>
                <Text style={styles.filterSectionTitle}>Building Codes</Text>
                <View style={styles.filterChips}>
                  {availableBuildingCodes.map((code) => (
                    <TouchableOpacity
                      key={code}
                      style={[
                        styles.filterChip,
                        selectedBuildingCodes.includes(code) && styles.filterChipActive,
                        { backgroundColor: (buildingCodeColors[code] || buildingCodeColors.default) + '20' }
                      ]}
                      onPress={() => {
                        setSelectedBuildingCodes(prev => 
                          prev.includes(code) 
                            ? prev.filter(c => c !== code)
                            : [...prev, code]
                        );
                      }}
                    >
                      <Text style={[
                        styles.filterChipText,
                        selectedBuildingCodes.includes(code) && styles.filterChipTextActive,
                        { color: buildingCodeColors[code] || buildingCodeColors.default }
                      ]}>
                        {code}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {/* Clear Filters */}
              {(selectedBrands.length > 0 || selectedCategories.length > 0 || selectedBuildingCodes.length > 0) && (
                <TouchableOpacity
                  style={styles.clearFiltersButton}
                  onPress={() => {
                    setSelectedBrands([]);
                    setSelectedCategories([]);
                    setSelectedBuildingCodes([]);
                  }}
                >
                  <IconSymbol name="xmark.circle.fill" size={16} color={Colors.dark.icon} />
                  <Text style={styles.clearFiltersText}>Clear All Filters</Text>
                </TouchableOpacity>
              )}
            </View>
          </ScrollView>
        </View>
      )}

      {/* Loading state */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.dark.tint} />
          <Text style={styles.loadingText}>Loading knowledge base...</Text>
        </View>
      )}

      {/* Library items */}
      <ScrollView style={styles.libraryList}>
        {displayItems.map((item, index) => (
          <TouchableOpacity 
            key={`${item.id}-${index}`} 
            style={styles.productCard}
            onPress={() => openProductDetails(item)}
            activeOpacity={0.7}
          >
            <View style={styles.productHeader}>
              <View style={styles.productTitleContainer}>
                <Text style={styles.productTitle} numberOfLines={2}>{item.title}</Text>
                <View style={styles.productBrandContainer}>
                  <IconSymbol 
                    name={typeIcons[item.type] || typeIcons.nzbc} 
                    size={16} 
                    color={Colors.dark.tint} 
                  />
                  <Text style={styles.productBrand}>{item.brand}</Text>
                </View>
              </View>
              <View style={styles.productActions}>
                {/* Favorite Button */}
                <TouchableOpacity
                  style={styles.favoriteButton}
                  onPress={() => toggleFavorite(item.id)}
                  activeOpacity={0.7}
                >
                  <IconSymbol 
                    name={favorites.has(item.id) ? "heart.fill" : "heart"} 
                    size={20} 
                    color={favorites.has(item.id) ? '#FF6B6B' : Colors.dark.icon} 
                  />
                </TouchableOpacity>
                {item.score && (
                  <View style={styles.scoreBadge}>
                    <Text style={styles.scoreText}>
                      {Math.round(Math.abs(item.score) * 100)}%
                    </Text>
                  </View>
                )}
              </View>
            </View>
            
            <Text style={styles.productCategory}>{item.category}</Text>
            
            {item.description && (
              <Text style={styles.productDescription} numberOfLines={3}>
                {item.description}
              </Text>
            )}
            
            {/* Specifications */}
            {item.specifications && item.specifications.length > 0 && (
              <View style={styles.specificationsContainer}>
                <Text style={styles.specificationsTitle}>Specifications</Text>
                <View style={styles.specificationsList}>
                  {item.specifications.slice(0, 3).map((spec, specIndex) => (
                    <View key={specIndex} style={styles.specificationChip}>
                      <Text style={styles.specificationText}>{spec}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
            
            <View style={styles.productFooter}>
              <View style={styles.tags}>
                {item.buildingCodes.slice(0, 3).map((tag, tagIndex) => {
                  const codeColor = buildingCodeColors[tag] || buildingCodeColors.default;
                  return (
                    <View key={`${tag}-${tagIndex}`} style={[styles.tag, { backgroundColor: codeColor + '20' }]}>
                      <Text style={[styles.tagText, { color: codeColor }]}>{tag}</Text>
                    </View>
                  );
                })}
                {item.tags.slice(0, 2).map((tag, tagIndex) => (
                  <View key={`category-${tag}-${tagIndex}`} style={styles.categoryTag}>
                    <Text style={styles.categoryTagText}>
                      {tag.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Text>
                  </View>
                ))}
                {(item.buildingCodes.length + item.tags.length) > 5 && (
                  <Text style={styles.moreTagsText}>
                    +{(item.buildingCodes.length + item.tags.length) - 5} more
                  </Text>
                )}
              </View>
              <View style={styles.productActions}>
                {item.savedAt && (
                  <Text style={styles.savedAt}>{item.savedAt}</Text>
                )}
                <IconSymbol name="chevron.right" size={16} color={Colors.dark.icon} />
              </View>
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Empty state */}
      {!loading && displayItems.length === 0 && (
        <View style={styles.emptyState}>
          <IconSymbol 
            name={searchQuery ? "magnifyingglass" : "books.vertical.fill"} 
            size={48} 
            color={Colors.dark.icon} 
          />
          <Text style={styles.emptyTitle}>
            {searchQuery ? 'No matches found' : 'Select a category above'}
          </Text>
          <Text style={styles.emptySubtitle}>
            {searchQuery 
              ? `No documents found for "${searchQuery}". Try different search terms.`
              : 'Browse the complete NZ Building Code, manufacturer specs, and product database'
            }
          </Text>
        </View>
      )}
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