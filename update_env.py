# -*- coding: utf-8 -*-
"""Update DATABASE_URL in .env file"""
import os

env_file = '.env'

# Read current .env file
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update DATABASE_URL
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith('DATABASE_URL='):
            old_value = line.strip()
            lines[i] = 'DATABASE_URL=postgresql://postgres:123456@10.56.11.121:5432/mh_cursor_test\n'
            updated = True
            print(f"Updated DATABASE_URL:")
            print(f"  Old: {old_value}")
            print(f"  New: {lines[i].strip()}")
            break
    
    if not updated:
        # DATABASE_URL not found, add it
        lines.append('\nDATABASE_URL=postgresql://postgres:123456@10.56.11.121:5432/mh_cursor_test\n')
        print("Added DATABASE_URL to .env file")
    
    # Write back to .env
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("\n✓ .env file updated successfully!")
    print("\nPlease restart Flask server to apply changes.")
else:
    print(f"Error: {env_file} not found")
