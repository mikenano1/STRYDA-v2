/**
 * PDF Viewer Screen
 * Displays PDFs from local assets or remote URLs with page jumping capability
 */

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity, Platform, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronLeft, ZoomIn, ZoomOut, FileText, ExternalLink } from 'lucide-react-native';
import * as Linking from 'expo-linking';

// For Expo Go compatibility, we'll use a WebView-based PDF viewer
// react-native-pdf requires native builds
import { WebView } from 'react-native-webview';

const { width, height } = Dimensions.get('window');

// Map of local assets to hosted URLs (since Expo Go can't bundle PDFs directly)
// In a production build, these would be bundled assets
const PDF_SOURCES: Record<string, string> = {
    'nzs3604': 'https://www.standards.govt.nz/shop/nzs-36042011/',
    'e2as1': 'https://www.building.govt.nz/assets/Uploads/building-code-compliance/e-moisture/e2-external-moisture/asvm/e2-external-moisture-1st-edition-amendment-1.pdf',
    // Placeholder - in production you'd host these or bundle them
};

export default function PDFViewerScreen() {
    const router = useRouter();
    const params = useLocalSearchParams();
    
    const source = params.source as string || 'Unknown';
    const clause = params.clause as string || '';
    const page = params.page as string || '1';
    const filePath = params.filePath as string || '';

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [scale, setScale] = useState(1.0);

    // Parse page number (handle formats like "6-5" -> page 5 of section 6)
    const getPageNumber = (): number => {
        if (!page) return 1;
        // If format is "6-5", extract the second number as the page
        if (page.includes('-')) {
            const parts = page.split('-');
            return parseInt(parts[1]) || 1;
        }
        return parseInt(page) || 1;
    };

    const pageNum = getPageNumber();

    // Determine PDF URL
    const getPdfUrl = (): string => {
        // Check if it's a known local asset
        const sourceKey = source.toLowerCase();
        if (sourceKey.includes('3604')) {
            // For NZS 3604, use Google Docs viewer with a placeholder
            // In production, you'd host your own PDF or use a licensed copy
            return `https://docs.google.com/viewer?url=${encodeURIComponent('https://www.standards.govt.nz/shop/nzs-36042011/')}&embedded=true`;
        }
        if (sourceKey.includes('e2')) {
            return `https://docs.google.com/viewer?url=${encodeURIComponent(PDF_SOURCES['e2as1'])}&embedded=true&page=${pageNum}`;
        }
        
        // Default: show info screen
        return '';
    };

    const pdfUrl = getPdfUrl();

    const handleOpenExternal = async () => {
        const url = source.includes('3604') 
            ? 'https://www.standards.govt.nz/shop/nzs-36042011/'
            : 'https://www.building.govt.nz/building-code-compliance/e-moisture/e2-external-moisture/';
        
        await Linking.openURL(url);
    };

    return (
        <SafeAreaView style={styles.container} edges={['top']}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <ChevronLeft size={24} color="#FFF" />
                </TouchableOpacity>
                <View style={styles.headerInfo}>
                    <Text style={styles.headerTitle} numberOfLines={1}>{source}</Text>
                    <Text style={styles.headerSubtitle}>Clause {clause} • Page {page}</Text>
                </View>
                <TouchableOpacity onPress={handleOpenExternal} style={styles.externalButton}>
                    <ExternalLink size={20} color="#F97316" />
                </TouchableOpacity>
            </View>

            {/* Content */}
            <View style={styles.content}>
                {/* Info Card - Since PDFs can't be bundled in Expo Go */}
                <View style={styles.infoCard}>
                    <FileText size={64} color="#F97316" style={styles.infoIcon} />
                    <Text style={styles.infoTitle}>Document Reference</Text>
                    
                    <View style={styles.detailsContainer}>
                        <View style={styles.detailRow}>
                            <Text style={styles.detailLabel}>Standard:</Text>
                            <Text style={styles.detailValue}>{source}</Text>
                        </View>
                        <View style={styles.detailRow}>
                            <Text style={styles.detailLabel}>Clause:</Text>
                            <Text style={styles.detailValue}>{clause}</Text>
                        </View>
                        <View style={styles.detailRow}>
                            <Text style={styles.detailLabel}>Page Reference:</Text>
                            <Text style={styles.detailValue}>{page}</Text>
                        </View>
                    </View>

                    <View style={styles.noteContainer}>
                        <Text style={styles.noteText}>
                            📋 NZ Building Standards are copyrighted documents. 
                            To view the full text, you need a licensed copy from Standards New Zealand.
                        </Text>
                    </View>

                    <TouchableOpacity style={styles.purchaseButton} onPress={handleOpenExternal}>
                        <ExternalLink size={18} color="#FFF" style={{ marginRight: 8 }} />
                        <Text style={styles.purchaseButtonText}>View on Standards NZ</Text>
                    </TouchableOpacity>

                    <Text style={styles.tipText}>
                        💡 Tip: If you have a PDF copy of this standard, you can navigate to Clause {clause} on page {page}.
                    </Text>
                </View>
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0A0A0A',
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 16,
        paddingVertical: 12,
        backgroundColor: '#1A1A1A',
        borderBottomWidth: 1,
        borderBottomColor: '#333',
    },
    backButton: {
        padding: 8,
        marginRight: 8,
    },
    headerInfo: {
        flex: 1,
    },
    headerTitle: {
        color: '#FFF',
        fontSize: 16,
        fontWeight: 'bold',
    },
    headerSubtitle: {
        color: '#999',
        fontSize: 12,
        marginTop: 2,
    },
    externalButton: {
        padding: 8,
        backgroundColor: '#2A2A2A',
        borderRadius: 8,
    },
    content: {
        flex: 1,
        padding: 16,
        justifyContent: 'center',
    },
    infoCard: {
        backgroundColor: '#1A1A1A',
        borderRadius: 16,
        padding: 24,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#333',
    },
    infoIcon: {
        marginBottom: 16,
    },
    infoTitle: {
        color: '#FFF',
        fontSize: 20,
        fontWeight: 'bold',
        marginBottom: 20,
    },
    detailsContainer: {
        width: '100%',
        backgroundColor: '#0A0A0A',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
    },
    detailRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 8,
    },
    detailLabel: {
        color: '#888',
        fontSize: 14,
    },
    detailValue: {
        color: '#FFF',
        fontSize: 14,
        fontWeight: '600',
        maxWidth: '60%',
        textAlign: 'right',
    },
    noteContainer: {
        backgroundColor: '#F97316' + '15',
        borderRadius: 8,
        padding: 12,
        marginBottom: 16,
        borderLeftWidth: 3,
        borderLeftColor: '#F97316',
    },
    noteText: {
        color: '#CCC',
        fontSize: 13,
        lineHeight: 18,
    },
    purchaseButton: {
        backgroundColor: '#F97316',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 14,
        paddingHorizontal: 24,
        borderRadius: 12,
        width: '100%',
        marginBottom: 16,
    },
    purchaseButtonText: {
        color: '#FFF',
        fontSize: 16,
        fontWeight: 'bold',
    },
    tipText: {
        color: '#666',
        fontSize: 12,
        textAlign: 'center',
        lineHeight: 18,
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingText: {
        color: '#999',
        marginTop: 12,
    },
    webview: {
        flex: 1,
        backgroundColor: '#0A0A0A',
    },
});
