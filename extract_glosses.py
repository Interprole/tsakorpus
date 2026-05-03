#!/usr/bin/env python3
"""
Script to extract glosses from Khanty XML file and generate categories.json entry
"""

import xml.etree.ElementTree as ET
import json
import re
from collections import defaultdict

def extract_glosses_from_xml(xml_file):
    """Extract all unique glosses from the XML file."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    glosses = set()
    
    # Find all <item type="gls" lang="ru"> elements
    for item in root.findall(".//item[@type='gls'][@lang='ru']"):
        if item.text:
            gloss = item.text.strip()
            if gloss:
                # Split by dot to get individual gloss parts
                # Since tsakorpus automatically splits glosses by dot
                if '.' in gloss:
                    parts = gloss.split('.')
                    for part in parts:
                        if part:  # Skip empty parts
                            glosses.add(part)
                else:
                    glosses.add(gloss)
    
    return sorted(glosses)

def categorize_glosses(glosses):
    """
    Categorize glosses based on their type.
    Returns a dictionary mapping gloss -> category type.
    """
    categories = {}
    
    # Define category patterns
    category_patterns = {
        'pos': [
            'n', 'v', 'adj', 'adv', 'pro', 'num', 'part', 'conj', 'postp', 'ptcl',
            'intj', 'pred', 'cop', 'nmzl', 'prev', 'proh', 'punct'
        ],
        'case': [
            'nom', 'acc', 'gen', 'dat', 'loc', 'abl', 'ins', 'com', 'lat', 
            'ill', 'prol', 'transl', 'instr', 'elat', 'term', 'appr'
        ],
        'num': ['sg', 'pl', 'du', 'plur', 'sg>sg', 'nsg>nsg'],
        'pers': ['1sg', '2sg', '3sg', '1pl', '2pl', '3pl', '1du', '2du', '3du',
                 '2/3du', '1', '2', '3', '3sg>sg/pl', '1pl>pl', '1pl>sg', 
                 '3pl>pl', '3pl>sg', '1du>sg', '2/3du>sg/pl', '2/3du>sg', '1sg>sg', '1sg>pl'],
        'poss': ['poss', 'poss>1sg', 'poss>2sg', 'poss>3sg', 'poss>1pl', 'poss>2pl', 'poss>3pl',
                 'poss>1du', 'poss>2du', 'poss>3du'],
        'tense': ['pst', 'prs', 'fut', 'praes', 'praet', 'pres', 'npst'],
        'mood': ['ind', 'imp', 'cond', 'opt', 'sub', 'imper', 'indic'],
        'aspect': ['ipf', 'pf', 'perf', 'imperf', 'iter', 'freq', 'mom'],
        'voice': ['act', 'pass', 'med', 'caus'],
        'evidentiality': ['ev', 'quot', 'infer', 'dir'],
        'polarity': ['neg', 'affirm'],
        'vForm': ['inf', 'ger', 'partcp', 'ptcp', 'cvb', 'sup', 'conv'],
        'adjForm': ['comp', 'supr', 'attr', 'pred'],
        'transitivity': ['tr', 'intr', 'tran', 'TR', 'detr'],
        'animacy': ['an', 'inan', 'anim'],
        'gender': ['m', 'f', 'n', 'mf', 'flst'],
        'definiteness': ['def', 'indef', 'INDEF'],
        'degree': ['dim', 'aug'],
        'derivation': ['nmlz', 'verb', 'deverbprop', 'denom', 'inch'],
        'specifier': ['ex', 'add', 'emph', 'foc', 'top'],
        'cardinality': ['car', 'ord'],
        'proprietive': ['prop'],
        'decessive': ['dec'],
        'pronoun': ['indf', 'sp', 'known'],
        'particle': ['p', 'irr']
    }
    
    for gloss in glosses:
        gloss_lower = gloss.lower()
        
        # Check if it's a complete match with known categories
        categorized = False
        for category, patterns in category_patterns.items():
            if gloss_lower in patterns or gloss in patterns:
                categories[gloss] = category
                categorized = True
                break
        
        # Check partial matches for compound glosses (e.g., "poss.1sg")
        if not categorized:
            for category, patterns in category_patterns.items():
                for pattern in patterns:
                    if pattern in gloss_lower:
                        categories[gloss] = category
                        categorized = True
                        break
                if categorized:
                    break
        
        # Default categorization for uncategorized glosses
        if not categorized:
            # If it looks like a suffix/prefix indicator, categorize as derivation
            if any(x in gloss_lower for x in ['.', '-']):
                categories[gloss] = 'gramm'
            else:
                # Otherwise, leave it for manual review
                categories[gloss] = 'other'
    
    return categories

def generate_categories_json(glosses, categorize=True):
    """Generate the categories.json format for Khanty glosses."""
    if categorize:
        categorized = categorize_glosses(glosses)
    else:
        categorized = {g: 'gramm' for g in glosses}
    
    # Create the dictionary in the same format as Russian
    # Skip glosses categorized as "other" and filter out long Russian translations
    khanty_dict = {}
    for gloss in sorted(glosses):
        category = categorized.get(gloss, 'other')
        # Skip if:
        # 1. Category is "other"
        # 2. Contains Cyrillic letters (Russian translations)
        # 3. Is too long (likely a sentence/phrase, not a gloss)
        # 4. Contains only special characters or digits with spaces
        # 5. Starts with certain problematic characters
        has_cyrillic = any('\u0400' <= c <= '\u04FF' for c in gloss)
        is_too_long = len(gloss) > 20
        is_special_only = gloss in [')', ']', '???', '...', '']
        is_sentence = gloss.count(' ') > 2 or '(' in gloss or ')' in gloss.strip(')')
        
        if (category != 'other' and not has_cyrillic and not is_too_long 
            and not is_special_only and not is_sentence):
            khanty_dict[gloss] = category
    
    return khanty_dict

def main():
    xml_file = 'src_convertors/corpus/xml/khanty.xml'
    categories_file = 'src_convertors/corpus/conf_conversion/categories.json'
    
    print("Extracting glosses from XML file...")
    glosses = extract_glosses_from_xml(xml_file)
    print(f"Found {len(glosses)} unique glosses")
    
    print("\nGenerating categories dictionary...")
    khanty_categories = generate_categories_json(glosses, categorize=True)
    
    # Read existing categories.json
    print(f"\nReading {categories_file}...")
    with open(categories_file, 'r', encoding='utf-8') as f:
        categories_data = json.load(f)
    
    # Add khanty section
    categories_data['khanty'] = khanty_categories
    
    # Write back to categories.json
    print(f"Writing updated categories.json...")
    with open(categories_file, 'w', encoding='utf-8') as f:
        json.dump(categories_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Successfully added {len(khanty_categories)} Khanty glosses to categories.json")
    
    # Print some statistics
    category_counts = defaultdict(int)
    for category in khanty_categories.values():
        category_counts[category] += 1
    
    print("\nCategory distribution:")
    for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {category}: {count}")
    
    # Print first 20 glosses as preview
    print("\nFirst 20 glosses:")
    for i, (gloss, category) in enumerate(list(khanty_categories.items())[:20]):
        print(f"  \"{gloss}\": \"{category}\"")
    
    print("\nDone! Check the categories.json file.")

if __name__ == '__main__':
    main()
