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
  };
  chunk_id: string;
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

  const filters = [
    { id: 'all', label: 'All', count: knowledgeStats?.total_documents || 0 },
    { id: 'nzbc', label: 'Building Code', count: knowledgeStats?.documents_by_type?.nzbc || 0 },
    { id: 'manufacturer', label: 'Manufacturers', count: knowledgeStats?.documents_by_type?.manufacturer || 0 },
    { id: 'nzs', label: 'NZ Standards', count: knowledgeStats?.documents_by_type?.nzs || 0 },
    { id: 'eboss_product', label: 'Products', count: knowledgeStats?.documents_by_type?.eboss_product || 0 },
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

  const getDisplayData = () => {
    if (searchQuery.length > 2) {
      return searchResults.map(result => ({
        id: result.chunk_id,
        type: result.metadata.document_type,
        title: result.metadata.section_title || result.title,
        snippet: result.content.substring(0, 150) + '...',
        tags: extractBuildingCodes(result.content, result.metadata),
        score: result.similarity_score,
        savedAt: 'Search result'
      }));
    }
    
    if (knowledgeStats?.recent_documents) {
      return knowledgeStats.recent_documents
        .filter(doc => selectedFilter === 'all' || doc.type === selectedFilter)
        .map(doc => ({
          id: doc.title,
          type: doc.type,
          title: doc.title,
          snippet: 'Recent document from knowledge base',
          tags: extractBuildingCodes(doc.title, {}),
          savedAt: formatTimeAgo(doc.processed_at)
        }));
    }
    
    return [];
  };

  const displayItems = getDisplayData();

  return (
    <View style={styles.container}>
      {/* Search bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <IconSymbol name="info.circle.fill" size={16} color={Colors.dark.icon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search library..."
            placeholderTextColor={Colors.dark.placeholder}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
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
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Library items */}
      <ScrollView style={styles.libraryList}>
        {filteredItems.map((item) => (
          <TouchableOpacity key={item.id} style={styles.libraryItem}>
            <View style={styles.itemHeader}>
              <IconSymbol 
                name={typeIcons[item.type]} 
                size={20} 
                color={Colors.dark.tint} 
              />
              <Text style={styles.itemTitle}>{item.title}</Text>
            </View>
            
            <Text style={styles.itemSnippet}>{item.snippet}</Text>
            
            <View style={styles.itemFooter}>
              <View style={styles.tags}>
                {item.tags.map((tag) => (
                  <View key={tag} style={styles.tag}>
                    <Text style={styles.tagText}>{tag}</Text>
                  </View>
                ))}
              </View>
              <Text style={styles.savedAt}>{item.savedAt}</Text>
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Empty state */}
      {filteredItems.length === 0 && (
        <View style={styles.emptyState}>
          <IconSymbol name="books.vertical.fill" size={48} color={Colors.dark.icon} />
          <Text style={styles.emptyTitle}>
            {searchQuery ? 'No matches found' : 'Library is empty'}
          </Text>
          <Text style={styles.emptySubtitle}>
            {searchQuery 
              ? 'Try adjusting your search or filter'
              : 'Save answers, manuals, and job packs to build your library'
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
  searchContainer: {
    paddingHorizontal: 20,
    paddingTop: 16,
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
  filtersContainer: {
    paddingLeft: 20,
    marginBottom: 20,
  },
  filtersContent: {
    paddingRight: 20,
    gap: 8,
  },
  filterTab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: Colors.dark.surface,
    borderWidth: 1,
    borderColor: Colors.dark.border,
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
  libraryList: {
    flex: 1,
    paddingHorizontal: 20,
  },
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
  },
  tagText: {
    fontSize: 12,
    color: Colors.dark.text,
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