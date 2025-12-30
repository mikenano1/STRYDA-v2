        # COMPLIANCE_STRICT
        strict_patterns = [
            r'\b(minimum|maximum|required|shall|must)\s+\d+',
            r'\b(what\s+(are|is)\s+the|what\s+does)\s+(nzs|nzbc|e2|h1|c/as|b1|f4|g5|g12|g13)\s+(requirement|say|require|specify|state)',
            r'\baccording to\s+(nzs|e2|h1|b1|nzbc|code|standard)\b',
            r'\b(nzs\s*3604|nzs\s*4229|e2/as1|h1/as1|b1/as1|c/as\d)\s+(table|clause|section)\s*\d',
            r'\bwhat\s+(r-?value|span|spacing|height|width|depth|thickness|cover)\s+(does|is|are).*(require|code|nzs|standard)',
            r'\bwhat\s+is\s+the\s+(stud|joist|rafter|purlin|beam|bearer)\s+spacing\b',
            r'\bwhat\s+is\s+the\s+maximum\s+span\b',
            r'\b(show|find)\s+(me\s+)?(the\s+)?(matrix|table|chart|diagram|figure|selection\s+tables?)\b',
            r'\b[a-h]\d+/as\d+\s+(says?|requires?|states?)\b',
            r'\b(nzs|nzbc)\s+\d+\s+(clause|table|section|requirements?)\b',
            r'\b(wind|corrosion)\s+zone\b',
            r'\b(nzs\s*3604|calculate)\b', # Added keywords
        ]