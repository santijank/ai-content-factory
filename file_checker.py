# file_checker.py - ตรวจสอบไฟล์ที่จำเป็นสำหรับ AI Content Factory
import os
import sys

def check_file_structure():
    """ตรวจสอบโครงสร้างไฟล์ที่จำเป็น"""
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Current directory: {current_dir}")
    print("=" * 80)
    
    # รายการไฟล์ที่จำเป็น
    required_files = [
        # Root files
        "main_app.py",
        ".env",
        
        # Content Engine structure
        "content-engine/__init__.py",
        "content-engine/ai_services/__init__.py",
        "content-engine/ai_services/text_ai/__init__.py",
        "content-engine/ai_services/text_ai/groq_service.py",
        "content-engine/services/__init__.py",
        "content-engine/services/ai_director.py",
        "content-engine/models/__init__.py",
        "content-engine/models/quality_tier.py",
        "content-engine/models/content_plan.py",
        
        # Templates (optional)
        "templates/dashboard.html",
        "templates/base.html",
        
        # Static files (optional)
        "static/css/dashboard.css",
        "static/js/dashboard.js"
    ]
    
    # ตรวจสอบไฟล์แต่ละตัว
    results = {}
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        full_path = os.path.join(current_dir, file_path)
        exists = os.path.exists(full_path)
        
        if exists:
            file_size = os.path.getsize(full_path)
            status = f"✅ EXISTS ({file_size} bytes)"
            existing_files.append(file_path)
        else:
            status = "❌ MISSING"
            missing_files.append(file_path)
        
        results[file_path] = {
            'exists': exists,
            'full_path': full_path,
            'status': status
        }
        
        print(f"{status:<20} {file_path}")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY:")
    print(f"✅ Existing files: {len(existing_files)}")
    print(f"❌ Missing files: {len(missing_files)}")
    print(f"📊 Total checked: {len(required_files)}")
    
    if missing_files:
        print(f"\n🔧 MISSING FILES TO CREATE:")
        for file_path in missing_files:
            print(f"   - {file_path}")
            
        # แสดงคำแนะนำการสร้างไฟล์
        print(f"\n💡 CREATE MISSING FILES:")
        for file_path in missing_files:
            if file_path.endswith('__init__.py'):
                print(f"   touch {file_path}")
            elif 'groq_service.py' in file_path:
                print(f"   # Create {file_path} with GroqService class")
            elif 'ai_director.py' in file_path:
                print(f"   # Create {file_path} with AIDirector class")
            elif 'quality_tier.py' in file_path:
                print(f"   # Create {file_path} with QualityTier enum")
            elif 'content_plan.py' in file_path:
                print(f"   # Create {file_path} with ContentPlan class")
    
    return results

def check_imports():
    """ตรวจสอบว่า import ได้หรือไม่"""
    print("\n" + "=" * 80)
    print("TESTING IMPORTS:")
    
    # เพิ่ม content-engine ใน Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    content_engine_path = os.path.join(current_dir, 'content-engine')
    if content_engine_path not in sys.path:
        sys.path.insert(0, content_engine_path)
    
    imports_to_test = [
        ("ai_services.text_ai.groq_service", "GroqService"),
        ("services.ai_director", "AIDirector"),
        ("models.quality_tier", "QualityTier"),
        ("models.content_plan", "ContentPlan")
    ]
    
    import_results = {}
    
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            status = f"✅ SUCCESS - {class_name} imported"
            import_results[module_name] = True
        except ImportError as e:
            status = f"❌ IMPORT ERROR - {e}"
            import_results[module_name] = False
        except AttributeError as e:
            status = f"❌ ATTRIBUTE ERROR - {e}"
            import_results[module_name] = False
        except Exception as e:
            status = f"❌ OTHER ERROR - {e}"
            import_results[module_name] = False
            
        print(f"{status}")
    
    return import_results

def check_content_engine_structure():
    """ตรวจสอบโครงสร้าง content-engine โดยละเอียด"""
    print("\n" + "=" * 80)
    print("CONTENT-ENGINE STRUCTURE:")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    content_engine_dir = os.path.join(current_dir, 'content-engine')
    
    if not os.path.exists(content_engine_dir):
        print("❌ content-engine directory does not exist!")
        return False
    
    print(f"📁 content-engine directory: {content_engine_dir}")
    
    # แสดงโครงสร้างไฟล์ทั้งหมดใน content-engine
    for root, dirs, files in os.walk(content_engine_dir):
        level = root.replace(content_engine_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}📁 {os.path.basename(root)}/")
        sub_indent = ' ' * 2 * (level + 1)
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            print(f"{sub_indent}📄 {file} ({file_size} bytes)")
    
    return True

def generate_missing_file_commands():
    """สร้างคำสั่งสำหรับสร้างไฟล์ที่ขาดหาย"""
    print("\n" + "=" * 80)
    print("COMMANDS TO CREATE MISSING FILES:")
    
    commands = [
        "# Create directories",
        "mkdir -p content-engine/ai_services/text_ai",
        "mkdir -p content-engine/services", 
        "mkdir -p content-engine/models",
        "mkdir -p templates",
        "mkdir -p static/css",
        "mkdir -p static/js",
        "",
        "# Create __init__.py files",
        "touch content-engine/__init__.py",
        "touch content-engine/ai_services/__init__.py",
        "touch content-engine/ai_services/text_ai/__init__.py",
        "touch content-engine/services/__init__.py",
        "touch content-engine/models/__init__.py",
        "",
        "# Main Python files need to be created with content:",
        "# - content-engine/ai_services/text_ai/groq_service.py",
        "# - content-engine/services/ai_director.py",
        "# - content-engine/models/quality_tier.py",
        "# - content-engine/models/content_plan.py"
    ]
    
    for cmd in commands:
        print(cmd)

if __name__ == "__main__":
    print("🔍 AI Content Factory File Structure Checker")
    print("=" * 80)
    
    # ตรวจสอบไฟล์
    file_results = check_file_structure()
    
    # ตรวจสอบโครงสร้าง content-engine
    check_content_engine_structure()
    
    # ตรวจสอบ imports
    import_results = check_imports()
    
    # แสดงคำสั่งสร้างไฟล์
    generate_missing_file_commands()
    
    print("\n" + "=" * 80)
    print("🎯 NEXT STEPS:")
    print("1. Create missing directories and __init__.py files")
    print("2. Create the main Python class files with proper content")
    print("3. Run this checker again to verify")
    print("4. Test main_app.py imports")