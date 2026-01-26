# 🔩 DUAL-CLEAT LOGIC: Multi-Component Calculation Protocol
**Version:** 1.0
**Status:** ACTIVE
**Location:** `/app/mastery/protocols/dual_cleat_logic.md`

---

## 📐 THE PRINCIPLE

When a user asks about **multiple identical components** working together, Stryda must:
1. Retrieve the **single unit capacity**
2. Apply the **linear multiplication factor** (for simple cases)
3. Apply **group reduction factors** (for anchors/bolts with edge effects)
4. State any **installation requirements** for the combination

---

## 🧮 CALCULATION MODES

### Mode 1: LINEAR DOUBLING (Timber Connectors)
**Applies to:** Joist hangers, straps, cleats, tie-downs, brackets

```
Total Capacity = Single Unit × Quantity
```

**Example:**
- User: "What if I use two Triple Grips?"
- Single Triple Grip: 6.0 kN uplift
- **Answer:** 2 × 6.0 kN = **12.0 kN total uplift capacity**

**Conditions:**
- Both units must be installed per manufacturer specs
- Adequate substrate (bearer/joist) to transfer load
- No interference between fixings

---

### Mode 2: GROUP EFFECT REDUCTION (Concrete Anchors)
**Applies to:** Hilti, Ramset, Bremick anchors in concrete/masonry

```
Total Capacity = Single Unit × Quantity × Group Factor (Ag/Ag0)
```

**Group factors depend on:**
- Edge distance (≥1.5 × embedment depth for full capacity)
- Spacing between anchors (≥3 × diameter for no reduction)
- Concrete strength (f'c)
- Cracked vs uncracked concrete

**Example (Hilti HIT-HY 200 M12):**
- Single anchor tension: 25.0 kN
- 4 anchors at 100mm spacing: Group factor = 0.75
- **Answer:** 4 × 25.0 kN × 0.75 = **75.0 kN total**

---

### Mode 3: SHEAR PLANE MULTIPLICATION (Bolted Connections)
**Applies to:** Bolts in timber, steel brackets

```
Capacity depends on:
- Single shear vs double shear
- Number of shear planes
- Bolt grade and diameter
```

---

## 🏷️ BRAND-SPECIFIC DOUBLING RULES

### Pryda
| Product | Single Capacity | Doubling Allowed? | Notes |
|---------|----------------|-------------------|-------|
| Triple Grip | 6.0 kN | ✅ Yes | Install on opposite faces |
| Framing Anchor | 4.0 kN | ✅ Yes | Both sides of stud |
| Joist Hanger | Per table | ✅ Yes | Adjacent hangers OK |
| Nail Plate | Per table | ⚠️ Check | Depends on timber width |

### MiTek / Lumberlok
| Product | Single Capacity | Doubling Allowed? | Notes |
|---------|----------------|-------------------|-------|
| Multi-Grip | 5.5 kN | ✅ Yes | Opposite faces |
| Joist Strap | 8.0 kN | ✅ Yes | Both ends |
| Purlin Cleat | Per table | ✅ Yes | Per purlin |

### Hilti (Anchors)
| Product | Single Capacity | Group Effect? | Notes |
|---------|----------------|---------------|-------|
| HIT-HY 200 | Per design | ✅ Yes | Use PROFIS for groups |
| HST3 | Per table | ✅ Yes | Edge/spacing reduction |
| HUS-HR | Per table | ✅ Yes | Concrete quality factor |

### Bremick (Fasteners)
| Product | Single Capacity | Doubling Notes |
|---------|----------------|----------------|
| Coach Screw | Per table | Linear for < 4 screws |
| Hex Bolt | Per grade | Check thread engagement |
| Dynabolt | Per table | Group factor for concrete |

---

## 💬 RESPONSE TEMPLATE

When user asks "What if I use X quantity of [Product]?":

```
**Single [Product] Capacity:** [X] kN ([tension/shear/uplift])

**For [Quantity] units:**
- Calculation: [Quantity] × [X] kN = **[Total] kN**
- [Any reduction factors if applicable]

**Installation Requirements:**
- [Spacing requirements]
- [Edge distance requirements]  
- [Substrate requirements]

**Source:** [Brand Manual], Page [X], Table [Y]

⚠️ Verify final design against [Brand] technical guidelines and site conditions.
```

---

## 🔗 INTEGRATION WITH STRYDA

### System Prompt Addition
When detecting quantity modifiers ("two", "double", "pair", "multiple", "4x", etc.):
1. Extract the base product
2. Retrieve single-unit capacity
3. Apply appropriate calculation mode
4. Include installation caveats

### Trigger Words
- "two", "double", "pair of"
- "multiple", "several"
- "4 anchors", "6 bolts"
- "group of", "array of"
- "what if I use X"

---

## 📁 Related Files
- `/app/mastery/protocols/stryda_platinum_master.md` - Main protocol
- `/app/backend-minimal/retrieval_service.py` - Search engine
- `/app/backend-minimal/core_prompts.py` - System prompts

---

**Last Updated:** January 2026
**Author:** Neo (Stryda Dev Assistant)
