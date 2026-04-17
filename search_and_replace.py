import pandas as pd
import re
import json

def batch_regex_replace(excel_path, json_path, output_path):
    # 1. Load CSV and prepare the mapping
    df = pd.read_csv(excel_path, sep=';')
    # Ensure strings and remove any empty rows
    df = df.dropna(subset=['Old_tage_names', 'New_tag_names'])
    
    # Create a dictionary for fast lookup during the regex sub
    mapping = {str(k): str(v) for k, v in zip(df['Old_tage_names'], df['New_tag_names'])}

    # 2. Build the Regex Pattern
    # We sort keys by length (descending) to ensure "apple_pie" is matched before "apple"
    pattern_keys = sorted(mapping.keys(), key=len, reverse=True)
    # Use re.escape to handle special characters in your Excel keys
    combined_pattern = re.compile("|".join(map(re.escape, pattern_keys)))

    # 3. Define the replacement function
    def replace_match(match):
        return mapping[match.group(0)]

    # 4. Process the JSON as a string for maximum speed
    print("Reading JSON file...")
    with open(json_path, 'r', encoding='utf-8') as f:
        json_contents = f.read()

    print("Performing batch replacement...")
    # This single pass replaces all occurrences found in the mapping
    updated_contents = combined_pattern.sub(replace_match, json_contents)

    # 5. Save the result
    print("Writing updated file...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(updated_contents)

    print("Done!")

# Example usage
batch_regex_replace('old_to_new_tags.csv', 'Q_9539.csv', 'updated_Q_9539.csv')

# A simple function to count occurrences of a specific string in a large file, which can be useful for verifying the number of replacements made or for general analysis.
# def count_specific_string(file_path, search_term):
#     """
#     Counts total occurrences of a specific string in a large file.
#     """
#     count = 0
#     print(f"Searching for: '{search_term}'...")
    
#     # Reading line-by-line is safer for 6,000,000+ line files
#     with open(file_path, 'r', encoding='utf-8') as f:
#         for line in f:
#             count += line.count(search_term)
            
#     print(f"Found '{search_term}' {count} times.")
#     return count

# # Example usage:
# total = count_specific_string('Q_9539-alarms.csv', 'A12.Solar.Q_9539.LPC.PIT_93817.Sts*')