export const PDF_MAPPING: Record<string, string> = {
  "E2/AS1": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/e-moisture/e2-external-moisture/asvm/e2-external-moisture-3rd-edition-amendment-10.pdf",
  "NZS 3604": "https://www.standards.govt.nz/assets/Publication-files/NZS3604-2011-Light-timber-framed-buildings-Standard.pdf", // Note: Usually paywalled, using placeholder or finding a public reference if possible. For now, let's use a generic MBIE one or assume user has access. Actually, let's use a solid public one for testing.
  "B1/AS1": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/b-stability/b1-structure/asvm/b1-structure-amendment-20.pdf",
  "H1/AS1": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/h-energy-efficiency/h1-energy-efficiency/asvm/h1-energy-efficiency-5th-edition-amendment-1.pdf",
  "NZ Metal Roofing": "https://www.metalroofing.org.nz/assets/Code-of-Practice/MRm-Code-of-Practice-v3.0.pdf",
  // Fallback for testing
  "Default": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/e-moisture/e2-external-moisture/asvm/e2-external-moisture-3rd-edition-amendment-10.pdf"
};

export const getPdfUrl = (sourceName: string): string => {
  // Simple fuzzy match
  const key = Object.keys(PDF_MAPPING).find(k => sourceName.includes(k));
  return key ? PDF_MAPPING[key] : PDF_MAPPING["Default"];
};
