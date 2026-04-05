import os
import json

def update_doctypes(root_dir):
    for root, dirs, files in os.walk(root_dir):
        if 'doctype' in root.lower() or 'report' in root.lower() or 'page' in root.lower():
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                        except Exception as e:
                            print(f"Error loading {file_path}: {e}")
                            continue
                    
                    if data.get('doctype') in ['DocType', 'Report', 'Page']:
                        if data.get('module') != 'Marketing':
                            print(f"Updating {file_path}...")
                            data['module'] = 'Marketing'
                            with open(file_path, 'w', encoding='utf-8') as f:
                                # Ensure we don't break formatting
                                json.dump(data, f, indent=1, ensure_ascii=False)

if __name__ == "__main__":
    target_dir = r"c:\Users\bizit\OneDrive\Documents\BISMALLAH BIZ PROJECTS INSHA'ALLAH\BISMALLAH ETHIOBIZ INSHA'ALLAH\BISMALLAH ETHIOBIZ INSTALLATION INSHA'ALLAH\BISMALLAH ETHIBIZ STAGING INSHA'ALLAH\bizmarketing\bizmarketing"
    update_doctypes(target_dir)
    print("BISMILLAH DONE!")
