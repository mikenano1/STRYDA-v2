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
  Image,
} from 'react-native';
import { Colors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';
import Constants from 'expo-constants';
import { useRouter } from 'expo-router';

// Types for the hierarchical product system
interface Brand {
  id: string;
  name: string;
  logo?: string;
  productCount: number;
  categories: string[];
}

interface ProductCategory {
  id: string;
  name: string;
  icon: string;
  productCount: number;
  subcategories?: string[];
}

interface Trade {
  id: string;
  name: string;
  icon: string;
  color: string;
  brands: string[];
}

interface ProductDetails {
  id: string;
  name: string;
  brand: string;
  category: string;
  subcategory?: string;
  specifications: Record<string, string>;
  installGuides: string[];
  warranties: string[];
  complianceCodes: string[];
  images: string[];
  description: string;
}

// Additional types for search functionality
interface KnowledgeStats {
  total_documents: number;
  total_chunks: number;
  documents_by_type: {
    nzbc?: number;
    manufacturer?: number;
    nzs?: number;
    lbp?: number;
    eboss_product?: number;
  };
  recent_documents: Array<{
    title: string;
    type: string;
    processed_at: string;
  }>;
}

interface SearchResult {
  chunk_id: string;
  title: string;
  content: string;
  similarity_score: number;
  metadata: {
    section_title?: string;
    manufacturer?: string;
    tags?: string;
    source_url?: string;
    document_type: string;
    building_codes?: string[];
  };
}

interface ProductCard {
  id: string;
  title: string;
  brand: string;
  category: string;
  description?: string;
  sourceUrl?: string;
  tags: string[];
  buildingCodes: string[];
  specifications: string[];
  type: string;
  score?: number;
  savedAt?: string;
}

type ViewMode = 'trades' | 'brands' | 'brand-detail' | 'category-detail' | 'product-detail';

interface NavigationState {
  mode: ViewMode;
  selectedTrade?: string;
  selectedBrand?: string;
  selectedCategory?: string;
  selectedProduct?: string;
}

const BACKEND_URL = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;

// Type icons mapping
const typeIcons = {
  nzbc: 'doc.text.fill',
  manufacturer: 'building.2.fill',
  nzs: 'checkmark.seal.fill',
  lbp: 'person.badge.shield.checkmark.fill',
  eboss_product: 'cube.box.fill',
};

// Building code color mapping
const buildingCodeColors = {
  G5: '#10B981', // Green
  H1: '#F59E0B', // Amber
  E2: '#3B82F6', // Blue
  B1: '#EF4444', // Red
  F2: '#8B5CF6', // Purple
  C1: '#06B6D4', // Cyan
  G1: '#84CC16', // Lime
  A1: '#F97316', // Orange
  D1: '#EC4899', // Pink
  E1: '#6366F1', // Indigo
  default: '#6B7280', // Gray
};

// Trade categories for filtering
const TRADES: Trade[] = [
  { id: 'all', name: 'All Products', icon: 'square.grid.2x2', color: '#6B7280', brands: [] },
  { id: 'documents', name: 'Building Documents', icon: 'doc.text.fill', color: '#3B82F6', brands: [] },
  { id: 'carpentry', name: 'Carpentry', icon: 'hammer.fill', color: '#8B4513', brands: ['James Hardie', 'Carter Holt Harvey'] },
  { id: 'roofing', name: 'Roofing', icon: 'house.fill', color: '#DC2626', brands: ['Dimond', 'Metalcraft', 'Nuralite'] },
  { id: 'plumbing', name: 'Plumbing', icon: 'drop.fill', color: '#2563EB', brands: ['Rehau', 'Metabronze'] },
  { id: 'electrical', name: 'Electrical', icon: 'bolt.fill', color: '#F59E0B', brands: ['Schneider Electric', 'ABB'] },
  { id: 'drainlayer', name: 'Drainage', icon: 'water.waves', color: '#059669', brands: ['Marley', 'Iplex'] },
  { id: 'painting', name: 'Painting', icon: 'paintbrush.fill', color: '#7C3AED', brands: ['Resene', 'Dulux'] },
  { id: 'plastering', name: 'Plastering', icon: 'rectangle.fill', color: '#EC4899', brands: ['GIB', 'Winstone Wallboards'] },
  { id: 'glazing', name: 'Glazing', icon: 'rectangle.portrait', color: '#06B6D4', brands: ['Viridian', 'Metro Glass'] },
  { id: 'insulation', name: 'Insulation', icon: 'shield.fill', color: '#10B981', brands: ['Pink Batts', 'Kingspan'] },
];

// Product type categories
const PRODUCT_TYPES: ProductCategory[] = [
  { id: 'structural', name: 'Structural', icon: 'building.2.fill', productCount: 0 },
  { id: 'cladding', name: 'Cladding', icon: 'rectangle.stack.fill', productCount: 0 },
  { id: 'roofing', name: 'Roofing', icon: 'house.fill', productCount: 0 },
  { id: 'interior', name: 'Interior', icon: 'door.left.hand.closed', productCount: 0 },
  { id: 'exterior', name: 'Exterior', icon: 'house', productCount: 0 },
  { id: 'windows-doors', name: 'Windows & Doors', icon: 'rectangle.portrait.and.arrow.right', productCount: 0 },
  { id: 'hardware', name: 'Hardware', icon: 'wrench.and.screwdriver.fill', productCount: 0 },
  { id: 'insulation', name: 'Insulation', icon: 'shield.fill', productCount: 0 },
];

// Mock brand data - in real app this would come from backend
const SAMPLE_BRANDS: Brand[] = [
  {
    id: 'james-hardie',
    name: 'James Hardie',
    productCount: 11,
    categories: ['Cladding', 'Eaves/Soffits', 'Flooring', 'Pre-Clad', 'Interior'],
  },
  {
    id: 'dimond',
    name: 'Dimond',
    productCount: 32,
    categories: ['Roofing', 'Wall Cladding', 'Spouting', 'Accessories'],
  },
  {
    id: 'vantage',
    name: 'VANTAGE',
    productCount: 62,
    categories: ['Windows', 'Doors', 'Hardware', 'Accessories'],
  },
  {
    id: 'altherm',
    name: 'Altherm',
    productCount: 51,
    categories: ['Windows', 'Sliding Doors', 'Hinged Doors', 'Hardware'],
  },
  {
    id: 'resene',
    name: 'Resene',
    productCount: 29,
    categories: ['Interior Paint', 'Exterior Paint', 'Primers', 'Specialty Coatings'],
  },
  {
    id: 'kingspan',
    name: 'Kingspan',
    productCount: 14,
    categories: ['Wall Insulation', 'Roof Insulation', 'Underfloor', 'Specialty'],
  },
];

export default function LibraryScreen() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [navigation, setNavigation] = useState<NavigationState>({ mode: 'trades' });
  const [selectedFilterType, setSelectedFilterType] = useState<'trades' | 'types'>('trades');
  const [brands, setBrands] = useState<Brand[]>(SAMPLE_BRANDS);

  const navigateTo = (newNavigation: NavigationState) => {
    setNavigation(newNavigation);
  };

  const getBreadcrumbs = (): string[] => {
    const crumbs = ['Products'];
    
    if (navigation.selectedTrade && navigation.selectedTrade !== 'all') {
      const trade = TRADES.find(t => t.id === navigation.selectedTrade);
      if (trade) crumbs.push(trade.name);
    }
    
    if (navigation.selectedBrand) {
      const brand = brands.find(b => b.id === navigation.selectedBrand);
      if (brand) crumbs.push(brand.name);
    }
    
    if (navigation.selectedCategory) {
      crumbs.push(navigation.selectedCategory);
    }
    
    return crumbs;
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <View style={styles.titleContainer}>
        <Text style={styles.title}>Products</Text>
        <Text style={styles.subtitle}>
          {brands.reduce((sum, brand) => sum + brand.productCount, 0)} NZ building products
        </Text>
      </View>

      {/* Breadcrumbs */}
      {navigation.mode !== 'trades' && (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.breadcrumbs}>
          {getBreadcrumbs().map((crumb, index) => (
            <View key={index} style={styles.breadcrumbContainer}>
              {index > 0 && <Text style={styles.breadcrumbSeparator}>›</Text>}
              <TouchableOpacity
                onPress={() => {
                  if (index === 0) navigateTo({ mode: 'trades' });
                  // Add more navigation logic for other breadcrumb levels
                }}
              >
                <Text style={[
                  styles.breadcrumbText,
                  index === getBreadcrumbs().length - 1 && styles.breadcrumbTextActive
                ]}>
                  {crumb}
                </Text>
              </TouchableOpacity>
            </View>
          ))}
        </ScrollView>
      )}

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <IconSymbol name="house.fill" size={16} color={Colors.dark.icon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search brands or products..."
            placeholderTextColor={Colors.dark.placeholder}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>
      </View>
    </View>
  );

  const renderTradesView = () => (
    <View style={styles.content}>
      {/* Filter Type Toggle */}
      <View style={styles.filterToggle}>
        <TouchableOpacity
          style={[styles.filterToggleButton, selectedFilterType === 'trades' && styles.filterToggleButtonActive]}
          onPress={() => setSelectedFilterType('trades')}
        >
          <Text style={[styles.filterToggleText, selectedFilterType === 'trades' && styles.filterToggleTextActive]}>
            By Trade
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterToggleButton, selectedFilterType === 'types' && styles.filterToggleButtonActive]}
          onPress={() => setSelectedFilterType('types')}
        >
          <Text style={[styles.filterToggleText, selectedFilterType === 'types' && styles.filterToggleTextActive]}>
            By Product Type
          </Text>
        </TouchableOpacity>
      </View>

      {/* Categories Grid */}
      <ScrollView style={styles.categoriesContainer} showsVerticalScrollIndicator={false}>
        <View style={styles.categoriesGrid}>
          {(selectedFilterType === 'trades' ? TRADES : PRODUCT_TYPES).map((category) => (
            <TouchableOpacity
              key={category.id}
              style={[styles.categoryCard, { borderLeftColor: 'color' in category ? category.color : Colors.dark.tint }]}
              onPress={() => {
                if (selectedFilterType === 'trades') {
                  navigateTo({ 
                    mode: 'brands', 
                    selectedTrade: category.id 
                  });
                } else {
                  navigateTo({ 
                    mode: 'brands', 
                    selectedCategory: category.id 
                  });
                }
              }}
            >
              <View style={styles.categoryIconContainer}>
                <IconSymbol 
                  name={category.icon} 
                  size={32} 
                  color={'color' in category ? category.color : Colors.dark.tint} 
                />
              </View>
              <Text style={styles.categoryName}>{category.name}</Text>
              {'productCount' in category && (
                <Text style={styles.categoryCount}>{category.productCount} products</Text>
              )}
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );

  const renderBrandsView = () => {
    // Filter brands based on selected trade or category
    let filteredBrands = brands;
    
    if (navigation.selectedTrade && navigation.selectedTrade !== 'all') {
      const selectedTrade = TRADES.find(t => t.id === navigation.selectedTrade);
      if (selectedTrade?.brands.length > 0) {
        filteredBrands = brands.filter(brand => 
          selectedTrade.brands.some(tradeBrand => 
            brand.name.toLowerCase().includes(tradeBrand.toLowerCase())
          )
        );
      }
    }

    // Sort alphabetically
    filteredBrands.sort((a, b) => a.name.localeCompare(b.name));

    return (
      <View style={styles.content}>
        <ScrollView style={styles.brandsContainer} showsVerticalScrollIndicator={false}>
          <View style={styles.brandsGrid}>
            {filteredBrands.map((brand) => (
              <TouchableOpacity
                key={brand.id}
                style={styles.brandCard}
                onPress={() => navigateTo({ 
                  ...navigation,
                  mode: 'brand-detail', 
                  selectedBrand: brand.id 
                })}
              >
                <View style={styles.brandLogoContainer}>
                  {/* Placeholder for brand logo */}
                  <View style={styles.brandLogoPlaceholder}>
                    <Text style={styles.brandLogoText}>
                      {brand.name.split(' ').map(word => word[0]).join('').toUpperCase()}
                    </Text>
                  </View>
                </View>
                <View style={styles.brandInfo}>
                  <Text style={styles.brandName}>{brand.name}</Text>
                  <Text style={styles.brandProductCount}>
                    {brand.productCount} products
                  </Text>
                  <View style={styles.brandCategories}>
                    {brand.categories.slice(0, 2).map((category, index) => (
                      <View key={index} style={styles.categoryChip}>
                        <Text style={styles.categoryChipText}>{category}</Text>
                      </View>
                    ))}
                    {brand.categories.length > 2 && (
                      <Text style={styles.moreCategoriesText}>
                        +{brand.categories.length - 2} more
                      </Text>
                    )}
                  </View>
                </View>
                <IconSymbol name="chevron.right" size={20} color={Colors.dark.icon} />
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </View>
    );
  };

  const renderBrandDetailView = () => {
    const selectedBrand = brands.find(b => b.id === navigation.selectedBrand);
    if (!selectedBrand) return null;

    return (
      <View style={styles.content}>
        {/* Brand Header */}
        <View style={styles.brandHeader}>
          <View style={styles.brandHeaderLogo}>
            <View style={styles.brandLogoPlaceholder}>
              <Text style={styles.brandLogoText}>
                {selectedBrand.name.split(' ').map(word => word[0]).join('').toUpperCase()}
              </Text>
            </View>
          </View>
          <View style={styles.brandHeaderInfo}>
            <Text style={styles.brandHeaderName}>{selectedBrand.name}</Text>
            <Text style={styles.brandHeaderCount}>
              {selectedBrand.productCount} products in {selectedBrand.categories.length} categories
            </Text>
          </View>
        </View>

        {/* Product Categories */}
        <ScrollView style={styles.brandCategoriesContainer} showsVerticalScrollIndicator={false}>
          <Text style={styles.sectionTitle}>Product Categories</Text>
          {selectedBrand.categories.map((category, index) => (
            <TouchableOpacity
              key={index}
              style={styles.productCategoryCard}
              onPress={() => navigateTo({
                ...navigation,
                mode: 'category-detail',
                selectedCategory: category
              })}
            >
              <View style={styles.categoryIconContainer}>
                <IconSymbol 
                  name="folder.fill" 
                  size={24} 
                  color={Colors.dark.tint} 
                />
              </View>
              <View style={styles.categoryInfo}>
                <Text style={styles.categoryTitle}>{category}</Text>
                <Text style={styles.categorySubtitle}>
                  View all {selectedBrand.name} {category.toLowerCase()} products
                </Text>
              </View>
              <IconSymbol name="chevron.right" size={20} color={Colors.dark.icon} />
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    );
  };

  const renderCategoryDetailView = () => {
    const selectedBrand = brands.find(b => b.id === navigation.selectedBrand);
    if (!selectedBrand || !navigation.selectedCategory) return null;

    // In a real app, this would fetch products from the category
    // For now, we'll show a few sample products per category
    const categoryProducts = [
      {
        id: 'axon-panel',
        name: 'Axon Panel',
        description: 'High-performance fibre cement cladding panel with distinctive linear texture',
        specifications: ['15mm thickness', '2440mm length', 'R-value 0.5', 'Class 1 fire rating'],
        warranty: '25 years structural, 15 years paint finish',
        compliance: ['NZBC E2', 'NZBC B1', 'CodeMark certified'],
        installGuide: 'Available as PDF download',
        image: null,
      },
      {
        id: 'linea-weatherboard',
        name: 'Linea Weatherboard',
        description: 'Traditional weatherboard profile with modern fibre cement durability',
        specifications: ['18mm thickness', '3600mm length', 'Pre-primed finish', 'Impact resistant'],
        warranty: '25 years structural, 15 years paint finish',
        compliance: ['NZBC E2', 'NZBC B1', 'CodeMark certified'],
        installGuide: 'Available as PDF download',
        image: null,
      },
    ];

    return (
      <View style={styles.content}>
        {/* Category Header */}
        <View style={styles.categoryHeader}>
          <Text style={styles.categoryHeaderTitle}>
            {selectedBrand.name} {navigation.selectedCategory}
          </Text>
          <Text style={styles.categoryHeaderSubtitle}>
            {categoryProducts.length} products available
          </Text>
        </View>

        {/* Products List */}
        <ScrollView style={styles.categoryProductsContainer} showsVerticalScrollIndicator={false}>
          {categoryProducts.map((product) => (
            <TouchableOpacity
              key={product.id}
              style={styles.categoryProductCard}
              onPress={() => navigateTo({
                ...navigation,
                mode: 'product-detail',
                selectedProduct: product.id
              })}
            >
              <View style={styles.productImagePlaceholder}>
                <IconSymbol name="photo" size={32} color={Colors.dark.icon} />
              </View>
              
              <View style={styles.categoryProductInfo}>
                <Text style={styles.categoryProductName}>{product.name}</Text>
                <Text style={styles.categoryProductDescription} numberOfLines={2}>
                  {product.description}
                </Text>
                
                {/* Key Specifications */}
                <View style={styles.categoryProductSpecs}>
                  {product.specifications.slice(0, 2).map((spec, index) => (
                    <View key={index} style={styles.specBadge}>
                      <Text style={styles.specBadgeText}>{spec}</Text>
                    </View>
                  ))}
                </View>
                
                {/* Compliance Badges */}
                <View style={styles.categoryProductCompliance}>
                  {product.compliance.slice(0, 2).map((code, index) => (
                    <View key={index} style={styles.complianceBadge}>
                      <Text style={styles.complianceBadgeText}>{code}</Text>
                    </View>
                  ))}
                </View>
              </View>
              
              <IconSymbol name="chevron.right" size={20} color={Colors.dark.icon} />
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    );
  };

  const renderProductDetailView = () => {
    const selectedBrand = brands.find(b => b.id === navigation.selectedBrand);
    if (!selectedBrand || !navigation.selectedProduct) return null;

    // Mock product data - in real app this would come from EBOSS database
    const productData = {
      id: 'axon-panel',
      name: 'Axon Panel',
      brand: selectedBrand.name,
      category: navigation.selectedCategory || 'Cladding',
      description: 'High-performance fibre cement cladding panel featuring a distinctive linear texture that creates striking shadow lines. Engineered for durability and weather resistance in New Zealand conditions.',
      specifications: {
        'Thickness': '15mm',
        'Length': '2440mm',
        'Width': '1200mm',
        'Weight': '18.5 kg/m²',
        'Fire Rating': 'Group 1-S, 1-SD',
        'Impact Resistance': 'Severe duty',
        'Thermal Rating': 'R-value 0.5',
        'Moisture Movement': '<0.5%',
      },
      compliance: [
        { code: 'NZBC E2', description: 'External moisture compliance', status: 'certified' },
        { code: 'NZBC B1', description: 'Structural requirements', status: 'certified' },
        { code: 'CodeMark', description: 'Building product certification', status: 'certified' },
        { code: 'AS/NZS 2908.2', description: 'Cellulose-cement products', status: 'compliant' },
      ],
      warranty: {
        structural: '25 years',
        finish: '15 years paint system warranty',
        conditions: 'Subject to correct installation and maintenance'
      },
      installation: {
        guides: ['Installation Manual PDF', 'Fixing Schedule', 'Joint Details', 'Flashing Guide'],
        requirements: ['Licensed installer recommended', 'Minimum 6mm gap from ground', 'Use stainless steel fixings'],
        tools: ['Circular saw with fine-tooth blade', 'Drill', 'Measuring tools', 'Safety equipment']
      },
      sustainability: {
        recycled: '15% recycled content',
        carbon: 'Low embodied carbon',
        disposal: 'Recyclable at end of life'
      }
    };

    return (
      <View style={styles.content}>
        <ScrollView style={styles.productDetailContainer} showsVerticalScrollIndicator={false}>
          {/* Product Header */}
          <View style={styles.productDetailHeader}>
            <View style={styles.productDetailImageContainer}>
              <View style={styles.productDetailImagePlaceholder}>
                <IconSymbol name="photo" size={48} color={Colors.dark.icon} />
              </View>
            </View>
            
            <View style={styles.productDetailHeaderInfo}>
              <Text style={styles.productDetailName}>{productData.name}</Text>
              <Text style={styles.productDetailBrand}>{productData.brand}</Text>
              <Text style={styles.productDetailCategory}>{productData.category}</Text>
            </View>
            
            {/* Action Buttons */}
            <View style={styles.productDetailActions}>
              <TouchableOpacity 
                style={styles.chatWithAIButton}
                onPress={() => {
                  router.push({
                    pathname: '/chat',
                    params: { message: `I'm looking at ${productData.brand} ${productData.name}. Want me to source something specific for you for this product?` }
                  });
                }}
              >
                <IconSymbol name="message.fill" size={16} color={Colors.dark.background} />
                <Text style={styles.chatWithAIText}>Ask AI</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Description */}
          <View style={styles.productSection}>
            <Text style={styles.productSectionTitle}>Description</Text>
            <Text style={styles.productDescription}>{productData.description}</Text>
          </View>

          {/* Specifications */}
          <View style={styles.productSection}>
            <Text style={styles.productSectionTitle}>Technical Specifications</Text>
            <View style={styles.specificationsGrid}>
              {Object.entries(productData.specifications).map(([key, value]) => (
                <View key={key} style={styles.specificationRow}>
                  <Text style={styles.specificationLabel}>{key}</Text>
                  <Text style={styles.specificationValue}>{value}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Building Code Compliance */}
          <View style={styles.productSection}>
            <Text style={styles.productSectionTitle}>Building Code Compliance</Text>
            {productData.compliance.map((item, index) => (
              <View key={index} style={styles.complianceRow}>
                <View style={styles.complianceCodeContainer}>
                  <Text style={styles.complianceCode}>{item.code}</Text>
                  <View style={[styles.complianceStatus, 
                    item.status === 'certified' && styles.complianceStatusCertified
                  ]}>
                    <Text style={styles.complianceStatusText}>
                      {item.status.toUpperCase()}
                    </Text>
                  </View>
                </View>
                <Text style={styles.complianceDescription}>{item.description}</Text>
              </View>
            ))}
          </View>

          {/* Warranty Information */}
          <View style={styles.productSection}>
            <Text style={styles.productSectionTitle}>Warranty</Text>
            <View style={styles.warrantyContainer}>
              <View style={styles.warrantyRow}>
                <Text style={styles.warrantyLabel}>Structural:</Text>
                <Text style={styles.warrantyValue}>{productData.warranty.structural}</Text>
              </View>
              <View style={styles.warrantyRow}>
                <Text style={styles.warrantyLabel}>Finish:</Text>
                <Text style={styles.warrantyValue}>{productData.warranty.finish}</Text>
              </View>
              <Text style={styles.warrantyConditions}>{productData.warranty.conditions}</Text>
            </View>
          </View>

          {/* Installation Information */}
          <View style={styles.productSection}>
            <Text style={styles.productSectionTitle}>Installation</Text>
            
            <View style={styles.installationSubsection}>
              <Text style={styles.installationSubtitle}>Available Guides</Text>
              {productData.installation.guides.map((guide, index) => (
                <TouchableOpacity key={index} style={styles.installationGuideRow}>
                  <IconSymbol name="doc.text" size={16} color={Colors.dark.tint} />
                  <Text style={styles.installationGuideText}>{guide}</Text>
                  <IconSymbol name="arrow.down.circle" size={16} color={Colors.dark.icon} />
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.installationSubsection}>
              <Text style={styles.installationSubtitle}>Key Requirements</Text>
              {productData.installation.requirements.map((req, index) => (
                <View key={index} style={styles.requirementRow}>
                  <IconSymbol name="checkmark.circle.fill" size={16} color={Colors.dark.tint} />
                  <Text style={styles.requirementText}>{req}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* AI Guidance Section */}
          <TouchableOpacity 
            style={styles.aiGuidanceSection}
            onPress={() => {
              router.push({
                pathname: '/chat',
                params: { message: `I'm looking at ${productData.brand} ${productData.name}. Want me to source something specific for you for this product?` }
              });
            }}
          >
            <View style={styles.aiGuidanceHeader}>
              <IconSymbol name="message.badge.fill" size={24} color={Colors.dark.tint} />
              <View style={styles.aiGuidanceHeaderText}>
                <Text style={styles.aiGuidanceTitle}>Ask STRYDA Anything</Text>
                <Text style={styles.aiGuidanceSubtitle}>
                  Need help with this product? Ask me anything specific
                </Text>
              </View>
              <IconSymbol name="chevron.right" size={20} color={Colors.dark.icon} />
            </View>
          </TouchableOpacity>

        </ScrollView>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {renderHeader()}
      
      {navigation.mode === 'trades' && renderTradesView()}
      {navigation.mode === 'brands' && renderBrandsView()}
      {navigation.mode === 'brand-detail' && renderBrandDetailView()}
      {navigation.mode === 'category-detail' && renderCategoryDetailView()}
      {navigation.mode === 'product-detail' && renderProductDetailView()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.dark.background,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.dark.border,
  },
  titleContainer: {
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: Colors.dark.text,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: Colors.dark.icon,
  },
  breadcrumbs: {
    marginBottom: 12,
  },
  breadcrumbContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 8,
  },
  breadcrumbSeparator: {
    fontSize: 16,
    color: Colors.dark.icon,
    marginHorizontal: 8,
  },
  breadcrumbText: {
    fontSize: 14,
    color: Colors.dark.icon,
    fontWeight: '500',
  },
  breadcrumbTextActive: {
    color: Colors.dark.tint,
    fontWeight: '600',
  },
  searchContainer: {
    marginTop: 8,
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
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  filterToggle: {
    flexDirection: 'row',
    backgroundColor: Colors.dark.surface,
    borderRadius: 8,
    padding: 4,
    marginVertical: 16,
  },
  filterToggleButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
  },
  filterToggleButtonActive: {
    backgroundColor: Colors.dark.tint,
  },
  filterToggleText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.dark.icon,
  },
  filterToggleTextActive: {
    color: Colors.dark.background,
  },
  categoriesContainer: {
    flex: 1,
  },
  categoriesGrid: {
    gap: 16,
  },
  categoryCard: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 16,
    padding: 20,
    borderLeftWidth: 4,
    borderColor: Colors.dark.border,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  categoryIconContainer: {
    marginBottom: 12,
  },
  categoryName: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.dark.text,
    marginBottom: 4,
  },
  categoryCount: {
    fontSize: 14,
    color: Colors.dark.icon,
  },
  brandsContainer: {
    flex: 1,
    paddingTop: 16,
  },
  brandsGrid: {
    gap: 16,
  },
  brandCard: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 16,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.dark.border,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  brandLogoContainer: {
    marginRight: 16,
  },
  brandLogoPlaceholder: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: Colors.dark.tint,
    alignItems: 'center',
    justifyContent: 'center',
  },
  brandLogoText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.dark.background,
  },
  brandInfo: {
    flex: 1,
  },
  brandName: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.dark.text,
    marginBottom: 4,
  },
  brandProductCount: {
    fontSize: 14,
    color: Colors.dark.icon,
    marginBottom: 8,
  },
  brandCategories: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  categoryChip: {
    backgroundColor: Colors.dark.inputBackground,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  categoryChipText: {
    fontSize: 11,
    color: Colors.dark.text,
    fontWeight: '500',
  },
  moreCategoriesText: {
    fontSize: 11,
    color: Colors.dark.placeholder,
    fontStyle: 'italic',
    alignSelf: 'center',
  },
  brandHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.dark.surface,
    borderRadius: 16,
    padding: 20,
    marginTop: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  brandHeaderLogo: {
    marginRight: 20,
  },
  brandHeaderInfo: {
    flex: 1,
  },
  brandHeaderName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.dark.text,
    marginBottom: 4,
  },
  brandHeaderCount: {
    fontSize: 16,
    color: Colors.dark.icon,
  },
  brandCategoriesContainer: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.dark.text,
    marginBottom: 16,
  },
  productCategoryCard: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  categoryInfo: {
    flex: 1,
    marginLeft: 16,
  },
  categoryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.text,
    marginBottom: 4,
  },
  categorySubtitle: {
    fontSize: 14,
    color: Colors.dark.icon,
  },
  // Category Detail View Styles
  categoryHeader: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 16,
    padding: 20,
    marginTop: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  categoryHeaderTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.dark.text,
    marginBottom: 4,
  },
  categoryHeaderSubtitle: {
    fontSize: 16,
    color: Colors.dark.icon,
  },
  categoryProductsContainer: {
    flex: 1,
  },
  categoryProductCard: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.dark.border,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  productImagePlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 8,
    backgroundColor: Colors.dark.inputBackground,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  categoryProductInfo: {
    flex: 1,
  },
  categoryProductName: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.dark.text,
    marginBottom: 4,
  },
  categoryProductDescription: {
    fontSize: 14,
    color: Colors.dark.icon,
    lineHeight: 20,
    marginBottom: 8,
  },
  categoryProductSpecs: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 8,
  },
  specBadge: {
    backgroundColor: Colors.dark.tint + '20',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  specBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.dark.tint,
  },
  categoryProductCompliance: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  complianceBadge: {
    backgroundColor: '#10B981' + '20',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  complianceBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#10B981',
  },
  // Product Detail View Styles
  productDetailContainer: {
    flex: 1,
  },
  productDetailHeader: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 16,
    padding: 20,
    marginTop: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: Colors.dark.border,
    flexDirection: 'row',
    alignItems: 'center',
  },
  productDetailImageContainer: {
    marginRight: 20,
  },
  productDetailImagePlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 12,
    backgroundColor: Colors.dark.inputBackground,
    alignItems: 'center',
    justifyContent: 'center',
  },
  productDetailHeaderInfo: {
    flex: 1,
  },
  productDetailName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.dark.text,
    marginBottom: 4,
  },
  productDetailBrand: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.tint,
    marginBottom: 4,
  },
  productDetailCategory: {
    fontSize: 14,
    color: Colors.dark.icon,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  productDetailActions: {
    alignItems: 'flex-end',
  },
  chatWithAIButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: Colors.dark.tint,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
  },
  chatWithAIText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.dark.background,
  },
  productSection: {
    marginBottom: 32,
  },
  productSectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.dark.text,
    marginBottom: 16,
  },
  productDescription: {
    fontSize: 16,
    color: Colors.dark.text,
    lineHeight: 24,
  },
  specificationsGrid: {
    gap: 12,
  },
  specificationRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: Colors.dark.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  specificationLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.dark.text,
    flex: 1,
  },
  specificationValue: {
    fontSize: 14,
    color: Colors.dark.tint,
    fontWeight: '500',
  },
  complianceRow: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  complianceCodeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  complianceCode: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.dark.text,
    marginRight: 12,
  },
  complianceStatus: {
    backgroundColor: Colors.dark.inputBackground,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  complianceStatusCertified: {
    backgroundColor: '#10B981' + '20',
  },
  complianceStatusText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#10B981',
  },
  complianceDescription: {
    fontSize: 14,
    color: Colors.dark.icon,
    lineHeight: 20,
  },
  warrantyContainer: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  warrantyRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  warrantyLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.dark.text,
  },
  warrantyValue: {
    fontSize: 14,
    color: Colors.dark.tint,
    fontWeight: '500',
  },
  warrantyConditions: {
    fontSize: 12,
    color: Colors.dark.icon,
    marginTop: 8,
    fontStyle: 'italic',
  },
  installationSubsection: {
    marginBottom: 20,
  },
  installationSubtitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.text,
    marginBottom: 12,
  },
  installationGuideRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: Colors.dark.surface,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  installationGuideText: {
    flex: 1,
    fontSize: 14,
    color: Colors.dark.text,
    marginHorizontal: 12,
  },
  requirementRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 8,
    gap: 12,
  },
  requirementText: {
    flex: 1,
    fontSize: 14,
    color: Colors.dark.text,
    lineHeight: 20,
  },
  aiGuidanceSection: {
    backgroundColor: Colors.dark.tint + '10',
    borderRadius: 16,
    padding: 20,
    borderWidth: 2,
    borderColor: Colors.dark.tint + '30',
    marginBottom: 24,
  },
  aiGuidanceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  aiGuidanceHeaderText: {
    flex: 1,
    marginHorizontal: 16,
  },
  aiGuidanceTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.dark.text,
    marginBottom: 4,
  },
  aiGuidanceSubtitle: {
    fontSize: 14,
    color: Colors.dark.icon,
    lineHeight: 20,
  },
});