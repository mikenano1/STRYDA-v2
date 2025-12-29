// app/frontend/src/internal/utils/pdfMap.ts

/**
 * Maps compliance citations (e.g., "E2/AS1") to public PDF URLs.
 * Used by the WebView to display documents.
 */
export const getPdfUrl = (citationTitle: string | null): { url: string; title: string } | null => {
  if (!citationTitle) return null;

  const lowerTitle = citationTitle.toLowerCase();

  // 1. E2/AS1 (External Moisture)
  if (lowerTitle.includes('e2/as1') || lowerTitle.includes('e2')) {
    return {
      title: 'E2/AS1 (External Moisture)',
      url: 'https://codehub.building.govt.nz/assets/Approved-Documents/E2-External-moisture-3rd-edition-Amendment-10.pdf'
    };
  }

  // 2. NZS 3604 (Timber Framed Buildings)
  if (lowerTitle.includes('3604') || lowerTitle.includes('timber')) {
    return {
      title: 'NZS 3604:2011 (Selected Extracts)',
      url: 'https://www.building.govt.nz/assets/Uploads/building-code-compliance/b-stability/b1-structure/as1-nzs3604-2011-light-timber-framed-buildings.pdf'
    };
  }

  // 3. H1 (Energy Efficiency)
  if (lowerTitle.includes('h1') || lowerTitle.includes('energy')) {
    return {
      title: 'H1/AS1 (Energy Efficiency)',
      url: 'https://www.building.govt.nz/assets/Uploads/building-code-compliance/h-energy-efficiency/h1-energy-efficiency/as1-h1-energy-efficiency-5th-edition-amendment-1.pdf'
    };
  }

  return {
      title: citationTitle,
      url: 'https://codehub.building.govt.nz/'
  };
};
