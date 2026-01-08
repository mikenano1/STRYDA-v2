import React from 'react';
import { View, Text, Modal, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { FileText, X, BookOpen, ChevronRight } from 'lucide-react-native';

interface EvidenceItem {
  text: string;
  page?: string;
  clause?: string;
  section?: string;
  score?: number;
  doc_type?: string;
  original_source?: string;
}

interface ComplianceModalProps {
  visible: boolean;
  onClose: () => void;
  onOpenDocument: (source: string, clause: string, page: string, filePath: string) => void;
  source: string;
  clause: string;
  page: string;
  textContent?: string;
  evidenceCollection?: EvidenceItem[];
}

export default function ComplianceModal({ 
  visible, 
  onClose, 
  onOpenDocument, 
  source, 
  clause, 
  page,
  textContent,
  evidenceCollection 
}: ComplianceModalProps) {
  
  // Normalize source name for display (strip suffixes after |, -, •)
  const normalizeSource = (src: string): string => {
    const baseSource = src.split(/[|\-•]/)[0].trim();
    return baseSource || src;
  };

  const displaySource = normalizeSource(source);
  
  // Determine what content to show
  const hasEvidenceCollection = evidenceCollection && evidenceCollection.length > 0;
  const hasTextContent = textContent && textContent.trim().length > 0;
  const hasAnyEvidence = hasEvidenceCollection || hasTextContent;

  // Format clause/page header for an evidence item
  const formatEvidenceHeader = (item: EvidenceItem, index: number): string => {
    const parts = [];
    if (item.clause) parts.push(`Clause ${item.clause}`);
    if (item.page) parts.push(`Page ${item.page}`);
    if (item.section) parts.push(item.section);
    
    if (parts.length === 0) return `Evidence ${index + 1}`;
    return parts.join(' • ');
  };

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
              <Text style={styles.modalTitle}>Source Evidence</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <X size={24} color="#999" />
            </TouchableOpacity>
          </View>

          {/* Source Info */}
          <View style={styles.sourceInfoContainer}>
            <Text style={styles.sourceTitle}>{displaySource}</Text>
            {hasEvidenceCollection && (
              <Text style={styles.sourceMeta}>
                {evidenceCollection!.length} evidence snippet{evidenceCollection!.length !== 1 ? 's' : ''} found
              </Text>
            )}
          </View>

          {/* Evidence Content */}
          <ScrollView 
            style={styles.evidenceContainer}
            showsVerticalScrollIndicator={true}
            contentContainerStyle={styles.evidenceScrollContent}
          >
            {hasEvidenceCollection ? (
              // MULTI-EVIDENCE: Loop through evidence_collection
              evidenceCollection!.map((item, index) => (
                <View key={index}>
                  {/* Divider between items (except first) */}
                  {index > 0 && <View style={styles.evidenceDivider} />}
                  
                  {/* Evidence Item */}
                  <View style={styles.evidenceItem}>
                    {/* Header: Clause/Page */}
                    <View style={styles.evidenceHeader}>
                      <FileText size={14} color="#FF7A00" />
                      <Text style={styles.evidenceHeaderText}>
                        {formatEvidenceHeader(item, index)}
                      </Text>
                    </View>
                    
                    {/* Document Type Badge (if available) */}
                    {item.doc_type && (
                      <View style={styles.docTypeBadge}>
                        <Text style={styles.docTypeText}>{item.doc_type.replace(/_/g, ' ')}</Text>
                      </View>
                    )}
                    
                    {/* Evidence Text */}
                    <Text style={styles.evidenceText}>{item.text}</Text>
                  </View>
                </View>
              ))
            ) : hasTextContent ? (
              // SINGLE EVIDENCE: Fallback to text_content
              <View style={styles.evidenceItem}>
                <View style={styles.evidenceHeader}>
                  <FileText size={14} color="#FF7A00" />
                  <Text style={styles.evidenceHeaderText}>
                    {clause ? `Clause ${clause}` : ''}{clause && page ? ' • ' : ''}{page ? `Page ${page}` : 'Evidence'}
                  </Text>
                </View>
                <Text style={styles.evidenceText}>{textContent}</Text>
              </View>
            ) : (
              // NO EVIDENCE
              <View style={styles.noContentContainer}>
                <FileText size={32} color="#666" />
                <Text style={styles.noContentTitle}>Evidence Not Available</Text>
                <Text style={styles.noContentText}>
                  The source text for this citation is not currently loaded.
                  Reference: {source}
                </Text>
              </View>
            )}
          </ScrollView>

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
    maxHeight: '85%',
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
    maxHeight: 350,
    backgroundColor: '#111',
    borderRadius: 12,
    marginBottom: 16,
  },
  evidenceScrollContent: {
    padding: 16,
  },
  evidenceItem: {
    marginVertical: 8,
  },
  evidenceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  evidenceHeaderText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FF7A00',
  },
  docTypeBadge: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255, 122, 0, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    marginBottom: 8,
  },
  docTypeText: {
    fontSize: 11,
    color: '#FF7A00',
    textTransform: 'capitalize',
  },
  evidenceText: {
    fontSize: 14,
    color: '#E0E0E0',
    lineHeight: 22,
  },
  evidenceDivider: {
    height: 1,
    backgroundColor: '#333',
    marginVertical: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
    padding: 40,
  },
  loadingText: {
    color: '#999',
    fontSize: 14,
  },
  noContentContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 30,
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
