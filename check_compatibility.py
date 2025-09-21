#!/usr/bin/env python3
"""
Compatibility checker for refactored UmaAutoGUI
Checks if all required methods are available
"""

import sys
import traceback

def check_compatibility():
    """Check if the refactored UmaAutoGUI has all required methods"""
    print("Checking UmaAutoGUI compatibility...")

    try:
        from gui.main_window_v2 import UmaAutoGUI

        # Create instance (but don't run mainloop)
        app = UmaAutoGUI()

        # List of methods that should exist
        required_methods = [
            # Original methods
            'init_variables',
            'load_initial_settings',
            'setup_gui',
            'setup_events',
            'load_tab_settings',
            'start_bot',
            'stop_bot',
            'enhanced_stop_bot',
            'force_exit_program',
            'set_running_state',
            'log_message',
            'save_settings',
            'get_event_choice_settings',
            'get_current_settings',
            'on_closing',

            # New required methods
            'update_current_date',
            'update_mood_status',
            'update_turn_status',
            'update_year_status',
            'update_energy_status',
            'save_support_card_state',
            'focus_game_window',

            # Core managers
            'window_manager',
            'ui_builder',
            'event_handler',
            'settings_manager',
            'bot_controller'
        ]

        missing_methods = []
        for method in required_methods:
            if not hasattr(app, method):
                missing_methods.append(method)

        # Check core managers exist and have required methods
        manager_checks = {
            'window_manager': ['load_window_settings', 'setup_window', 'save_window_position'],
            'ui_builder': ['create_main_layout'],
            'event_handler': ['setup_events', 'on_closing'],
            'settings_manager': ['load_all_settings', 'save_all_settings'],
            'bot_controller': ['start_bot', 'stop_bot', 'check_key_validation']
        }

        for manager_name, methods in manager_checks.items():
            if hasattr(app, manager_name):
                manager = getattr(app, manager_name)
                for method in methods:
                    if not hasattr(manager, method):
                        missing_methods.append(f"{manager_name}.{method}")
            else:
                missing_methods.append(f"Manager: {manager_name}")

        # Report results
        if missing_methods:
            print("❌ COMPATIBILITY ISSUES FOUND:")
            for method in missing_methods:
                print(f"   - Missing: {method}")
            return False
        else:
            print("✅ ALL COMPATIBILITY CHECKS PASSED!")
            print("   - All required methods are present")
            print("   - All core managers are available")
            return True

    except ImportError as e:
        print(f"❌ IMPORT ERROR: {e}")
        print("   - Cannot import UmaAutoGUI")
        return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality without running mainloop"""
    print("\nTesting basic functionality...")

    try:
        from gui.main_window_v2 import UmaAutoGUI

        # Test app creation
        app = UmaAutoGUI()
        print("✅ App creation: SUCCESS")

        # Test logging
        app.log_message("Test log message")
        print("✅ Logging: SUCCESS")

        # Test settings access
        settings = app.get_current_settings()
        print("✅ Settings access: SUCCESS")

        # Test window manager
        app.window_manager.get_window_settings()
        print("✅ Window manager: SUCCESS")

        print("✅ ALL BASIC TESTS PASSED!")
        return True

    except Exception as e:
        print(f"❌ BASIC TEST FAILED: {e}")
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("=" * 50)
    print("UmaAutoGUI Compatibility Checker")
    print("=" * 50)

    compatibility_ok = check_compatibility()
    functionality_ok = test_basic_functionality()

    print("\n" + "=" * 50)
    if compatibility_ok and functionality_ok:
        print("🎉 REFACTORING SUCCESSFUL!")
        print("   The refactored UmaAutoGUI is ready to use.")
        print("   You can run: python main.py")
    else:
        print("⚠️  REFACTORING ISSUES DETECTED!")
        print("   Please fix the issues above before using the app.")
    print("=" * 50)

if __name__ == "__main__":
    main()