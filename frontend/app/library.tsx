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
} from 'react-native';
import { Colors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';
import Constants from 'expo-constants';

// Types for our knowledge base
interface KnowledgeDocument {
  title: string;
  type: string;
  processed_at: string;
  snippet?: string;
  tags?: string[];
}

interface KnowledgeStats {
  total_documents: number;
  total_chunks: number;
  documents_by_type: Record<string, number>;
  recent_documents: KnowledgeDocument[];
}

interface SearchResult {
  title: string;
  content: string;
  similarity_score: number;
  metadata: {
    document_type: string;
    section_title?: string;
    building_codes?: string[];
    source_url?: string;
    manufacturer?: string;
    category?: string;
    tags?: string;
  };
  chunk_id: string;
}

interface ProductCard {
  id: string;
  title: string;
  brand: string;
  category: string;
  description: string;
  sourceUrl?: string;
  tags: string[];
  buildingCodes: string[];
  specifications?: string[];
  type: 'nzbc' | 'manufacturer' | 'nzs' | 'eboss_product' | 'lbp';
  imageUrl?: string;
  savedAt?: string;
  score?: number;
}

const BACKEND_URL = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;

const typeIcons = {
  nzbc: 'doc.text.fill',
  manufacturer: 'building.2.fill',
  nzs: 'book.closed.fill',
  lbp: 'checkmark.seal.fill',
  eboss_product: 'cube.box.fill',
};

const buildingCodeColors = {
  'G5': '#FF6B6B', // Fire safety - red
  'H1': '#4ECDC4', // Energy - teal  
  'E2': '#45B7D1', // Weathertightness - blue
  'B1': '#96CEB4', // Structure - green
  'F2': '#FECA57', // Fire materials - yellow
  'C1': '#FF9FF3', // Fire - pink
  'G1': '#DDA0DD', // Water - purple
  'default': Colors.dark.tint
};

export default function LibraryScreen() {
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
    
    // Extract brand from title (format: "EBOSS Product: Title by Brand – EBOSS - Brand")
    const titleMatch = metadata.title?.match(/^EBOSS Product: (.+) by (.+?) – EBOSS/);
    const productTitle = titleMatch?.[1] || metadata.section_title || result.title || 'Unknown Product';
    const brand = titleMatch?.[2] || metadata.manufacturer || 'Unknown Brand';
    
    // Extract categories from tags
    const tagArray = metadata.tags?.split(',') || [];
    const categories = tagArray.filter(tag => 
      !['product', 'eboss', 'nz_building'].includes(tag.trim())
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
          <TouchableOpacity key={`${item.id}-${index}`} style={styles.productCard}>
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
              {item.score && (
                <View style={styles.scoreBadge}>
                  <Text style={styles.scoreText}>
                    {Math.round(Math.abs(item.score) * 100)}%
                  </Text>
                </View>
              )}
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