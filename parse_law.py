import json
import re
import os

def parse_law_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # تقسيم المحتوى بناءً على العناوين الرئيسية للأنظمة
    # نلاحظ أن الأنظمة تبدأ غالباً بـ "تنظيم" أو "نظام" أو "ضوابط"
    systems = []
    
    # محاولة تقسيم النص بناءً على فواصل الصفحات أو العناوين الكبيرة
    # سنستخدم نمطاً بسيطاً للتقسيم الأولي
    raw_sections = re.split(r'\n(?=ضوابط|تنظيم|نظام)\s+', content)
    
    for section in raw_sections:
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        system_name = lines[0].strip()
        articles = []
        
        # البحث عن المواد: "المادة الأولى"، "المادة الثانية"...
        # نستخدم regex للتعرف على "المادة" متبوعة بكلمة تدل على الرقم
        article_pattern = r'(المادة\s+(الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|الحادية\s+عشرة|الثانية\s+عشرة|الثالثة\s+عشرة|الرابعة\s+عشرة|الخامسة\s+عشرة|السادسة\s+عشرة|السابعة\s+عشرة|الثامنة\s+عشرة|التاسعة\s+عشرة|العشرون|الحادية\s+والعشرون|الثانية\s+والعشرون|الثالثة\s+والعشرون|الرابعة\s+والعشرون|الخامسة\s+والعشرون|السادسة\s+والعشرون|السابعة\s+والعشرون|الثامنة\s+والعشرون|التاسعة\s+والعشرون|الثلاثون|الأربعون|الخمسون|الستون|السبعون|الثمانون|التسعون|المائة))'
        
        current_article = None
        current_text = []
        
        for line in lines[1:]:
            match = re.search(article_pattern, line)
            if match:
                if current_article:
                    articles.append({
                        "id": current_article,
                        "text": "\n".join(current_text).strip()
                    })
                current_article = match.group(1)
                current_text = [line.replace(current_article, "").strip(":").strip()]
            else:
                if current_article:
                    current_text.append(line.strip())
        
        # إضافة آخر مادة
        if current_article:
            articles.append({
                "id": current_article,
                "text": "\n".join(current_text).strip()
            })
            
        if articles:
            systems.append({
                "system": system_name,
                "articles": articles
            })
            
    return systems

if __name__ == "__main__":
    input_file = "/home/ubuntu/Fuhrer/law_text.txt"
    output_file = "/home/ubuntu/Fuhrer/law_knowledge_base.json"
    
    if os.path.exists(input_file):
        data = parse_law_text(input_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Successfully parsed {len(data)} systems into {output_file}")
    else:
        print("Input file not found.")
