# STRYDA-v2 Ingested Documents Audit

**Audit Date:** 2025-11-03 08:41:21
**Database:** Supabase PostgreSQL
**Table Used:** documents
**Total Documents:** 1742
**Total Chunks:** 1742

## Document Inventory

| Source | Chunks | Pages | Status |
|--------|--------|-------|--------|
| NZ Metal Roofing | 593 | 593 | ✅ Complete |
| NZS 3604:2011 | 449 | 449 | ✅ Complete |
| NZ Building Code | 224 | 224 | ✅ Complete |
| E2/AS1 | 196 | 196 | ✅ Complete |
| NZS 4229:2013 | 169 | 169 | ✅ Complete |
| B1 Amendment 13 | 88 | 88 | ✅ Complete |
| B1/AS1 | 21 | 21 | ✅ Complete |
| TEST_GUIDE | 1 | 1 | ⚠️ Incomplete |
| TEST_WIND | 1 | 1 | ⚠️ Incomplete |

## Corpus Statistics

- Total unique sources: 9
- Total chunks: 1742
- Average chunk length: 1956 characters
- Chunks with embeddings: 1740/1742 (99.9%)
- Average pages per document: 193.6

## Top Documents by Size

1. **NZ Metal Roofing** - 593 chunks, 593 pages
2. **NZS 3604:2011** - 449 chunks, 449 pages
3. **NZ Building Code** - 224 chunks, 224 pages
4. **E2/AS1** - 196 chunks, 196 pages
5. **NZS 4229:2013** - 169 chunks, 169 pages
6. **B1 Amendment 13** - 88 chunks, 88 pages
7. **B1/AS1** - 21 chunks, 21 pages
8. **TEST_GUIDE** - 1 chunks, 1 pages
9. **TEST_WIND** - 1 chunks, 1 pages

## Findings

- ✅ Complete documents: Documents with >10 chunks appear complete
- ⚠️ Incomplete/Missing: Some documents may have fewer chunks than expected
- 🔍 Database contains comprehensive NZ Building Code documentation

## Recommendations

1. Verify all expected NZ Building Code PDFs are present
2. Check for any duplicate entries
3. Ensure all documents have embeddings for vector search
4. Consider adding metadata for ingestion dates
