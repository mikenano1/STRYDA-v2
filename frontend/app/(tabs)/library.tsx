import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getDocuments, Document } from '../../src/internal/lib/api';
import { useRouter } from 'expo-router';
import { FileText, ChevronRight, Search } from 'lucide-react-native';

const theme = {
  bg: '#111111',
  text: '#FFFFFF',
  muted: '#A7A7A7',
  card: '#1F1F1F',
  border: '#333333',
  primary: '#F97316'
};

export default function LibraryScreen() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDocs();
  }, []);

  const loadDocs = async () => {
    try {
        const docs = await getDocuments();
        setDocuments(docs);
    } catch (e) {
        console.error(e);
    } finally {
        setLoading(false);
    }
  };

  const openDoc = (doc: Document) => {
      // For now, mapping known docs to public URLs or Google Viewer logic
      let url = "";
      if (doc.source.includes("3604")) url = "https://www.building.govt.nz/assets/Uploads/building-code-compliance/b-stability/b1-structure/as1-nzs3604-2011-light-timber-framed-buildings.pdf";
      else if (doc.source.includes("E2")) url = "https://codehub.building.govt.nz/assets/Approved-Documents/E2-External-moisture-3rd-edition-Amendment-10.pdf";
      else url = "https://codehub.building.govt.nz/"; // Fallback

      router.push({ pathname: '/pdf-viewer', params: { url, title: doc.title } });
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Library</Text>
        <TouchableOpacity style={styles.searchButton}>
            <Search size={24} color="white" />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.sectionTitle}>Compliance Documents</Text>
        
        {loading ? (
            <ActivityIndicator color={theme.primary} size="large" style={{ marginTop: 20 }} />
        ) : (
            documents.map((doc, index) => (
                <TouchableOpacity key={index} style={styles.card} onPress={() => openDoc(doc)}>
                    <View style={styles.iconContainer}>
                        <FileText size={24} color={theme.primary} />
                    </View>
                    <View style={styles.cardContent}>
                        <Text style={styles.cardTitle}>{doc.title}</Text>
                        <Text style={styles.cardSubtitle}>Building Code Reference</Text>
                    </View>
                    <ChevronRight size={20} color={theme.muted} />
                </TouchableOpacity>
            ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.bg,
  },
  header: {
    padding: 24,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: theme.border,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: theme.text,
  },
  searchButton: {
    padding: 8,
    backgroundColor: theme.card,
    borderRadius: 50,
    borderWidth: 1,
    borderColor: theme.border,
  },
  scrollContent: {
    padding: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.text,
    marginBottom: 16,
  },
  card: {
    backgroundColor: theme.card,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: theme.border,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(249, 115, 22, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  cardContent: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.text,
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 12,
    color: theme.muted,
  },
});
