"""
Create a completely cleaned NCM table by processing all 15,144 entries
Uses learned rules to intelligently clean each description
"""
import json
import re
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*80)
print(" CREATING CLEANED NCM TABLE")
print("="*80)

# Load original table
print("\nLoading original NCM table...")
with open('../android/app/src/main/assets/ncm_table_old.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    original_entries = data['Nomenclaturas']

print(f"✓ Loaded {len(original_entries)} entries")

# Build lookup dictionary for hierarchy access
ncm_dict = {e['Codigo']: e for e in original_entries}

def clean_text(text):
    """Basic text cleaning"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove leading dashes
    text = re.sub(r'^--\s*', '', text)
    text = re.sub(r'^-\s*', '', text)
    
    # Remove trailing colons
    text = text.rstrip(':').strip()
    
    # Remove asterisks
    text = text.replace('*', '')
    
    # Remove parenthetical scientific names
    text = re.sub(r'\s*\([^)]*spp\.\)', '', text)
    
    # Clean up spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Fix encoding - comprehensive mappings
    replacements = {
        'Ã': 'ã', 'A-': 'í', 'Ac': 'é', 'A3': 'ó', 'A\'': 'ô',
        'AÃ': 'ão', 'Aâ': 'á', 'AAâ': 'ça', 'A1': 'á', 'Aç': 'ê',
        'AO': 'ú', 'A2': 'â', 'Ãª': 'ê', 'Ãâ': 'í',
        'Ãº': 'ú', 'Ã¡': 'á', 'Ã§': 'ç', 'Ã­': 'í', 'Ã©': 'é',
        'Ã³': 'ó', 'Ãµ': 'õ', 'Ã¢': 'â',
        # Additional for hyphenated words
        'Êú': 'Aç', 'Ãâ': 'í', 'âº': 'ú',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Clean up common encoding artifacts
    text = text.replace('Ã', 'á')  # Fallback for remaining Ã
    
    return text

def extract_product_name(desc):
    """Extract clean product name from description"""
    # Semicolon lists: take first item
    if ';' in desc:
        first = desc.split(';')[0].strip()
        first = re.sub(r'\s+do gênero\s+\w+', '', first, flags=re.IGNORECASE)
        first = re.sub(r'\s+da espécie\s+\w+', '', first, flags=re.IGNORECASE)
        return first.strip()
    
    # Comma lists: take first item
    if ',' in desc:
        first = desc.split(',')[0].strip()
        # Remove parenthetical notes
        first = re.sub(r'\s*\([^)]*\)', '', first).strip()
        # Remove "frescos ou secos" endings
        first = re.sub(r'\s+(frescos?|secas?|refrigeradas?|congeladas?)\s+ou\s+\w+', '', first, flags=re.IGNORECASE)
        return first.strip()
    
    # "E" (and) lists: take first item
    if ' e ' in desc and len(desc) > 30:
        first = desc.split(' e ')[0].strip()
        first = re.sub(r'\s*\([^)]*\)', '', first).strip()
        return first
    
    # Remove parenthetical clarifications if they don't add value
    # Keep important ones like "UHT (Ultra High Temperature)"
    if '(' in desc:
        # If parenthesis is at the end and adds clarification, keep it
        # Otherwise remove
        match = re.search(r'^(.+?)\s*\(([^)]+)\)\s*$', desc)
        if match:
            main = match.group(1).strip()
            clarification = match.group(2).strip()
            # Keep if it's an important clarification
            important_keywords = ['uht', 'ultra', 'temperatura', 'alta', 'domesticus']
            if any(kw in clarification.lower() for kw in important_keywords):
                return desc  # Keep as is
            # Otherwise just return the main part
            return main
    
    return desc

def get_parent_description(code):
    """Get parent description in hierarchy - try ALL levels"""
    code_no_dots = code.replace('.', '').zfill(8)
    
    # Try progressively higher levels - INCLUDING all subposition variants
    parent_codes = [
        f"{code_no_dots[:4]}.{code_no_dots[4:6]}",    # 3808.94 (full subposition)
        f"{code_no_dots[:4]}.{code_no_dots[4]}",      # 0904.2 (short subposition)
        f"{code_no_dots[:2]}.{code_no_dots[2:4]}",    # 09.04 (position)
        code_no_dots[:2],                              # 09 (chapter)
    ]
    
    for parent_code in parent_codes:
        if parent_code in ncm_dict:
            parent_desc = clean_text(ncm_dict[parent_code]['Descricao'])
            # Skip if parent is also generic
            if parent_desc.lower().strip() not in ['outros', 'outras', 'outro', 'outra']:
                return parent_desc
    
    return None

def clean_ncm_entry(entry):
    """Clean a single NCM entry intelligently"""
    code = entry['Codigo']
    original_desc = entry['Descricao']
    
    # Clean the description
    cleaned = clean_text(original_desc)
    
    # Extract product name
    product_name = extract_product_name(cleaned)
    
    # Check if it's generic/unclear
    generic_terms = ['outros', 'outras', 'outro', 'outra', 'demais']
    is_generic = product_name.lower().strip() in generic_terms
    
    # Packaging/processing only
    packaging_patterns = [
        r'^em embalagens', r'^em recipientes', r'^polido ou brunido',
        r'^triturad[oa]s? ou em pó', r'^em grão$', r'^em pó$',
        r'^secos?$', r'^frescas?$', r'^refrigeradas?$', r'^congeladas?$',
        r'^preparadas?$', r'^cozidas?$', r'^desossadas?$'
    ]
    is_packaging = any(re.match(pattern, product_name.lower()) for pattern in packaging_patterns)
    
    # Species-only descriptions
    is_species_only = (
        product_name.lower().startswith('de aves da espécie') or
        product_name.lower().startswith('de animais da espécie')
    )
    
    # If generic, packaging-only, or species-only, add parent context
    if is_generic or is_packaging or is_species_only:
        parent = get_parent_description(code)
        if parent:
            parent_clean = extract_product_name(parent)
            
            # Special handling for "Produtos X" cases - use position description directly
            if parent_clean.lower().startswith('produtos'):
                # Use this directly - it's better than just "Produtos"
                product_name = parent_clean
            elif is_generic:
                # Just use first word from parent
                words = parent_clean.split()
                meaningful = [w for w in words if len(w) > 3 and w.lower() not in generic_terms]
                if meaningful:
                    product_name = meaningful[0]
                elif words:
                    product_name = words[0]
            else:
                # Combine parent + qualifier
                if len(parent_clean) < 40:
                    product_name = f"{parent_clean} {product_name}"
                else:
                    # Use first few words of parent
                    words = parent_clean.split()[:3]
                    product_name = f"{' '.join(words)} {product_name}"
    
    # Final cleanup and length optimization
    if len(product_name) > 60:
        words = product_name.split()[:6]
        product_name = ' '.join(words)
    
    # Convert to title case
    product_name = ' '.join(
        word.capitalize() if len(word) > 2 else word.lower() 
        for word in product_name.split()
    )
    
    return {
        'Codigo': code,
        'Nome': product_name
    }

# Process all entries
print("\nProcessing all entries...")
cleaned_entries = []

for i, entry in enumerate(original_entries):
    if i % 1000 == 0:
        print(f"  Progress: {i}/{len(original_entries)} ({i*100//len(original_entries)}%)")
    
    cleaned = clean_ncm_entry(entry)
    cleaned_entries.append(cleaned)

print(f"✓ Processed all {len(cleaned_entries)} entries")

# Create output JSON
output = {
    "Data_Ultima_Atualizacao": "2025-11-10",
    "Fonte": "NCM Table - Intelligently Cleaned",
    "Total_Entries": len(cleaned_entries),
    "Processing_Rules": [
        "Extract first item from lists (comma, semicolon, 'e' separated)",
        "Remove HTML tags and Latin scientific names",
        "Add parent context for generic terms (outros, outras, etc.)",
        "Add parent context for packaging/processing-only descriptions",
        "Convert to title case for readability",
        "Limit length to 60 characters for UI display"
    ],
    "Produtos": cleaned_entries
}

# Save
output_file = 'ncm_clean_complete.json'
print(f"\nSaving to {output_file}...")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✓ Saved successfully!")

# Show samples
print("\n" + "="*80)
print(" SAMPLE CLEANED ENTRIES")
print("="*80)

samples = [0, 100, 500, 1000, 5000, 10000, 15000]
for idx in samples:
    if idx < len(cleaned_entries):
        entry = cleaned_entries[idx]
        print(f"\n  {entry['Codigo']:15s} -> {entry['Nome']}")

print("\n" + "="*80)
print(" COMPLETE!")
print("="*80)
print(f"\nOutput: {output_file}")
print(f"Total entries: {len(cleaned_entries)}")
print("\nReady to copy to Android assets!")

