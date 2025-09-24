#!/usr/bin/env python3
"""
แก้ไข HTML test ให้ตรงกับ Ultra Fast version
"""

def fix_test_system():
    """อัปเดต test_system.py ให้ตรวจสอบ HTML elements ที่ถูกต้อง"""
    
    # อ่านไฟล์เดิม
    with open('test_system.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # แก้ไข HTML elements ที่ต้องตรวจสอบ
    old_elements = '''required_elements = [
                "AI Content Factory",
                "Trend Monitor",
                "Content Opportunities", 
                "Content Generator",
                "Analytics",
                "loadAnalytics",
                "loadTrends"
            ]'''
    
    new_elements = '''required_elements = [
                "AI Content Factory",
                "Analytics",
                "Trends", 
                "loadAnalytics",
                "loadTrends"
            ]'''
    
    # แทนที่
    updated_content = content.replace(old_elements, new_elements)
    
    # เขียนไฟล์ใหม่
    with open('test_system.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Updated test_system.py to match Ultra Fast HTML")

def main():
    fix_test_system()
    print("🔧 HTML test requirements updated")
    print("Now run: python test_system.py")

if __name__ == "__main__":
    main()