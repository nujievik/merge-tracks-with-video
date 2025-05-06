import os
import re

from wcwidth import wcswidth

project_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(project_dir)

source = os.path.join(project_dir, 'resources/iso639_language_list.cpp')
enum_out = os.path.join(project_dir, 'src/types/lang_code.rs')
map_from_str_out = os.path.join(project_dir, 'src/types/lang_code/map_from_str.rs')
list_langs_out = os.path.join(project_dir, 'src/types/lang_code/list_langs.rs')

with open(source, 'r', encoding='utf-8') as f:
    lines = f.readlines()

max_name = 0
full_names = list()
codes = list()

for line in lines:
    if "Reserved for local use" in line:
        continue
    match = re.search(r'{\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)"', line)
    if match:
        _codes = list()
        for i in range(2, 5):
            code = match.group(i).strip()
            if code:
                _codes.append(code)
        if not _codes:
            continue

        name = match.group(1).strip()

        len_name = len(name)
        if len_name > max_name:
            max_name = len_name

        full_names.append(name)
        codes.append(_codes)

# PascalCase
def to_pascal(code):
    return ''.join(word.capitalize() for word in code.split('_'))

# Generate enum
enum_variants = [f"    {to_pascal(_codes[0])}," for _codes in codes]
rust_enum = (
    "// Auto-generated LangCode enum\n\n"

    "mod impls;\n"
    "mod list_langs;\n"
    "mod map_from_str;\n\n"

    "use strum_macros::AsRefStr;\n\n"

    "#[derive(AsRefStr, Clone, Copy, Eq, PartialEq, Hash)]\n"
    '#[strum(serialize_all = "kebab-case")]\n'
    "pub enum LangCode {\n" +
    '\n'.join(enum_variants) +
    "\n}\n"
)

with open(enum_out, 'w', encoding='utf-8') as f:
    f.write(rust_enum)

print("✅ Rust enum generated →", enum_out)

# Generate MAP_FROM_STR
map_entries = list()
for _codes in codes:
    enum = _codes[0]
    for code in _codes:
        map_entries.append(f'    "{code}" => LangCode::{to_pascal(enum)},')

rust_map = (
    "// Auto-generated MAP_FROM_STR of LangCode\n\n"

    "use super::LangCode;\n"
    "use phf::phf_map;\n\n"

    "pub(in crate::types::lang_code) static MAP_FROM_STR: phf::Map<&'static str, LangCode> = phf_map! {\n" +
    '\n'.join(map_entries) +
    "\n};\n"
)

with open(map_from_str_out, 'w', encoding='utf-8') as f:
    f.write(rust_map)

print("✅ PHF map generated →", map_from_str_out)

# Generate HELP_LIST

NAME_COLUMN = max_name + 1
CODE_COLUMN = 16

header = "English language name".ljust(NAME_COLUMN)
for title in ["ISO 639-3 code", "ISO 639-2 code", "ISO 639-1 code"]:
    header += "|" + " " + title.ljust(CODE_COLUMN - 1)
header += "\n"

separator = "-" * NAME_COLUMN
for _ in range(3):
    separator += "+" + "-" * (CODE_COLUMN)
separator += "\n"

# Some symbols in name may display as 1 but store as multiple
def visual_width(s):
    return wcswidth(s)

body = ""
for name, code_list in zip(full_names, codes):
    padding = NAME_COLUMN - visual_width(name)
    line = name + ' ' * padding
    for code in code_list:
        line += "|" + " " + code.ljust(15)
    while len(code_list) < 3:
        line += "|" + " " + " " * 15
        code_list.append("")
    line += "\n"
    body += line

s = header + separator + body

with open(list_langs_out, 'w', encoding='utf-8') as f:
    f.write(f'pub(in crate::types::lang_code) static LIST_LANGS: &str = r#"\n{s}"#;\n')

print("✅ Help language list generated →", list_langs_out)
