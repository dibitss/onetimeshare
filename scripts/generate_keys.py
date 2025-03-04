#!/usr/bin/env python3
"""Generate secure keys for OneTimeShare."""
import secrets

def generate_keys():
    """Generate secure keys for the application."""
    secret_key = secrets.token_hex(32)
    encryption_key = secrets.token_hex(32)
    
    print('Generated secure keys. Add these to your environment:')
    print(f'export SECRET_KEY="{secret_key}"')
    print(f'export ENCRYPTION_KEY="{encryption_key}"')
    
    # Also create a secrets.yaml file for Helm
    with open('secrets.yaml', 'w') as f:
        f.write(f'''secrets:
  secretKey: "{secret_key}"
  encryptionKey: "{encryption_key}"
''')
    print('\nCreated secrets.yaml file for Helm deployment.')

if __name__ == '__main__':
    generate_keys() 