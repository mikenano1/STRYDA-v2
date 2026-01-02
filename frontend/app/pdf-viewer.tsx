/**
 * PDF Viewer Screen
 * Displays PDFs using WebView with Google Docs Viewer
 * Supports page jumping and handles NZ Building Standards
 */

import React, { useState, useRef, useEffect } from 'react';
import { 
    View, 
    Text, 
    StyleSheet, 
    ActivityIndicator, 
    TouchableOpacity, 
    Platform,
    Alert,
    Share
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronLeft, ExternalLink, Share2, AlertCircle, FileText, BookOpen } from 'lucide-react-native';
import { WebView } from 'react-native-webview';
import * as Linking from 'expo-linking';

// Mapping of sources to their official/hosted PDF URLs
// Note: NZ Standards are copyrighted - these are placeholder/official links
const PDF_URL_MAP: Record<string, string> = {
    // NZS 3604:2011 - Timber-framed buildings (official purchase link)
    'nzs3604': 'https://www.standards.govt.nz/shop/nzs-36042011/',
    
    // E2/AS1 - External Moisture (MBIE hosted, publicly available)
    'e2as1': 'https://www.building.govt.nz/assets/Uploads/building-code-compliance/e-moisture/e2-external-moisture/asvm/e2-external-moisture-1st-edition-amendment-1.pdf',
    
    // B1/AS1 - Structure (MBIE hosted)
    'b1as1': 'https://www.building.govt.nz/assets/Uploads/building-code-compliance/b-stability/b1-structure/asvm/b1-structure-1st-edition-amendment-19.pdf',
    
    // NZ Metal Roofing Code of Practice
    'nzmrm': 'https://www.metalroofing.org.nz/code-of-practice',
};

// Info URLs for standards that can't be directly embedded
const INFO_URL_MAP: Record<string, string> = {
    'nzs3604': 'https://www.standards.govt.nz/shop/nzs-36042011/',
    'e2as1': 'https://www.building.govt.nz/building-code-compliance/e-moisture/e2-external-moisture/',
    'b1as1': 'https://www.building.govt.nz/building-code-compliance/b-stability/b1-structure/',
    'nzmrm': 'https://www.metalroofing.org.nz/code-of-practice',
};

export default function PDFViewerScreen() {
    const router = useRouter();
    const params = useLocalSearchParams();
    const webViewRef = useRef<WebView>(null);
    
    const source = (params.source as string) || 'Unknown Document';
    const clause = (params.clause as string) || '';
    const page = (params.page as string) || '1';
    const filePath = (params.filePath as string) || '';

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [canEmbed, setCanEmbed] = useState(false);

    // Parse page number (handle formats like "6-5" -> page 5)
    const getPageNumber = (): number => {
        if (!page) return 1;
        // If format is "6-5", extract the second number
        if (page.includes('-')) {
            const parts = page.split('-');
            return parseInt(parts[1]) || 1;
        }
        return parseInt(page) || 1;
    };

    const pageNum = getPageNumber();

    // Determine the source key for URL lookup
    const getSourceKey = (): string => {
        const s = source.toLowerCase();
        if (s.includes('3604')) return 'nzs3604';
        if (s.includes('e2') || s.includes('e2/as1')) return 'e2as1';
        if (s.includes('b1') || s.includes('b1/as1')) return 'b1as1';
        if (s.includes('metal') || s.includes('roofing') || s.includes('nzmrm')) return 'nzmrm';
        return '';
    };

    const sourceKey = getSourceKey();

    // Get the PDF URL and determine if it can be embedded
    const getPdfConfig = () => {
        const key = sourceKey;
        const url = PDF_URL_MAP[key];
        
        // E2/AS1 and B1/AS1 are publicly hosted PDFs that can be embedded
        if (key === 'e2as1' || key === 'b1as1') {
            return {
                url: url,
                canEmbed: true,
                // Use Google Docs viewer for cross-platform PDF viewing
                viewerUrl: `https://docs.google.com/gview?embedded=true&url=${encodeURIComponent(url)}#page=${pageNum}`
            };
        }
        
        // NZS 3604 is a paid standard - can't embed directly
        return {
            url: url || '',
            canEmbed: false,
            viewerUrl: ''
        };
    };

    const pdfConfig = getPdfConfig();

    useEffect(() => {
        setCanEmbed(pdfConfig.canEmbed);
    }, [sourceKey]);

    // Open in external browser
    const handleOpenExternal = async () => {
        const url = INFO_URL_MAP[sourceKey] || pdfConfig.url;
        if (url) {
            await Linking.openURL(url);
        } else {
            Alert.alert('Error', 'No external link available for this document.');
        }
    };

    // Share the reference
    const handleShare = async () => {
        try {
            await Share.share({
                message: `STRYDA Citation Reference:\n\nSource: ${source}\nClause: ${clause}\nPage: ${page}\n\nView at: ${INFO_URL_MAP[sourceKey] || 'N/A'}`,
                title: `${source} - Clause ${clause}`,
            });
        } catch (err) {
            console.error('Share error:', err);
        }
    };

    // Render the info card for non-embeddable PDFs (like NZS 3604)
    const renderInfoCard = () => (
        <View style={styles.infoContainer}>
            <View style={styles.infoCard}>
                <View style={styles.iconContainer}>
                    <FileText size={48} color="#F97316" />
                </View>
                
                <Text style={styles.infoTitle}>Document Reference</Text>
                <Text style={styles.infoSubtitle}>{source}</Text>
                
                <View style={styles.detailsBox}>
                    <View style={styles.detailRow}>
                        <Text style={styles.detailLabel}>Clause:</Text>
                        <Text style={styles.detailValue}>{clause || 'N/A'}</Text>
                    </View>
                    <View style={styles.detailRow}>
                        <Text style={styles.detailLabel}>Page:</Text>
                        <Text style={styles.detailValue}>{page || 'N/A'}</Text>
                    </View>
                    <View style={styles.detailRow}>
                        <Text style={styles.detailLabel}>Section Page:</Text>
                        <Text style={styles.detailValue}>{pageNum}</Text>
                    </View>
                </View>

                <View style={styles.copyrightNotice}>
                    <AlertCircle size={16} color="#FCD34D" style={{ marginRight: 8 }} />
                    <Text style={styles.copyrightText}>
                        This is a copyrighted NZ Standard. A licensed copy is required for full access.
                    </Text>
                </View>

                <TouchableOpacity style={styles.primaryButton} onPress={handleOpenExternal}>
                    <ExternalLink size={18} color="#FFF" style={{ marginRight: 8 }} />
                    <Text style={styles.primaryButtonText}>View on Standards NZ</Text>
                </TouchableOpacity>

                <TouchableOpacity style={styles.secondaryButton} onPress={handleShare}>
                    <Share2 size={18} color="#F97316" style={{ marginRight: 8 }} />
                    <Text style={styles.secondaryButtonText}>Share Reference</Text>
                </TouchableOpacity>

                <Text style={styles.tipText}>
                    💡 If you have a licensed PDF copy, navigate to Clause {clause} on page {page}.
                </Text>
            </View>
        </View>
    );

    // Render WebView PDF viewer for embeddable PDFs
    const renderPdfViewer = () => (
        <View style={styles.webviewContainer}>
            {loading && (
                <View style={styles.loadingOverlay}>
                    <ActivityIndicator size="large" color="#F97316" />
                    <Text style={styles.loadingText}>Loading PDF...</Text>
                    <Text style={styles.loadingSubtext}>Jumping to page {pageNum}</Text>
                </View>
            )}
            
            <WebView
                ref={webViewRef}
                source={{ uri: pdfConfig.viewerUrl }}
                style={styles.webview}
                onLoadStart={() => setLoading(true)}
                onLoadEnd={() => setLoading(false)}
                onError={(e) => {
                    console.error('WebView error:', e.nativeEvent);
                    setError('Failed to load document. Try opening externally.');
                    setLoading(false);
                }}
                javaScriptEnabled={true}
                domStorageEnabled={true}
                startInLoadingState={true}
                scalesPageToFit={true}
                allowsInlineMediaPlayback={true}
            />

            {error && (
                <View style={styles.errorBanner}>
                    <AlertCircle size={16} color="#EF4444" />
                    <Text style={styles.errorText}>{error}</Text>
                    <TouchableOpacity onPress={handleOpenExternal}>
                        <Text style={styles.errorLink}>Open Externally</Text>
                    </TouchableOpacity>
                </View>
            )}
        </View>
    );

    return (
        <SafeAreaView style={styles.container} edges={['top']}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <ChevronLeft size={24} color="#FFF" />
                </TouchableOpacity>
                
                <View style={styles.headerInfo}>
                    <Text style={styles.headerTitle} numberOfLines={1}>{source}</Text>
                    <Text style={styles.headerSubtitle}>
                        {clause ? `Clause ${clause}` : ''}{clause && page ? ' • ' : ''}{page ? `Page ${page}` : ''}
                    </Text>
                </View>

                <View style={styles.headerActions}>
                    <TouchableOpacity onPress={handleShare} style={styles.headerButton}>
                        <Share2 size={20} color="#999" />
                    </TouchableOpacity>
                    <TouchableOpacity onPress={handleOpenExternal} style={styles.headerButton}>
                        <ExternalLink size={20} color="#F97316" />
                    </TouchableOpacity>
                </View>
            </View>

            {/* Page indicator */}
            <View style={styles.pageIndicator}>
                <BookOpen size={14} color="#666" />
                <Text style={styles.pageIndicatorText}>
                    Target: Page {pageNum} of {source}
                </Text>
            </View>

            {/* Content */}
            {canEmbed ? renderPdfViewer() : renderInfoCard()}
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
        paddingHorizontal: 12,
        paddingVertical: 12,
        backgroundColor: '#1A1A1A',
        borderBottomWidth: 1,
        borderBottomColor: '#333',
    },
    backButton: {
        padding: 8,
        marginRight: 4,
    },
    headerInfo: {
        flex: 1,
        marginRight: 8,
    },
    headerTitle: {
        color: '#FFF',
        fontSize: 15,
        fontWeight: 'bold',
    },
    headerSubtitle: {
        color: '#888',
        fontSize: 12,
        marginTop: 2,
    },
    headerActions: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    headerButton: {
        padding: 8,
        marginLeft: 4,
    },
    pageIndicator: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 8,
        backgroundColor: '#151515',
        borderBottomWidth: 1,
        borderBottomColor: '#252525',
    },
    pageIndicatorText: {
        color: '#666',
        fontSize: 12,
        marginLeft: 6,
    },
    // WebView styles
    webviewContainer: {
        flex: 1,
        backgroundColor: '#1A1A1A',
    },
    webview: {
        flex: 1,
        backgroundColor: '#1A1A1A',
    },
    loadingOverlay: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: '#0A0A0A',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 10,
    },
    loadingText: {
        color: '#FFF',
        fontSize: 16,
        marginTop: 16,
        fontWeight: '500',
    },
    loadingSubtext: {
        color: '#666',
        fontSize: 13,
        marginTop: 4,
    },
    errorBanner: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#1A0A0A',
        padding: 12,
        borderTopWidth: 1,
        borderTopColor: '#3A1A1A',
    },
    errorText: {
        color: '#EF4444',
        fontSize: 13,
        marginLeft: 8,
        flex: 1,
    },
    errorLink: {
        color: '#F97316',
        fontSize: 13,
        fontWeight: '600',
    },
    // Info card styles
    infoContainer: {
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
        borderColor: '#2A2A2A',
    },
    iconContainer: {
        width: 80,
        height: 80,
        borderRadius: 40,
        backgroundColor: '#F97316' + '15',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 16,
    },
    infoTitle: {
        color: '#FFF',
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    infoSubtitle: {
        color: '#888',
        fontSize: 14,
        marginBottom: 20,
    },
    detailsBox: {
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
        color: '#666',
        fontSize: 14,
    },
    detailValue: {
        color: '#FFF',
        fontSize: 14,
        fontWeight: '600',
    },
    copyrightNotice: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        backgroundColor: '#FCD34D' + '10',
        borderRadius: 8,
        padding: 12,
        marginBottom: 16,
        borderLeftWidth: 3,
        borderLeftColor: '#FCD34D',
    },
    copyrightText: {
        color: '#CCC',
        fontSize: 12,
        flex: 1,
        lineHeight: 18,
    },
    primaryButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#F97316',
        borderRadius: 12,
        paddingVertical: 14,
        paddingHorizontal: 20,
        width: '100%',
        marginBottom: 12,
    },
    primaryButtonText: {
        color: '#FFF',
        fontSize: 15,
        fontWeight: 'bold',
    },
    secondaryButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'transparent',
        borderRadius: 12,
        borderWidth: 1,
        borderColor: '#F97316',
        paddingVertical: 12,
        paddingHorizontal: 20,
        width: '100%',
        marginBottom: 16,
    },
    secondaryButtonText: {
        color: '#F97316',
        fontSize: 14,
        fontWeight: '600',
    },
    tipText: {
        color: '#555',
        fontSize: 12,
        textAlign: 'center',
        lineHeight: 18,
    },
});
