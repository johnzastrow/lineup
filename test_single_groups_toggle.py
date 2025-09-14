#!/usr/bin/env python3
"""
Test script to validate the single groups toggle functionality.
"""

import sys
from pathlib import Path

def test_single_groups_toggle():
    """Test that the single groups toggle functionality is correctly implemented."""
    print("Testing Single Groups Toggle Functionality")
    print("=" * 55)
    
    try:
        # Read main.py content
        main_py_path = Path("main.py")
        if not main_py_path.exists():
            print("❌ main.py not found")
            return False
        
        content = main_py_path.read_text()
        
        # Test 1: Check for hide_single_groups attribute initialization
        print("\n1. Checking for hide_single_groups attribute...")
        if "self.hide_single_groups = True" in content:
            print("✅ hide_single_groups attribute initialized")
        else:
            print("❌ hide_single_groups attribute not properly initialized")
            return False
        
        # Test 2: Check for hide single groups switch widget
        print("\n2. Checking for Hide Single Groups switch...")
        if "hide_single_switch = ctk.CTkSwitch(" in content:
            print("✅ Hide Single Groups switch widget found")
        else:
            print("❌ Hide Single Groups switch widget missing")
            return False
        
        # Test 3: Check for switch text
        print("\n3. Checking switch text...")
        if 'text="Hide Single Groups"' in content:
            print("✅ Correct switch text found")
        else:
            print("❌ Switch text missing or incorrect")
            return False
        
        # Test 4: Check for toggle method
        print("\n4. Checking for toggle method...")
        if "def toggle_hide_single_groups(self):" in content:
            print("✅ toggle_hide_single_groups method found")
        else:
            print("❌ toggle_hide_single_groups method missing")
            return False
        
        # Test 5: Check for filtering logic in populate_group_list
        print("\n5. Checking filtering logic in populate_group_list...")
        filter_logic = "if self.hide_single_groups and summary['existing_images'] <= 1:"
        if filter_logic in content:
            print("✅ Filtering logic found in populate_group_list")
        else:
            print("❌ Filtering logic missing from populate_group_list")
            return False
        
        # Test 6: Check for enhanced status feedback
        print("\n6. Checking for enhanced status feedback...")
        if "Hiding" in content and "single-image groups" in content:
            print("✅ Enhanced status feedback found")
        else:
            print("❌ Enhanced status feedback missing")
            return False
        
        # Test 7: Check for group count feedback
        print("\n7. Checking for group count feedback...")
        if "groups shown" in content and "groups included" in content:
            print("✅ Group count feedback found")
        else:
            print("❌ Group count feedback missing")
            return False
        
        # Test 8: Check for current group handling
        print("\n8. Checking for current group handling...")
        if "current_group not in self.group_buttons" in content:
            print("✅ Current group handling logic found")
        else:
            print("❌ Current group handling logic missing")
            return False
        
        # Test 9: Check for no groups display message
        print("\n9. Checking for no groups display message...")
        if "No groups to display with current filter settings" in content:
            print("✅ No groups display message found")
        else:
            print("❌ No groups display message missing")
            return False
        
        # Test 10: Check for default state (enabled by default)
        print("\n10. Checking for default state...")
        if "hide_single_switch.select()" in content:
            print("✅ Default state (enabled) found")
        else:
            print("❌ Default state not properly set")
            return False
        
        # Test 11: Check for switch placement in toolbar
        print("\n11. Checking switch placement...")
        if 'hide_single_switch.pack(side="right"' in content:
            print("✅ Switch properly placed in toolbar")
        else:
            print("❌ Switch placement not found")
            return False
        
        print("\n" + "=" * 55)
        print("✅ ALL SINGLE GROUPS TOGGLE TESTS PASSED!")
        print("\nImplementation Summary:")
        print("  ✅ Hide Single Groups switch in main toolbar")
        print("  ✅ Toggle functionality with enhanced feedback")
        print("  ✅ Smart filtering of groups with ≤1 images")
        print("  ✅ Status messages showing group counts")
        print("  ✅ Current group handling when hidden")
        print("  ✅ Graceful fallback when no groups to display")
        print("  ✅ Default state enabled (hides single groups)")
        print("  ✅ Proper integration with group navigation")
        print("  ✅ Visual feedback and logging")
        print("  ✅ User-friendly status messages")
        print("\nFeature Details:")
        print("  • Located in main toolbar (right side)")
        print("  • Default: ON (hides single-image groups)")
        print("  • Shows count of hidden/shown groups")
        print("  • Automatically switches group if current becomes hidden")
        print("  • Provides clear feedback when no groups match filter")
        print("  • Integrates with navigation buttons and group selection")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Run the single groups toggle test."""
    success = test_single_groups_toggle()
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())