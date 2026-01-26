# ⚓ HILTI GROUP EFFECTS PROTOCOL
**Version:** 1.0
**Status:** PRE-FLIGHT READY
**Location:** `/app/mastery/protocols/hilti_group_effects.md`

---

## 📐 THE CHALLENGE

Hilti anchors are typically installed in **groups** (4, 6, or more anchors in a baseplate). The total capacity is NOT simply `Single × Count` because of:

1. **Concrete Cone Overlap** - Adjacent anchors share failure cones
2. **Edge Effects** - Reduced capacity near edges
3. **Spacing Effects** - Too-close anchors reduce capacity
4. **Group Factor (Ag/Ag0)** - The reduction multiplier

---

## 🧮 HILTI GROUP CAPACITY FORMULA

```
Ngroup = Nsingle × n × (Ag/Ag0) × ψs × ψec × ψre × ψM
```

Where:
- `Nsingle` = Single anchor capacity
- `n` = Number of anchors
- `Ag/Ag0` = Projected area ratio (group factor)
- `ψs` = Edge distance factor
- `ψec` = Eccentricity factor
- `ψre` = Reinforcement factor
- `ψM` = Material factor

---

## 📊 COMMON GROUP CONFIGURATIONS

### 4-Anchor Baseplate (Standard Column Base)

```
  o     o
  
  o     o
```

**Typical Spacing:** 150-200mm
**Typical Edge:** 75-100mm

| Spacing | Edge | Group Factor |
|---------|------|--------------|
| 150mm | 75mm | 0.65 |
| 150mm | 100mm | 0.75 |
| 200mm | 100mm | 0.85 |
| 200mm | 150mm | 0.95 |

### 6-Anchor Baseplate (Heavy Column)

```
  o   o   o
  
  o   o   o
```

**Group Factor Range:** 0.50 - 0.80

### 2-Anchor (Hold-down/Bracket)

```
  o     o
```

**Group Factor Range:** 0.80 - 0.95

---

## 🏷️ HILTI PRODUCT LINES

### Chemical Anchors (Adhesive)
| Product | Substrate | Typical Tension (M12) | Notes |
|---------|-----------|----------------------|-------|
| HIT-HY 200-R | Concrete | 25-40 kN | Most common |
| HIT-HY 200-A | Concrete | 30-45 kN | High performance |
| HIT-RE 500 V4 | Concrete | 35-50 kN | Seismic rated |

### Mechanical Anchors
| Product | Substrate | Typical Tension (M12) | Notes |
|---------|-----------|----------------------|-------|
| HST3 | Cracked concrete | 15-25 kN | Through-bolt |
| HSL-3 | Cracked concrete | 20-35 kN | Heavy duty |
| HUS-HR | Masonry | 8-15 kN | Screw anchor |
| Kwik Bolt TZ | Concrete | 18-30 kN | Wedge anchor |

---

## 💬 STRYDA RESPONSE TEMPLATE (Group Queries)

When user asks about multiple Hilti anchors:

```
**Single [Product] Capacity:** [X] kN tension / [Y] kN shear
(Source: Hilti Technical Data, [Concrete/Masonry], f'c = [X] MPa)

**For [N]-Anchor Group:**
- Base: [N] × [X] kN = [Total] kN
- Group Factor (Ag/Ag0): ~[0.XX] (based on [spacing]mm spacing, [edge]mm edge)
- **Reduced Capacity:** [Total] × [Factor] = **[Final] kN**

**Installation Requirements:**
- Minimum spacing: [X]mm (≥3d for full capacity)
- Minimum edge distance: [Y]mm (≥1.5hef)
- Hole diameter: [Z]mm
- Embedment depth: [hef]mm
- Torque: [T] Nm

**⚠️ For precise group calculations, use Hilti PROFIS Anchor software.**

Source: Hilti Technical Guide, Page [X]
```

---

## 🔗 SYNONYM MAPPING

Add to `retrieval_service.py`:

```python
PRODUCT_SYNONYMS = {
    # Hilti
    'hit-hy': ['chemical anchor', 'adhesive anchor', 'injection anchor', 'hybrid anchor'],
    'hit-re': ['epoxy anchor', 'chemical anchor', 'resin anchor'],
    'hst': ['through bolt', 'mechanical anchor', 'expansion bolt'],
    'hsl': ['sleeve anchor', 'heavy duty anchor'],
    'hus': ['screw anchor', 'masonry anchor'],
    'kwik bolt': ['wedge anchor', 'kb-tz', 'mechanical anchor'],
    'profis': ['anchor design', 'anchor software', 'group calculation'],
}
```

---

## 🎯 TRIGGER DETECTION

When query contains:
- "group of anchors"
- "4 anchors", "6 anchors"
- "baseplate", "column base"
- "anchor array", "anchor pattern"
- "multiple Hilti", "group effect"

→ Apply Group Effects protocol

---

## 📁 HILTI FILES TO INGEST

Priority order:
1. **Hilti Anchor Technical Data** (Master tables)
2. **Hilti Application Guide NZ** (Local requirements)
3. **HIT-HY 200 Technical Data** (Chemical anchor details)
4. **HST3/HSL-3 Technical Data** (Mechanical anchors)
5. **PROFIS Output Examples** (For reference)

---

## ⚠️ IMPORTANT NOTES

1. **Always recommend PROFIS** for final design - Stryda provides estimates only
2. **Seismic zones** affect capacity significantly in NZ
3. **Cracked vs uncracked** concrete changes everything
4. **Fire rating** may require specific products (HIT-HY 200-R V5)

---

**Last Updated:** January 2026
**Status:** Awaiting Hilti file upload for ingestion
