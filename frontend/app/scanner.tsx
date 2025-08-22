import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  ScrollView,
  Dimensions,
} from 'react-native';
import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { createWorker } from 'tesseract.js';
import { router } from 'expo-router';
import { Colors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';
import Constants from 'expo-constants';

interface ScannedProduct {
  text: string;
  confidence: number;
  productMatches: ProductMatch[];
  complianceInfo?: string[];
}

interface ProductMatch {
  title: string;
  brand: string;
  category: string;
  confidence: number;
  ebossUrl?: string;
  specifications?: Record<string, string>;
}

const BACKEND_URL = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;

export default function ScannerScreen() {
  const [facing, setFacing] = useState<CameraType>('back');
  const [permission, requestPermission] = useCameraPermissions();
  const [isScanning, setIsScanning] = useState(false);
  const [scannedData, setScannedData] = useState<ScannedProduct | null>(null);
  const [ocrWorker, setOcrWorker] = useState<any>(null);
  const cameraRef = useRef<CameraView>(null);

  // Initialize OCR worker
  useEffect(() => {
    const initOCR = async () => {
      try {
        const worker = await createWorker('eng');
        setOcrWorker(worker);
      } catch (error) {
        console.error('Failed to initialize OCR:', error);
      }
    };

    initOCR();

    return () => {
      if (ocrWorker) {
        ocrWorker.terminate();
      }
    };
  }, []);

  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <View style={styles.permissionContainer}>
          <IconSymbol name="camera.fill" size={64} color={Colors.dark.icon} />
          <Text style={styles.permissionTitle}>Camera Access Required</Text>
          <Text style={styles.permissionMessage}>
            STRYDA needs camera access to scan product labels and barcodes for instant specifications.
          </Text>
          <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
            <Text style={styles.permissionButtonText}>Enable Camera</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const takePicture = async () => {
    if (!cameraRef.current || !ocrWorker) {
      Alert.alert('Error', 'Camera or OCR not ready');
      return;
    }

    try {
      setIsScanning(true);
      
      // Take photo
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        skipProcessing: false,
      });

      if (photo?.uri) {
        await processImage(photo.uri);
      }
    } catch (error) {
      console.error('Error taking picture:', error);
      Alert.alert('Error', 'Failed to take picture');
      setIsScanning(false);
    }
  };

  const pickImage = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]?.uri) {
        setIsScanning(true);
        await processImage(result.assets[0].uri);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to select image');
    }
  };

  const processImage = async (imageUri: string) => {
    try {
      if (!ocrWorker) {
        throw new Error('OCR worker not initialized');
      }

      // Perform OCR on the image
      const { data: { text, confidence } } = await ocrWorker.recognize(imageUri);
      
      if (!text.trim()) {
        Alert.alert('No Text Found', 'No readable text was detected in the image. Try taking another photo with better lighting.');
        setIsScanning(false);
        return;
      }

      // Process extracted text to find product matches
      const productMatches = await searchProducts(text);
      
      // Get compliance information if products found
      const complianceInfo = productMatches.length > 0 
        ? await getComplianceInfo(productMatches) 
        : [];

      setScannedData({
        text: text.trim(),
        confidence,
        productMatches,
        complianceInfo,
      });

    } catch (error) {
      console.error('Error processing image:', error);
      Alert.alert('Processing Error', 'Failed to process the image. Please try again.');
    } finally {
      setIsScanning(false);
    }
  };

  const searchProducts = async (text: string): Promise<ProductMatch[]> => {
    try {
      // Extract potential product information from OCR text
      const searchTerms = extractProductInfo(text);
      
      if (searchTerms.length === 0) {
        return [];
      }

      // Search EBOSS database for matches
      const promises = searchTerms.slice(0, 3).map(async (term) => {
        try {
          const response = await fetch(`${BACKEND_URL}/api/products/search?query=${encodeURIComponent(term)}&limit=3`);
          if (response.ok) {
            const data = await response.json();
            return data.results || [];
          }
        } catch (error) {
          console.error('Product search error:', error);
        }
        return [];
      });

      const searchResults = await Promise.all(promises);
      const allMatches = searchResults.flat();

      // Convert to ProductMatch format and deduplicate
      const productMatches: ProductMatch[] = [];
      const seen = new Set();

      for (const result of allMatches) {
        const key = `${result.title}-${result.brand}`;
        if (!seen.has(key)) {
          seen.add(key);
          productMatches.push({
            title: result.title || 'Unknown Product',
            brand: result.brand || 'Unknown Brand',
            category: result.category || 'General',
            confidence: result.confidence || 0.5,
            ebossUrl: result.url,
            specifications: result.specifications || {},
          });
        }
      }

      return productMatches.slice(0, 5); // Limit to top 5 matches
    } catch (error) {
      console.error('Error searching products:', error);
      return [];
    }
  };

  const extractProductInfo = (text: string): string[] => {
    const terms: string[] = [];
    const lines = text.split('\n').map(line => line.trim()).filter(Boolean);
    
    for (const line of lines) {
      // Extract brand names (common NZ building brands)
      const brands = ['James Hardie', 'GIB', 'Pink Batts', 'Resene', 'Kingspan', 'Dimond', 'Metalcraft', 'Altherm', 'First Windows'];
      for (const brand of brands) {
        if (line.toLowerCase().includes(brand.toLowerCase())) {
          terms.push(brand);
          terms.push(line); // Include the full line with brand
        }
      }
      
      // Extract model numbers (alphanumeric patterns)
      const modelMatch = line.match(/\b[A-Z0-9]{2,}[-_]?[A-Z0-9]*\b/g);
      if (modelMatch) {
        terms.push(...modelMatch);
      }
      
      // Extract R-values for insulation
      const rValueMatch = line.match(/R[-\s]?(\d+\.?\d*)/i);
      if (rValueMatch) {
        terms.push(`R${rValueMatch[1]} insulation`);
      }
      
      // Extract product categories
      const categories = ['insulation', 'cladding', 'roofing', 'plasterboard', 'timber', 'steel', 'concrete'];
      for (const category of categories) {
        if (line.toLowerCase().includes(category)) {
          terms.push(category);
        }
      }
      
      // Include lines that look like product names (title case, reasonable length)
      if (line.length > 5 && line.length < 50 && /^[A-Z]/.test(line)) {
        terms.push(line);
      }
    }
    
    return [...new Set(terms)]; // Remove duplicates
  };

  const getComplianceInfo = async (products: ProductMatch[]): Promise<string[]> => {
    try {
      if (products.length === 0) return [];
      
      const productQuery = products.map(p => `${p.brand} ${p.title}`).join(', ');
      
      const response = await fetch(`${BACKEND_URL}/api/chat/enhanced`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `What are the building code compliance requirements for: ${productQuery}?`,
          session_id: 'ocr_scanner',
          enable_compliance_analysis: true,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        return data.compliance_issues?.map((issue: any) => 
          `${issue.code_reference}: ${issue.description}`
        ) || [];
      }
    } catch (error) {
      console.error('Error getting compliance info:', error);
    }
    return [];
  };

  const retryScanning = () => {
    setScannedData(null);
    setIsScanning(false);
  };

  const searchProductInChat = (productTitle: string) => {
    router.push({
      pathname: '/chat',
      params: { message: `Tell me about ${productTitle} specifications and installation requirements` }
    });
  };

  function toggleCameraFacing() {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  }

  if (scannedData) {
    return (
      <View style={styles.container}>
        <ScrollView style={styles.resultsContainer} contentContainerStyle={styles.resultsContent}>
          {/* Header */}
          <View style={styles.resultsHeader}>
            <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
              <IconSymbol name="chevron.left" size={20} color={Colors.dark.text} />
            </TouchableOpacity>
            <Text style={styles.resultsTitle}>Scan Results</Text>
            <TouchableOpacity onPress={retryScanning} style={styles.retryButton}>
              <IconSymbol name="camera.fill" size={20} color={Colors.dark.tint} />
            </TouchableOpacity>
          </View>

          {/* OCR Results */}
          <View style={styles.ocrSection}>
            <Text style={styles.sectionTitle}>Detected Text</Text>
            <Text style={styles.ocrText}>{scannedData.text}</Text>
            <Text style={styles.confidenceText}>
              Confidence: {Math.round(scannedData.confidence)}%
            </Text>
          </View>

          {/* Product Matches */}
          {scannedData.productMatches.length > 0 && (
            <View style={styles.productsSection}>
              <Text style={styles.sectionTitle}>Product Matches</Text>
              {scannedData.productMatches.map((product, index) => (
                <TouchableOpacity 
                  key={index} 
                  style={styles.productCard}
                  onPress={() => searchProductInChat(product.title)}
                >
                  <View style={styles.productHeader}>
                    <Text style={styles.productTitle}>{product.title}</Text>
                    <Text style={styles.productBrand}>{product.brand}</Text>
                  </View>
                  <Text style={styles.productCategory}>{product.category}</Text>
                  <View style={styles.productFooter}>
                    <Text style={styles.productConfidence}>
                      {Math.round(product.confidence * 100)}% match
                    </Text>
                    <IconSymbol name="chevron.right" size={16} color={Colors.dark.icon} />
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          )}

          {/* Compliance Information */}
          {scannedData.complianceInfo && scannedData.complianceInfo.length > 0 && (
            <View style={styles.complianceSection}>
              <Text style={styles.sectionTitle}>Compliance Requirements</Text>
              {scannedData.complianceInfo.map((info, index) => (
                <View key={index} style={styles.complianceItem}>
                  <IconSymbol name="checkmark.seal.fill" size={16} color={Colors.dark.tint} />
                  <Text style={styles.complianceText}>{info}</Text>
                </View>
              ))}
            </View>
          )}

          {/* No Results */}
          {scannedData.productMatches.length === 0 && (
            <View style={styles.noResultsSection}>
              <IconSymbol name="questionmark.circle.fill" size={48} color={Colors.dark.icon} />
              <Text style={styles.noResultsTitle}>No Product Matches</Text>
              <Text style={styles.noResultsText}>
                No products were found matching the scanned text. Try scanning a clearer image of the product label or barcode.
              </Text>
              <TouchableOpacity style={styles.chatButton} onPress={() => searchProductInChat(scannedData.text)}>
                <Text style={styles.chatButtonText}>Ask STRYDA AI</Text>
                <IconSymbol name="message.fill" size={16} color={Colors.dark.background} />
              </TouchableOpacity>
            </View>
          )}
        </ScrollView>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Camera View */}
      <CameraView style={styles.camera} facing={facing} ref={cameraRef}>
        {/* Header Controls */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.headerButton} onPress={() => router.back()}>
            <IconSymbol name="xmark" size={24} color="white" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Product Scanner</Text>
          <TouchableOpacity style={styles.headerButton} onPress={toggleCameraFacing}>
            <IconSymbol name="camera.rotate" size={24} color="white" />
          </TouchableOpacity>
        </View>

        {/* Scanning Frame */}
        <View style={styles.scanningFrame}>
          <View style={styles.frameCorner} />
          <View style={[styles.frameCorner, styles.frameCornerTopRight]} />
          <View style={[styles.frameCorner, styles.frameCornerBottomLeft]} />
          <View style={[styles.frameCorner, styles.frameCornerBottomRight]} />
          
          <Text style={styles.scanningText}>
            Align product label or barcode within the frame
          </Text>
        </View>

        {/* Bottom Controls */}
        <View style={styles.bottomControls}>
          <TouchableOpacity style={styles.galleryButton} onPress={pickImage}>
            <IconSymbol name="photo" size={24} color="white" />
            <Text style={styles.buttonText}>Gallery</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.captureButton, isScanning && styles.captureButtonDisabled]} 
            onPress={takePicture}
            disabled={isScanning}
          >
            {isScanning ? (
              <ActivityIndicator size="large" color="white" />
            ) : (
              <IconSymbol name="camera.fill" size={32} color="white" />
            )}
          </TouchableOpacity>

          <TouchableOpacity style={styles.helpButton} onPress={() => {
            Alert.alert(
              'Scanner Help',
              'Position the product label or barcode within the frame. Ensure good lighting and avoid shadows. The scanner works best with clear, unobstructed text.',
              [{ text: 'Got it', style: 'default' }]
            );
          }}>
            <IconSymbol name="questionmark.circle" size={24} color="white" />
            <Text style={styles.buttonText}>Help</Text>
          </TouchableOpacity>
        </View>
      </CameraView>
    </View>
  );
}

const { width, height } = Dimensions.get('window');

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.dark.background,
  },
  camera: {
    flex: 1,
  },
  permissionContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
  },
  permissionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.dark.text,
    marginTop: 20,
    marginBottom: 12,
    textAlign: 'center',
  },
  permissionMessage: {
    fontSize: 16,
    color: Colors.dark.icon,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  permissionButton: {
    backgroundColor: Colors.dark.tint,
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
  },
  permissionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 60,
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  headerButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: 'white',
  },
  scanningFrame: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  frameCorner: {
    position: 'absolute',
    width: 30,
    height: 30,
    borderLeftWidth: 4,
    borderTopWidth: 4,
    borderColor: Colors.dark.tint,
    top: -100,
    left: width / 2 - 120,
  },
  frameCornerTopRight: {
    borderLeftWidth: 0,
    borderRightWidth: 4,
    right: width / 2 - 120,
    left: 'auto' as any,
  },
  frameCornerBottomLeft: {
    borderTopWidth: 0,
    borderBottomWidth: 4,
    bottom: -100,
    top: 'auto' as any,
  },
  frameCornerBottomRight: {
    borderLeftWidth: 0,
    borderTopWidth: 0,
    borderRightWidth: 4,
    borderBottomWidth: 4,
    bottom: -100,
    right: width / 2 - 120,
    left: 'auto' as any,
    top: 'auto' as any,
  },
  scanningText: {
    fontSize: 16,
    color: 'white',
    textAlign: 'center',
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 120,
  },
  bottomControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 40,
    paddingBottom: 60,
  },
  galleryButton: {
    alignItems: 'center',
    gap: 4,
  },
  helpButton: {
    alignItems: 'center',
    gap: 4,
  },
  buttonText: {
    fontSize: 12,
    color: 'white',
    fontWeight: '500',
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.dark.tint,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 4,
    borderColor: 'white',
  },
  captureButtonDisabled: {
    opacity: 0.7,
  },
  // Results Screen Styles
  resultsContainer: {
    flex: 1,
  },
  resultsContent: {
    padding: 20,
  },
  resultsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  backButton: {
    padding: 8,
  },
  retryButton: {
    padding: 8,
  },
  resultsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.dark.text,
  },
  ocrSection: {
    backgroundColor: Colors.dark.surface,
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.text,
    marginBottom: 12,
  },
  ocrText: {
    fontSize: 14,
    color: Colors.dark.text,
    lineHeight: 20,
    marginBottom: 8,
  },
  confidenceText: {
    fontSize: 12,
    color: Colors.dark.icon,
  },
  productsSection: {
    marginBottom: 20,
  },
  productCard: {
    backgroundColor: Colors.dark.surface,
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  productHeader: {
    marginBottom: 8,
  },
  productTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.text,
    marginBottom: 4,
  },
  productBrand: {
    fontSize: 14,
    color: Colors.dark.tint,
    fontWeight: '500',
  },
  productCategory: {
    fontSize: 12,
    color: Colors.dark.icon,
    marginBottom: 12,
  },
  productFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  productConfidence: {
    fontSize: 12,
    color: Colors.dark.icon,
  },
  complianceSection: {
    marginBottom: 20,
  },
  complianceItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: Colors.dark.surface,
    borderRadius: 8,
    marginBottom: 8,
  },
  complianceText: {
    flex: 1,
    fontSize: 14,
    color: Colors.dark.text,
    lineHeight: 20,
  },
  noResultsSection: {
    alignItems: 'center',
    padding: 40,
  },
  noResultsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.dark.text,
    marginTop: 16,
    marginBottom: 8,
  },
  noResultsText: {
    fontSize: 14,
    color: Colors.dark.icon,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24,
  },
  chatButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: Colors.dark.tint,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  chatButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.dark.background,
  },
});