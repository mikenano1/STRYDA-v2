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
  answer: 'message.fill',
  manual: 'doc.text',
  jobpack: 'folder.fill',
};

export default function LibraryScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');

  const filters = [
    { id: 'all', label: 'All' },
    { id: 'answers', label: 'Saved Answers' },
    { id: 'manuals', label: 'Manuals' },
    { id: 'jobpacks', label: 'Job Packs' },
  ];

  const filteredItems = mockLibraryItems.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.snippet.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesFilter = selectedFilter === 'all' || 
                         (selectedFilter === 'answers' && item.type === 'answer') ||
                         (selectedFilter === 'manuals' && item.type === 'manual') ||
                         (selectedFilter === 'jobpacks' && item.type === 'jobpack');
                         
    return matchesSearch && matchesFilter;
  });

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