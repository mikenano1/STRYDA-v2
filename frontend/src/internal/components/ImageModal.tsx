import React from 'react';
import { View, Text, Modal, TouchableOpacity, StyleSheet, Image, Dimensions, ActivityIndicator } from 'react-native';
import { Image as ImageIcon, X, ExternalLink } from 'lucide-react-native';
import * as Linking from 'expo-linking';

interface ImageModalProps {
  visible: boolean;
  onClose: () => void;
  source: string;
  page: string;
  imageUrl: string;
  summary?: string;
  imageType?: string;
  brand?: string;
}

export default function ImageModal({ 
  visible, 
  onClose, 
  source, 
  page,
  imageUrl,
  summary,
  imageType,
  brand
}: ImageModalProps) {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(false);
  
  const screenWidth = Dimensions.get('window').width;
  const imageWidth = screenWidth - 80; // Modal padding
  
  // Normalize source name for display
  const normalizeSource = (src: string): string => {
    const baseSource = src.split(/[|\-•]/)[0].trim();
    return baseSource || src;
  };

  const displaySource = normalizeSource(source);
  const displayType = imageType?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || 'Image';
  
  const handleOpenExternal = () => {
    if (imageUrl) {
      Linking.openURL(imageUrl);
    }
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
              <ImageIcon size={20} color="#FF7A00" style={{marginRight: 8}} />
              <Text style={styles.modalTitle}>View Image</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <X size={24} color="#999" />
            </TouchableOpacity>
          </View>

          {/* Source Info */}
          <View style={styles.sourceInfoContainer}>
            <Text style={styles.sourceTitle}>{displaySource}</Text>
            <Text style={styles.sourceMeta}>
              {displayType} • Page {page}
              {brand && ` • ${brand}`}
            </Text>
          </View>

          {/* Image Container */}
          <View style={styles.imageContainer}>
            {loading && (
              <View style={styles.loadingOverlay}>
                <ActivityIndicator size="large" color="#FF7A00" />
                <Text style={styles.loadingText}>Loading image...</Text>
              </View>
            )}
            
            {error ? (
              <View style={styles.errorContainer}>
                <ImageIcon size={48} color="#666" />
                <Text style={styles.errorText}>Failed to load image</Text>
                <TouchableOpacity 
                  style={styles.externalButton}
                  onPress={handleOpenExternal}
                >
                  <ExternalLink size={16} color="#FF7A00" />
                  <Text style={styles.externalButtonText}>Open in Browser</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <Image
                source={{ uri: imageUrl }}
                style={[styles.image, { width: imageWidth, height: imageWidth * 0.75 }]}
                resizeMode="contain"
                onLoadStart={() => setLoading(true)}
                onLoadEnd={() => setLoading(false)}
                onError={() => {
                  setLoading(false);
                  setError(true);
                }}
              />
            )}
          </View>

          {/* Summary */}
          {summary && (
            <View style={styles.summaryContainer}>
              <Text style={styles.summaryLabel}>📝 AI Analysis:</Text>
              <Text style={styles.summaryText}>{summary}</Text>
            </View>
          )}

          {/* Footer */}
          <View style={styles.footer}>
            <TouchableOpacity 
              style={styles.externalLinkButton}
              onPress={handleOpenExternal}
            >
              <ExternalLink size={16} color="#FF7A00" />
              <Text style={styles.externalLinkText}>Open Full Size</Text>
            </TouchableOpacity>
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
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
  },
  modalView: {
    backgroundColor: '#1A1A1A',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingTop: 20,
    paddingHorizontal: 20,
    paddingBottom: 34,
    maxHeight: '90%',
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
  imageContainer: {
    backgroundColor: '#111',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 200,
  },
  image: {
    borderRadius: 8,
  },
  loadingOverlay: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    color: '#999',
    fontSize: 14,
  },
  errorContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    padding: 20,
  },
  errorText: {
    color: '#999',
    fontSize: 14,
  },
  externalButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#252525',
    borderRadius: 8,
  },
  externalButtonText: {
    color: '#FF7A00',
    fontSize: 14,
    fontWeight: '500',
  },
  summaryContainer: {
    backgroundColor: '#252525',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  summaryLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FF7A00',
    marginBottom: 8,
  },
  summaryText: {
    fontSize: 14,
    color: '#E0E0E0',
    lineHeight: 20,
  },
  footer: {
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#333',
    marginBottom: 12,
    alignItems: 'center',
  },
  externalLinkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  externalLinkText: {
    color: '#FF7A00',
    fontSize: 14,
    fontWeight: '500',
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
