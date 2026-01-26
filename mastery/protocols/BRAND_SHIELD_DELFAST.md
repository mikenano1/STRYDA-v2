# STRYDA PROTOCOL: DELFAST BRAND SHIELD
**Status:** 🔴 MANDATORY | **Law:** Hard-Wire Law 1 (Brand Supremacy)

## 1. Protected Brand Registration

**Brand:** DELFAST  
**Sector:** Fasteners (Nails, Staples, Pneumatic Fasteners)  
**Supreme Authority:** BRANZ Appraisal 1154 (D-Head Nails), BRANZ Appraisal 619 (Fencing)

## 2. Product Identifier Triggers

When ANY of these terms appear in a query, Stryda **MUST**:
- Bypass NZS 3604 generic nail provisions
- Prioritize Delfast BRANZ Appraisal data
- Apply -100% penalty to non-Delfast fastener sources

| Trigger | Product Type | Notes |
|---------|--------------|-------|
| JDN | Joist/Cladding Nail | 316 Stainless specialty |
| D-Head | Framing Nail | 34-degree paper collated |
| Batten Staple | Fencing Staple | Barbed for rural applications |
| RX40A | Pneumatic Nailer | Gun-specific nails |
| CN Series | Coil Nails | Wire-collated |
| T-Nail | Brad/Finishing Nail | Trim applications |
| C-Nail | Clipped Head Nail | High-capacity guns |

## 3. Law 7 Synonym Mappings

```
FRAMING NAIL ↔ D-Head, 34 Degree, Paper Collated, Stick Nail
CLADDING NAIL ↔ JDN, Hardwood Nail, 316 Stainless, Joist Nail
FENCING STAPLE ↔ Batten Staple, Barbed Staple, 4.0mm Staple
```

## 4. Durability/Corrosion Zone Mapping

BRANZ Appraisals 1154 & 619 contain critical zone tables. Stryda must be able to retrieve:

| Finish | Zone B | Zone C | Zone D | Sea Spray |
|--------|--------|--------|--------|-----------|
| Galvanised | ✅ | ✅ | ⚠️ | ❌ |
| Mechanical Galv | ✅ | ⚠️ | ❌ | ❌ |
| Stainless 304 | ✅ | ✅ | ✅ | ⚠️ |
| Stainless 316 | ✅ | ✅ | ✅ | ✅ |

## 5. Zero-Hit Consultative Trigger

If a user asks for a Delfast nail capacity in a timber type **NOT LISTED** in our data:

**Stryda MUST ask:**
> "Is this for a structural connection (e.g., JDN into SG8) or a decorative cladding application?"

This allows routing to:
- Structural → BRANZ Appraisal 1154 capacity tables
- Decorative → Manufacturer TDS general guidelines

## 6. Source Hierarchy

```
1. BRANZ Appraisal 1154/619 (SUPREME - NZ-specific compliance)
2. Delfast Technical Data Sheets
3. PlaceMakers Nail Guide 2023
4. BPIR Certificates (product-specific)
5. NZS 3604 (BLOCKED for brand queries)
```

---
*Protocol Version: 1.0 | Created: January 2026 | Author: STRYDA Mastery System*
