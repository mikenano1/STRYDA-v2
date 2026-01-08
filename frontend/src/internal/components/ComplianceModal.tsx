import React, { useState, useEffect } from 'react';
import { View, Text, Modal, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { FileText, CheckCircle, X, BookOpen } from 'lucide-react-native';

interface ComplianceModalProps {
  visible: boolean;
  onClose: () => void;
  onOpenDocument: (source: string, clause: string, page: string, filePath: string) => void;
  source: string;
  clause: string;
  page: string;
  textContent?: string;  // RAG snippet / evidence text
}

export default function ComplianceModal({ 
  visible, 
  onClose, 
  onOpenDocument, 
  source, 
  clause, 
  page,
  textContent 
}: ComplianceModalProps) {
  
  const [fetchedContent, setFetchedContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Normalize source name for display (strip suffixes after |, -, •)
  const normalizeSource = (src: string): string => {
    const baseSource = src.split(/[|\-•]/)[0].trim();
    return baseSource || src;
  };

  const displaySource = normalizeSource(source);
  
  // Try to fetch evidence from backend if not provided
  useEffect(() => {
    if (visible && !textContent && source) {
      // Could fetch from backend here if needed
      // For now, just show what we have
      setFetchedContent(null);
    }
  }, [visible, source, textContent]);

  // Determine what content to show
  const evidenceText = textContent || fetchedContent;
  const hasEvidence = evidenceText && evidenceText.trim().length > 0;

  return (
    <Modal
      animationType="slide"
      transparent={true}
      visible={visible}
      onRequestClose={onClose}
    >
      <View style={styles.centeredView}>
        <View style={styles.modalView}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.headerTitleContainer}>
              <BookOpen size={20} color="#FF7A00" style={{marginRight: 8}} />
              <Text style={styles.modalTitle}>Source Extract</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <X size={24} color="#999" />
            </TouchableOpacity>
          </View>

          {/* Source Info */}
          <View style={styles.sourceInfoContainer}>
            <Text style={styles.sourceTitle}>{displaySource}</Text>
            {(clause || page) && (
              <Text style={styles.sourceMeta}>
                {clause ? `${clause}` : ''}
                {clause && page ? ' • ' : ''}
                {page ? `Page ${page}` : ''}
              </Text>
            )}
          </View>

          {/* Evidence Content */}
          <View style={styles.evidenceContainer}>
            {isLoading ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="small" color="#FF7A00" />
                <Text style={styles.loadingText}>Loading evidence...</Text>
              </View>
            ) : hasEvidence ? (
              <ScrollView 
                style={styles.evidenceScroll}
                showsVerticalScrollIndicator={true}
              >
                <Text style={styles.evidenceText}>{evidenceText}</Text>
              </ScrollView>
            ) : (
              <View style={styles.noContentContainer}>
                <FileText size={32} color="#666" />
                <Text style={styles.noContentTitle}>Evidence Not Available</Text>
                <Text style={styles.noContentText}>
                  The source text for this citation is not currently loaded.
                  The reference points to: {source}
                </Text>
              </View>
            )}
          </View>

          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>
              📚 Source Extract (Generated from Search)
            </Text>
          </View>

          {/* Close Button */}
          <TouchableOpacity 
            style={styles.closeFullButton}
            onPress={onClose}
          >
            <Text style={styles.closeButtonText}>Close</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  centeredView: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  modalView: {
    backgroundColor: '#1A1A1A',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingTop: 20,
    paddingHorizontal: 20,
    paddingBottom: 34,
    maxHeight: '80%',
    borderWidth: 1,
    borderColor: '#333',
    borderBottomWidth: 0,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  headerTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: 'white',
  },
  closeButton: {
    padding: 4,
  },
  sourceInfoContainer: {
    backgroundColor: '#252525',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#FF7A00',
  },
  sourceTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FF7A00',
    marginBottom: 4,
  },
  sourceMeta: {
    fontSize: 13,
    color: '#999',
  },
  evidenceContainer: {
    flex: 1,
    minHeight: 150,
    maxHeight: 300,
    backgroundColor: '#111',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  evidenceScroll: {
    flex: 1,
  },
  evidenceText: {
    fontSize: 14,
    color: '#E0E0E0',
    lineHeight: 22,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    color: '#999',
    fontSize: 14,
  },
  noContentContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    gap: 12,
  },
  noContentTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#888',
  },
  noContentText: {
    fontSize: 13,
    color: '#666',
    textAlign: 'center',
    lineHeight: 18,
  },
  footer: {
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#333',
    marginBottom: 12,
  },
  footerText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  closeFullButton: {
    backgroundColor: '#FF7A00',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  closeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});
