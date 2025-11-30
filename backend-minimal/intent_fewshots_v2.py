"""
STRYDA Intent Classifier V2.3 - Expanded Few-Shot Examples
Real NZ builder phrasing from training_questions_v2
"""

# COMPLIANCE_STRICT - Explicit code requirements (30 examples)
fewshots_compliance_strict = [
    "What are the NZS 3604 stud spacing requirements for Extra High wind?",
    "What does E2/AS1 4th edition say about cavity batten treatment?",
    "What's the minimum R-value for ceilings in climate zone 2 per H1/AS1?",
    "What fire rating does C/AS2 require between garage and dwelling?",
    "According to NZS 4229, what reinforcement is required for masonry walls?",
    "What does clause 7.1 of NZS 3604 specify for bracing?",
    "What's the maximum span for 140x45 joists in NZS 3604 Table 6.7?",
    "What fall does E2/AS1 require for membrane roofing?",
    "What cover is required for rebar in B1/AS1 strip footings?",
    "What clearance does G5.3.2 require for hearth installations?",
    "What's the minimum barrier height required by F4/AS1?",
    "What does H1/VM1 6th edition say about window performance?",
    "According to G12/AS1, what temperature is required for tempering valves?",
    "What spacing does NZS 3604 clause 8.4 specify for purlin fixings?",
    "What's the required FRR for inter-tenancy walls under C/AS1?",
    "What does E3/AS1 say about waterproofing wet areas over timber?",
    "According to F7/AS1, what's required for smoke alarm installation?",
    "What fall is specified in G13/AS1 for stormwater laterals?",
    "What does NZS 3604 Table 7.1 say about stud grades?",
    "What's the minimum depth for foundation trenches per B1/AS1?",
    "What's the exact requirement in E2 for apron flashing cover?",
    "According to NZBC, what's the maximum riser height for stairs?",
    "What does NZS 3604 specify for nog spacing in bracing walls?",
    "What's the required fixing pattern for metal cladding in Very High wind?",
    "What insulation R-value does H1 require for walls in zone 3?",
    "What's the minimum overlap for horizontal weatherboards per E2/AS1?",
    "According to C/AS2, what fire separation is needed at boundaries?",
    "What does the code say about ventilation in wet areas?",
    "What's the NZBC requirement for deck balustrade spacing?",
    "What fall does the standard require for shower floors?"
]

# IMPLICIT_COMPLIANCE - Checking/verifying compliance (30 examples)
fewshots_implicit_compliance = [
    "Does my 450mm spacing meet NZS 3604 for wall studs?",
    "Is 18mm cavity acceptable under E2/AS1 for brick veneer?",
    "Can I legally use 90x45 framing on a non-loadbearing wall?",
    "Will council accept this bracing layout per NZS 3604?",
    "Is my shower waterproofing compliant with the internal wet area code?",
    "Does this deck design meet Building Code for safety barriers?",
    "For a house built in 2005, which NZS 3604 version applies?",
    "Is PEX pipe acceptable for hot water under G12/AS1?",
    "Will this foundation comply with B1 for earthquake zone?",
    "Can I use this insulation and still meet H1 requirements?",
    "Is GIB EzyBrace acceptable for garage conversion under code?",
    "Does 12mm ply meet NZS 3604 for bracing walls?",
    "Will council sign off on this fire separation detail?",
    "Is my gully trap depth compliant with G13/AS1?",
    "Can I legally connect this fixture without a vent pipe?",
    "Does my design meet verification method VM1 for structure?",
    "Is 600mm stud spacing acceptable per code for this wall?",
    "Will this cladding system pass E2/AS1 compliance check?",
    "Can I use treated pine H3.2 for this deck application?",
    "Is my window flashing detail compliant with current E2?",
    "Will the inspector fail me if stairs don't have handrail?",
    "Do I need to meet NZS 3604 for this garage slab?",
    "Is it legal to skip the bottom plate flashing here?",
    "Will this deck pass if bracing line moves 500mm?",
    "Can I direct fix over old building paper and still comply?",
    "Is my roof pitch okay under E2 for this wind zone?",
    "Will council allow this without a PS3?",
    "Does this meet current code or do I need engineer?",
    "Is 150mm apron flashing enough to pass inspection?",
    "Can I use this fixing pattern and still be compliant?"
]

# GENERAL_HELP - Practical tradie guidance (30 examples)
fewshots_general_help = [
    "How far can 140x45 joists span for a standard deck?",
    "Why does my deck feel bouncy even with new timber?",
    "What's the best way to stop weatherboards from cupping?",
    "How do I fix a squeaky floor in a new build?",
    "What drill bit works best for predrilling hardwood decking?",
    "How do you stop insulation sagging in wall cavities?",
    "Why do roof sheets whistle in high wind?",
    "What's the easiest way to clean swarf off longrun?",
    "How do I stop condensation forming under metal roofing?",
    "Why do plasterboard screws pop through paint?",
    "What causes GIB joints to crack after painting?",
    "How do you straighten a bowed stud before lining?",
    "Why does concrete crack even when it looks fine initially?",
    "What's the best method for laying out a stud wall quickly?",
    "How do I stop timber posts rotting at the base?",
    "Why do nails back out of weatherboards over time?",
    "What saw blade gives cleanest cuts in plywood?",
    "How do you keep mesh lifted during concrete pour?",
    "Why does my timber gate sag after installation?",
    "What's the right screw length for fixing decking boards?",
    "How do I square up a timber frame quickly?",
    "Why do studs sometimes warp after installation?",
    "What's the preferred nail size for framing 90x45?",
    "How do you avoid overdriving nails in cladding?",
    "What's the normal spacing for ceiling battens?",
    "Why do window reveals sometimes sit out of square?",
    "How do you fix uneven gaps around interior doors?",
    "What's the easiest way to pack a window level?",
    "Why does timber framing sometimes make cracking noises?",
    "How do you stop timber beams from twisting?"
]

# PRODUCT_INFO - Product/material recommendations (15 examples)
fewshots_product_info = [
    "What's the best weatherboard brand for coastal homes?",
    "Which GIB system should I use for 60 minute fire walls?",
    "What Ardex membrane is best for tiled showers over timber?",
    "Which insulation brand lasts longest in NZ conditions?",
    "What metal roofing profile suits high rainfall areas?",
    "Which stain works best on cedar in coastal zones?",
    "What timber grade should I use for exterior decks?",
    "Which vapour barrier is best for cold climate zones?",
    "What's the most durable cladding for beach houses?",
    "Which concrete sealer works best for driveways?",
    "What Resene paint system lasts longest on fibre cement?",
    "Which Pink Batts product suits cathedral ceilings?",
    "What James Hardie cladding handles coastal exposure best?",
    "Which Metalcraft profile suits steep roof pitches?",
    "What Nuralite membrane system works for deck waterproofing?"
]

# COUNCIL_PROCESS - Consent and inspection processes (15 examples)
fewshots_council_process = [
    "How do I apply for a Code Compliance Certificate?",
    "What's the process for getting a building consent?",
    "When do I need a Producer Statement PS1?",
    "How long does council inspection take after framing?",
    "What paperwork is needed for a deck consent?",
    "Do I need Schedule 1 exemption for this minor alteration?",
    "How do I submit an RFI to council?",
    "What's the consent process for a garage conversion?",
    "When should I call for pre-pour inspection?",
    "What documents does council need for final sign-off?",
    "How do I get a Certificate of Acceptance?",
    "What's the process for amending an existing consent?",
    "When is PS3 required instead of PS1?",
    "How do I book a pre-line inspection with council?",
    "What forms are needed for a minor variation?"
]

