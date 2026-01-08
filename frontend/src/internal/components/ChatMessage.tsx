/**
 * Chat Message Component
 * Renders user/assistant messages with citations and error states
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { ChatMessage, Citation } from '../types/chat';
import CitationPill from './CitationPill';
import ComplianceModal from './ComplianceModal';

interface ChatMessageProps {
  message: ChatMessage;
  onCitationPress: (citation: Citation) => void;
  onOpenDocument: (source: string, clause: string, page: string, filePath: string) => void;
  onRetry?: (messageId: string) => void;
}

export function ChatMessageComponent({ message, onCitationPress, onOpenDocument, onRetry }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState<{
    source: string; 
    clause: string; 
    page: string; 
    textContent?: string;
    evidenceCollection?: any[];
  } | null>(null);

  // Format timestamp
  const formatTime = (ts: number) => {
    const date = new Date(ts);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleRetry = () => {
    if (onRetry) {
      console.log('🔄 Retry requested for message:', message.id);
      onRetry(message.id);
    }
  };

  // Helper to find citation data from citations array by matching source
  const findCitationData = (source: string): { textContent?: string; evidenceCollection?: any[] } => {
    if (!message.citations || message.citations.length === 0) return {};
    
    // Multiple matching strategies for flexible source matching
    const searchSource = source.toLowerCase().trim();
    
    // Strategy 1: Extract brand name from the beginning
    // "EXPOL ThermaSlab Family (EPS) Technical Data Sheet" -> "expol"
    const extractBrandName = (s: string): string => {
      const normalized = s.toLowerCase().trim();
      // First word is often the brand
      const firstWord = normalized.split(/[\s\-]/)[0];
      // Also try splitting on delimiters
      const beforeDelimiter = normalized.split(/[|\-•]/)[0].trim();
      return firstWord.length > 2 ? firstWord : beforeDelimiter;
    };
    
    const searchBrand = extractBrandName(source);
    
    // Strategy 2: Check if either source contains the other (partial match)
    const containsMatch = (a: string, b: string): boolean => {
      const aLower = a.toLowerCase();
      const bLower = b.toLowerCase();
      return aLower.includes(bLower) || bLower.includes(aLower);
    };
    
    // Strategy 3: Brand extraction from both sides
    const brandMatch = (citationSource: string, searchSource: string): boolean => {
      const citationBrand = extractBrandName(citationSource);
      const searchBrand = extractBrandName(searchSource);
      return citationBrand === searchBrand && citationBrand.length > 2;
    };
    
    // Find matching citation using multiple strategies
    let match = message.citations.find((c: any) => {
      const citationSource = (c.source || c.title || '').toLowerCase().trim();
      
      // Exact match (after lowercase)
      if (citationSource === searchSource) return true;
      
      // Brand name match (most reliable for normalized vs full names)
      if (brandMatch(citationSource, searchSource)) return true;
      
      // Contains match (one is substring of other)
      if (containsMatch(citationSource, searchSource)) return true;
      
      return false;
    });
    
    // Fallback: If still no match, try any citation with evidence
    if (!match && message.citations.length > 0) {
      // Pick first citation that has text content
      match = message.citations.find((c: any) => 
        c.text_content || c.snippet || (c.evidence_collection && c.evidence_collection.length > 0)
      );
    }
    
    console.log(`🔍 findCitationData: source="${source}" -> matched=${match?.source || 'NONE'}`);
    
    return {
      textContent: match?.text_content || match?.snippet,
      evidenceCollection: match?.evidence_collection || []
    };
  };

  const handlePillPress = (source: string, clause: string, page: string) => {
      console.log(`🟠🟠🟠 CITATION BUTTON PRESSED 🟠🟠🟠`);
      console.log(`>>> Source: ${source}`);
      console.log(`>>> Clause: ${clause}`);
      console.log(`>>> Page: ${page}`);
      
      // Try to find citation data (text content + evidence collection) from the citations array
      const citationData = findCitationData(source);
      console.log(`>>> Text Content found: ${citationData.textContent ? 'YES' : 'NO'}`);
      console.log(`>>> Evidence Collection: ${citationData.evidenceCollection?.length || 0} items`);
      
      setSelectedMatch({ 
        source, 
        clause, 
        page, 
        textContent: citationData.textContent,
        evidenceCollection: citationData.evidenceCollection 
      });
      setModalVisible(true);
      console.log(`>>> Modal state set to TRUE`);
  };

  // Function to clean markdown artifacts from AI responses
  const cleanMarkdown = (text: string): string => {
      return text
          .replace(/\*\*(.*?)\*\*/g, '$1')  // **bold** → bold
          .replace(/\*(.*?)\*/g, '$1')       // *italic* → italic
          .replace(/__(.*?)__/g, '$1')       // __underline__ → underline
          .replace(/~~(.*?)~~/g, '$1')       // ~~strikethrough~~ → strikethrough
          .replace(/^#+\s*/gm, '')           // # headers → plain text
          .replace(/^[-*]\s+/gm, '• ')       // - bullets → • bullets
          .replace(/^>\s*/gm, '')            // > blockquotes → plain
          .replace(/`([^`]+)`/g, '$1')       // `code` → code
          .replace(/^['"`]|['"`]$/g, '')     // Remove wrapping quotes
          .trim();
  };

  // Regex to parse the hybrid citation format
  // Updated to handle optional Clause field and various source name formats (with spaces, dashes, dots)
  // Format 1: [[Source: X | Clause: Y | Page: Z]]
  // Format 2: [[Source: X | Page: Z]] (no clause)
  // Format 3: [[Source: X]] (just source)
  const citationRegexFull = /\[\[Source:\s*([^|\]]+?)\s*\|\s*Clause:\s*([^|\]]+?)\s*\|\s*Page:\s*([^\]]+?)\]\]/g;
  const citationRegexNoClause = /\[\[Source:\s*([^|\]]+?)\s*\|\s*Page:\s*([^\]]+?)\]\]/g;
  const citationRegexSourceOnly = /\[\[Source:\s*([^\]]+?)\]\]/g;
  
  // Helper function to normalize source names for display
  // "J&L Duke - J-frame-BRANZ • 7.4" → "J&L Duke"
  const normalizeSourceForDisplay = (source: string): string => {
    // Split on pipe, dash, or bullet point and take the first part
    const baseSource = source.split(/[|\-•]/)[0].trim();
    return baseSource || source;
  };
  
  // Find all matches for each format
  const matchesFull = [...(message.text || '').matchAll(citationRegexFull)];
  const matchesNoClause = [...(message.text || '').matchAll(citationRegexNoClause)];
  const matchesSourceOnly = [...(message.text || '').matchAll(citationRegexSourceOnly)];
  
  // Combine all matches into a unified format: { source, clause, page }
  const allMatches: { source: string; clause: string; page: string; raw: string }[] = [];
  
  // Full matches (Source + Clause + Page)
  matchesFull.forEach(match => {
    allMatches.push({
      source: match[1].trim(),
      clause: match[2].trim(),
      page: match[3].trim(),
      raw: match[0]
    });
  });
  
  // No Clause matches (Source + Page)
  matchesNoClause.forEach(match => {
    // Check if this wasn't already matched by the full regex
    const alreadyMatched = allMatches.some(m => m.raw.includes(match[1].trim()));
    if (!alreadyMatched) {
      allMatches.push({
        source: match[1].trim(),
        clause: '',
        page: match[2].trim(),
        raw: match[0]
      });
    }
  });
  
  // Source-only matches
  matchesSourceOnly.forEach(match => {
    const alreadyMatched = allMatches.some(m => m.source === match[1].trim());
    if (!alreadyMatched) {
      allMatches.push({
        source: match[1].trim(),
        clause: '',
        page: '1',
        raw: match[0]
      });
    }
  });
  
  // Remove all citation formats from raw text
  let rawText = message.text || '';
  rawText = rawText.replace(citationRegexFull, '');
  rawText = rawText.replace(citationRegexNoClause, '');
  rawText = rawText.replace(citationRegexSourceOnly, '');
  rawText = rawText.trim();
  
  const cleanText = cleanMarkdown(rawText);

  return (
    <>
        <View style={[styles.messageContainer, isUser ? styles.userContainer : styles.assistantContainer]}>
        {/* Message bubble */}
        <View style={[
            styles.messageBubble,
            isUser ? styles.userBubble : styles.assistantBubble,
            message.error && styles.errorBubble
        ]}>
            {/* Loading indicator */}
            {message.loading && isAssistant && (
            <View style={styles.loadingContainer}>
                <Text style={styles.loadingText}>STRYDA is thinking...</Text>
            </View>
            )}
            
            {/* Message text */}
            {!message.loading && (
            <View>
                <Text style={[
                    styles.messageText,
                    isUser ? styles.userText : styles.assistantText
                ]}>
                    {cleanText}
                </Text>

                {/* Parsed Citation Pills - deduplicated by normalized source name */}
                {(() => {
                    // Deduplicate by normalized source name
                    const seenSources = new Set<string>();
                    const uniqueMatches = allMatches.filter(match => {
                        const normalizedSource = normalizeSourceForDisplay(match.source);
                        if (seenSources.has(normalizedSource)) {
                            return false;
                        }
                        seenSources.add(normalizedSource);
                        return true;
                    }).slice(0, 3); // Max 3 pills
                    
                    return uniqueMatches.map((match, i) => {
                        const displaySource = normalizeSourceForDisplay(match.source);
                        return (
                            <TouchableOpacity 
                                key={`parsed-${i}`} 
                                onPress={() => handlePillPress(match.source, match.clause, match.page)} 
                                style={styles.pillButton}
                                activeOpacity={0.6}
                                hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                            >
                                <Text style={styles.pillText}>
                                    📄 {displaySource.length > 30 ? displaySource.substring(0, 30) + '...' : displaySource}
                                    {match.page ? ` • p.${match.page}` : ''}
                                </Text>
                            </TouchableOpacity>
                        );
                    });
                })()}
            </View>
            )}
            
            {/* Error state with retry */}
            {message.error && (
            <TouchableOpacity 
                style={styles.retryButton}
                onPress={handleRetry}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
                <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
            )}
        </View>
        
        {/* Timestamp */}
        <View style={[styles.timestampContainer, isUser ? styles.userTimestamp : styles.assistantTimestamp]}>
            <Text style={styles.timestampText}>
            {formatTime(message.ts)}
            </Text>
        </View>
        </View>

        {/* Compliance Modal - MOVED OUTSIDE BUBBLE, INSIDE FRAGMENT */}
        {selectedMatch && (
            <ComplianceModal 
                visible={modalVisible}
                onClose={() => setModalVisible(false)}
                onOpenDocument={onOpenDocument}
                source={selectedMatch.source}
                clause={selectedMatch.clause}
                page={selectedMatch.page}
                textContent={selectedMatch.textContent}
                evidenceCollection={selectedMatch.evidenceCollection}
            />
        )}
    </>
  );
}

const styles = StyleSheet.create({
  messageContainer: {
    marginVertical: 8,
    marginHorizontal: 16,
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '85%',
    padding: 12,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: '#FF7A00', // Orange accent
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#2A2A2A', // Dark gray
    borderBottomLeftRadius: 4,
  },
  errorBubble: {
    backgroundColor: '#FF4444', // Error red
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: '#000000', // Black on orange
    fontWeight: '500',
  },
  assistantText: {
    color: '#FFFFFF', // White on dark
  },
  loadingContainer: {
    paddingVertical: 4,
  },
  loadingText: {
    color: '#CCCCCC',
    fontSize: 14,
    fontStyle: 'italic',
  },
  retryButton: {
    marginTop: 8,
    backgroundColor: '#FFFFFF20',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    alignSelf: 'flex-start',
  },
  retryText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  timestampContainer: {
    marginTop: 4,
  },
  userTimestamp: {
    alignItems: 'flex-end',
  },
  assistantTimestamp: {
    alignItems: 'flex-start',
  },
  timestampText: {
    color: '#888888',
    fontSize: 12,
  },
  pillButton: {
      marginTop: 12,
      backgroundColor: '#F97316',
      paddingVertical: 10,
      paddingHorizontal: 16,
      borderRadius: 12,
      alignSelf: 'flex-start',
      zIndex: 9999, // Force top
      elevation: 10, // Android shadow/z-index
  },
  pillText: {
      color: 'white',
      fontWeight: 'bold',
      fontSize: 14,
  }
});

export default ChatMessageComponent;
