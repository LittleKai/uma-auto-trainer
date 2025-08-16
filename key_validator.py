import json
import time
from typing import Optional

# Try to import requests, fallback to urllib if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False

class KeyValidator:
    """Validates application key against remote source"""

    def __init__(self):
        self.config_file = "config.json"
        self.remote_url = "https://docs.google.com/document/d/1qcQoKZKkD81Fej1yEyFmVv9t4ed-g46afPshif088WE/export?format=txt"
        self.expected_key = "jJ10uNHDwuPW9LGNWWZ2"
        self.cached_result = None
        self.last_check_time = 0
        self.cache_duration = 300  # 5 minutes cache

    def load_config_key(self) -> Optional[str]:
        """Load key from config.json"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('key', '')
        except FileNotFoundError:
            self.create_default_config()
            return self.expected_key
        except Exception as e:
            print(f"Error loading config: {e}")
            return None

    def create_default_config(self):
        """Create default config with key"""
        try:
            default_config = {
                "priority_stat": ["spd", "pwr", "sta", "wit", "guts"],
                "maximum_failure": 15,
                "minimum_energy_percentage": 40,
                "critical_energy_percentage": 20,
                "stat_caps": {
                    "spd": 1120,
                    "sta": 1120,
                    "pwr": 1120,
                    "guts": 500,
                    "wit": 500
                },
                "key": "jJ10uNHDwuPW9LGNWWZ2"
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)

        except Exception as e:
            print(f"Error creating default config: {e}")

    def fetch_remote_key_with_requests(self) -> Optional[str]:
        """Fetch key from remote Google Docs using requests library"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(self.remote_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Get text content with proper encoding handling
            response.encoding = 'utf-8'
            content = response.text

            # Debug logging
            print(f"[DEBUG] Raw content length: {len(content)}")
            print(f"[DEBUG] Raw content bytes: {content.encode('utf-8')[:50]}...")

            return self._extract_key_from_content(content)

        except requests.exceptions.RequestException as e:
            print(f"Network error fetching remote key: {e}")
            return None
        except Exception as e:
            print(f"Error fetching remote key: {e}")
            return None

    def fetch_remote_key_with_urllib(self) -> Optional[str]:
        """Fetch key from remote Google Docs using urllib (fallback)"""
        try:
            req = urllib.request.Request(
                self.remote_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                # Read as bytes first, then decode properly
                raw_data = response.read()

                # Try different encodings
                for encoding in ['utf-8', 'utf-8-sig', 'latin-1']:
                    try:
                        content = raw_data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    content = raw_data.decode('utf-8', errors='ignore')

                # Debug logging
                print(f"[DEBUG] Raw content length: {len(content)}")
                print(f"[DEBUG] Raw content bytes: {raw_data[:50]}...")

                return self._extract_key_from_content(content)

        except urllib.error.URLError as e:
            print(f"Network error fetching remote key: {e}")
            return None
        except Exception as e:
            print(f"Error fetching remote key: {e}")
            return None

    def _extract_key_from_content(self, content: str) -> Optional[str]:
        """Extract key from content with BOM and whitespace cleaning"""
        # Remove BOM (Byte Order Mark) characters
        content = content.encode('utf-8').decode('utf-8-sig').strip()

        # Remove common invisible characters
        content = content.replace('\ufeff', '')  # BOM
        content = content.replace('\u200b', '')  # Zero-width space
        content = content.replace('\u00a0', '')  # Non-breaking space

        # Look for the key in the content
        lines = content.split('\n')
        for line in lines:
            line = line.strip()

            # Clean invisible characters from line
            line = line.encode('utf-8').decode('utf-8-sig').strip()
            line = line.replace('\ufeff', '').replace('\u200b', '').replace('\u00a0', '')

            if line and len(line) == len(self.expected_key):
                # Check if it contains only alphanumeric characters
                if line.isalnum():
                    return line

        # If no valid key found, clean the entire content
        cleaned_content = content.strip()
        if cleaned_content and len(cleaned_content) <= 50:  # Reasonable key length
            # Final cleaning
            cleaned_content = cleaned_content.encode('utf-8').decode('utf-8-sig').strip()
            cleaned_content = cleaned_content.replace('\ufeff', '').replace('\u200b', '').replace('\u00a0', '')
            return cleaned_content

        return None

    def fetch_remote_key(self) -> Optional[str]:
        """Fetch key from remote Google Docs"""
        if HAS_REQUESTS:
            return self.fetch_remote_key_with_requests()
        else:
            return self.fetch_remote_key_with_urllib()

    def validate_key(self, show_success=False) -> tuple[bool, str]:
        """
        Validate key against remote source
        Returns: (is_valid, message)
        """
        # Check cache first
        current_time = time.time()
        if (self.cached_result is not None and
                current_time - self.last_check_time < self.cache_duration):
            if show_success and self.cached_result[0]:
                return (True, "Key validation successful (cached)")
            return self.cached_result

        # Load local key
        local_key = self.load_config_key()
        if not local_key:
            result = (False, "No key found in config.json")
            self.cached_result = result
            self.last_check_time = current_time
            return result

        # Clean local key as well
        local_key = local_key.encode('utf-8').decode('utf-8-sig').strip()
        local_key = local_key.replace('\ufeff', '').replace('\u200b', '').replace('\u00a0', '')

        # Check if requests library is available
        if not HAS_REQUESTS:
            print("Warning: requests library not found, using urllib fallback")

        # Fetch remote key
        remote_key = self.fetch_remote_key()
        if remote_key is None:
            result = (False, "Unable to fetch remote key. Please check your internet connection.")
            self.cached_result = result
            self.last_check_time = current_time
            return result

        # Debug logging (only in console, not in error message)
        print(f"[DEBUG] Local key: '{local_key}' (length: {len(local_key)})")
        print(f"[DEBUG] Remote key: '{remote_key}' (length: {len(remote_key)})")
        print(f"[DEBUG] Local key bytes: {local_key.encode('utf-8')}")
        print(f"[DEBUG] Remote key bytes: {remote_key.encode('utf-8')}")

        # Compare keys
        if local_key.strip() == remote_key.strip():
            result = (True, "Key validation successful" if show_success else "")
            self.cached_result = result
            self.last_check_time = current_time
            return result
        else:
            # Simple error message
            result = (False, "Invalid key")
            self.cached_result = result
            self.last_check_time = current_time
            return result

    def quick_validate(self) -> bool:
        """Quick validation without detailed messages"""
        is_valid, _ = self.validate_key()
        return is_valid

    def clear_cache(self):
        """Clear validation cache"""
        self.cached_result = None
        self.last_check_time = 0

    def fix_local_key(self) -> bool:
        """Try to fix local key by fetching and updating from remote source"""
        try:
            print("🔧 Attempting to fix local key...")

            # Fetch remote key
            remote_key = self.fetch_remote_key()
            if not remote_key:
                print("❌ Could not fetch remote key")
                return False

            print(f"✅ Fetched remote key: {repr(remote_key)}")

            # Update config with remote key
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                config['key'] = remote_key

                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)

                print("✅ Updated config.json with new key")

                # Clear cache to force re-validation
                self.clear_cache()

                # Test validation
                is_valid, message = self.validate_key(show_success=True)
                if is_valid:
                    print("🎉 Key fix successful!")
                    return True
                else:
                    print(f"❌ Key fix failed: {message}")
                    return False

            except Exception as e:
                print(f"❌ Failed to update config: {e}")
                return False

        except Exception as e:
            print(f"❌ Key fix failed: {e}")
            return False

# Global validator instance
_key_validator = None

def get_key_validator() -> KeyValidator:
    """Get global key validator instance"""
    global _key_validator
    if _key_validator is None:
        _key_validator = KeyValidator()
    return _key_validator

def validate_application_key(show_success=False) -> tuple[bool, str]:
    """Validate application key - main function for external use"""
    validator = get_key_validator()
    return validator.validate_key(show_success)

def is_key_valid() -> bool:
    """Quick check if key is valid"""
    validator = get_key_validator()
    return validator.quick_validate()

def check_dependencies() -> dict:
    """Check if all required dependencies are available"""
    deps_status = {
        'requests': HAS_REQUESTS,
        'urllib': True,  # Always available in Python standard library
        'json': True,    # Always available in Python standard library
        'time': True     # Always available in Python standard library
    }
    return deps_status

def fix_key_automatically():
    """Automatically fix key by fetching from remote and updating local config"""
    validator = get_key_validator()
    return validator.fix_local_key()

def interactive_key_fix():
    """Interactive key fixing with user confirmation"""
    print("🔧 Interactive Key Fix Tool")
    print("=" * 40)

    validator = get_key_validator()

    # Check current status
    is_valid, message = validator.validate_key()
    if is_valid:
        print("✅ Key is already valid!")
        return True

    print(f"❌ Key validation failed: {message}")
    print()

    # Ask user if they want to fix
    response = input("Do you want to try to fix the key automatically? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Key fix cancelled by user")
        return False

    # Attempt fix
    return fix_key_automatically()

def test_key_validation():
    """Test function to debug key validation issues"""
    print("🔍 Testing Key Validation...")
    print("=" * 50)

    validator = get_key_validator()

    # Test local key
    local_key = validator.load_config_key()
    print(f"Local key: '{local_key}'")
    print(f"Local key length: {len(local_key) if local_key else 'None'}")
    if local_key:
        print(f"Local key bytes: {local_key.encode('utf-8')}")
        print(f"Local key repr: {repr(local_key)}")

    print()

    # Test remote key
    print("Fetching remote key...")
    remote_key = validator.fetch_remote_key()
    print(f"Remote key: '{remote_key}'")
    print(f"Remote key length: {len(remote_key) if remote_key else 'None'}")
    if remote_key:
        print(f"Remote key bytes: {remote_key.encode('utf-8')}")
        print(f"Remote key repr: {repr(remote_key)}")

    print()

    # Character-by-character comparison
    if local_key and remote_key:
        print("Character-by-character comparison:")
        max_len = max(len(local_key), len(remote_key))
        for i in range(max_len):
            local_char = local_key[i] if i < len(local_key) else '(missing)'
            remote_char = remote_key[i] if i < len(remote_key) else '(missing)'
            local_ord = ord(local_key[i]) if i < len(local_key) else 'N/A'
            remote_ord = ord(remote_key[i]) if i < len(remote_key) else 'N/A'

            match = "✓" if local_char == remote_char else "✗"
            print(f"  {i:2d}: '{local_char}' ({local_ord}) | '{remote_char}' ({remote_ord}) {match}")

    print()

    # Test validation
    is_valid, message = validator.validate_key(show_success=True)
    print(f"Validation result: {is_valid}")
    print(f"Message: {message}")

    print("=" * 50)
    return is_valid

def debug_key_details():
    """Detailed debug function for troubleshooting key issues"""
    print("🔬 Detailed Key Analysis...")
    print("=" * 60)

    validator = get_key_validator()

    # Load and analyze local key
    local_key = validator.load_config_key()
    if local_key:
        print("LOCAL KEY ANALYSIS:")
        print(f"  Raw: {repr(local_key)}")
        print(f"  Length: {len(local_key)}")
        print(f"  Bytes: {local_key.encode('utf-8')}")
        print(f"  Hex: {local_key.encode('utf-8').hex()}")

        # Clean local key
        cleaned_local = local_key.encode('utf-8').decode('utf-8-sig').strip()
        cleaned_local = cleaned_local.replace('\ufeff', '').replace('\u200b', '').replace('\u00a0', '')
        print(f"  Cleaned: {repr(cleaned_local)}")
        print(f"  Cleaned Length: {len(cleaned_local)}")
        print()

    # Fetch and analyze remote key
    print("REMOTE KEY ANALYSIS:")
    remote_key = validator.fetch_remote_key()
    if remote_key:
        print(f"  Raw: {repr(remote_key)}")
        print(f"  Length: {len(remote_key)}")
        print(f"  Bytes: {remote_key.encode('utf-8')}")
        print(f"  Hex: {remote_key.encode('utf-8').hex()}")
    else:
        print("  Failed to fetch remote key")

    print()

    # Expected key analysis
    print("EXPECTED KEY ANALYSIS:")
    expected = validator.expected_key
    print(f"  Expected: {repr(expected)}")
    print(f"  Length: {len(expected)}")
    print(f"  Bytes: {expected.encode('utf-8')}")
    print(f"  Hex: {expected.encode('utf-8').hex()}")

    print("=" * 60)

if __name__ == "__main__":
    # Run test when script is executed directly
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        debug_key_details()
    else:
        test_key_validation()