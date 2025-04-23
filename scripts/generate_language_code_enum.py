import re

SOURCE = '../resources/iso639_language_list.cpp'
ENUM_OUT = '../src/types/language_code.rs'
MAP_OUT = '../src/types/language_code/map.rs'

with open(SOURCE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

codes = set()

for line in lines:
    if "Reserved for local use" in line:
        continue
    match = re.search(r'{\s*".*?",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)"', line)
    if match:
        for i in range(1, 4):
            code = match.group(i).strip()
            if code:
                codes.add(code)

codes = sorted(codes)

# PascalCase
def to_pascal(code):
    return ''.join(word.capitalize() for word in code.split('_'))

# Generate enum
enum_variants = [f"    {to_pascal(code)}," for code in codes]
rust_enum = (
    "// Auto-generated LanguageCode enum\n\n"

    "mod impls;\n"
    "mod map;\n\n"

    "#[derive(Clone, Copy)]\n"
    "pub enum LanguageCode {\n" +
    '\n'.join(enum_variants) +
    "\n}\n"
)

with open(ENUM_OUT, 'w', encoding='utf-8') as f:
    f.write(rust_enum)

print("✅ Rust enum generated →", ENUM_OUT)

# Generate phf map
map_entries = [f'    "{code}" => LanguageCode::{to_pascal(code)},' for code in codes]
rust_map = (
    "// Auto-generated PHF map of LanguageCode\n\n"

    "use super::LanguageCode;\n"
    "use phf::phf_map;\n\n"

    "pub static LANG_MAP: phf::Map<&'static str, LanguageCode> = phf_map! {\n" +
    '\n'.join(map_entries) +
    "\n};\n"
)

with open(MAP_OUT, 'w', encoding='utf-8') as f:
    f.write(rust_map)

print("✅ PHF map generated →", MAP_OUT)
