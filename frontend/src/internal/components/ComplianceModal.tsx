import React, { useState } from 'react';
import { View, Text, Modal, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { FileText, CheckCircle, X } from 'lucide-react-native';

interface ComplianceModalProps {
  visible: boolean;
  onClose: () => void;
  onOpenDocument: (source: string, clause: string, page: string, filePath: string) => void;
  source: string;
  clause: string;
  page: string;
}

export default function ComplianceModal({ visible, onClose, onOpenDocument, source, clause, page }: ComplianceModalProps) {
  
  // Hardcoded map for MVP (In reality this would be dynamic or in a config file)
  const getLocalPath = (src: string) => {
      const s = src.toLowerCase();
      if (s.includes('3604')) return 'assets/standards/nzs3604.pdf';
      if (s.includes('e2/as1') || s.includes('e2')) return 'assets/standards/e2as1.pdf';
      if (s.includes('3500')) return 'assets/standards/asnzs3500.pdf';
      return 'Unknown - Requires Download';
  };

  const localPath = getLocalPath(source);
  const isAvailable = localPath.startsWith('assets');

  const handleOpenDocument = () => {
      console.log(`🔗 Opening PDF Viewer: ${source} | ${clause} | Page ${page}`);
      onClose(); // Close the modal first
      onOpenDocument(source, clause, page, localPath);
  };

  return (
    <Modal
      animationType="fade"
      transparent={true}
      visible={visible}
      onRequestClose={onClose}
    >
      <View style={styles.centeredView}>
        <View style={styles.modalView}>
          <View style={styles.header}>
            <Text style={styles.modalTitle}>System Check</Text>
            <TouchableOpacity onPress={onClose}>
                <X size={24} color="#999" />
            </TouchableOpacity>
          </View>

          <View style={styles.statusContainer}>
              <View style={styles.statusRow}>
                  <Text style={styles.label}>Status:</Text>
                  <View style={styles.badge}>
                      <CheckCircle size={16} color="#4ADE80" style={{marginRight: 4}} />
                      <Text style={styles.badgeText}>CITATION LINKED</Text>
                  </View>
              </View>

              <View style={styles.divider} />

              <View style={styles.detailRow}>
                  <Text style={styles.label}>Source:</Text>
                  <Text style={styles.value}>{source}</Text>
              </View>
              
              <View style={styles.detailRow}>
                  <Text style={styles.label}>Clause:</Text>
                  <Text style={styles.value}>{clause}</Text>
              </View>

              <View style={styles.detailRow}>
                  <Text style={styles.label}>Target Page:</Text>
                  <Text style={styles.value}>{page}</Text>
              </View>

              <View style={styles.detailRow}>
                  <Text style={styles.label}>File Path:</Text>
                  <Text style={[styles.value, styles.pathText]}>{localPath}</Text>
              </View>
          </View>

          <TouchableOpacity 
            style={[styles.openButton, !isAvailable && styles.disabledButton]}
            onPress={() => console.log(`Opening ${localPath} at page ${page}`)}
            disabled={!isAvailable}
          >
              <FileText size={20} color="white" style={{marginRight: 8}} />
              <Text style={styles.buttonText}>
                  {isAvailable ? "Open Document" : "Document Unavailable"}
              </Text>
          </TouchableOpacity>

        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  centeredView: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  modalView: {
    width: '85%',
    backgroundColor: '#1E1E1E',
    borderRadius: 20,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
    borderWidth: 1,
    borderColor: '#333',
  },
  header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
  },
  statusContainer: {
      backgroundColor: '#111',
      borderRadius: 12,
      padding: 16,
      marginBottom: 24,
  },
  statusRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 8,
  },
  badge: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: 'rgba(74, 222, 128, 0.1)', // Green tint
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 6,
      borderWidth: 1,
      borderColor: 'rgba(74, 222, 128, 0.3)',
  },
  badgeText: {
      color: '#4ADE80',
      fontSize: 12,
      fontWeight: 'bold',
  },
  divider: {
      height: 1,
      backgroundColor: '#333',
      marginVertical: 12,
  },
  detailRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: 8,
  },
  label: {
      color: '#999',
      fontSize: 14,
  },
  value: {
      color: 'white',
      fontSize: 14,
      fontWeight: '500',
      maxWidth: '60%',
      textAlign: 'right',
  },
  pathText: {
      fontFamily: 'monospace',
      fontSize: 12,
      color: '#F97316', // Orange
  },
  openButton: {
      backgroundColor: '#F97316',
      borderRadius: 12,
      padding: 16,
      flexDirection: 'row',
      justifyContent: 'center',
      alignItems: 'center',
  },
  disabledButton: {
      backgroundColor: '#444',
      opacity: 0.6,
  },
  buttonText: {
      color: 'white',
      fontWeight: 'bold',
      fontSize: 16,
  },
});
