import re
import json

def clean_ts_to_json(ts_file, json_out):
    with open(ts_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extract the campaignWeeks array content
    # We'll match everything inside `export const campaignWeeks: WeekData[] = [` and `];`
    match = re.search(r'export const campaignWeeks: WeekData\[\] = \[(.*?)\];\n', content, flags=re.DOTALL)
    if not match:
        print("Could not find campaignWeeks array")
        return
        
    weeks_body = match.group(1)
    
    # Very manual extraction of posts
    posts = []
    
    post_blocks = re.findall(r'\{\s*id:.*?week:.*?\s*\},?', weeks_body, flags=re.DOTALL)
    for pb in post_blocks:
        post = {}
        
        id_m = re.search(r'id:\s*"([^"]+)"', pb)
        if id_m: post['id'] = id_m.group(1)
        
        date_m = re.search(r'date:\s*"([^"]+)"', pb)
        if date_m: post['date'] = date_m.group(1)
        
        plat_m = re.search(r'platform:\s*\[(.*?)\]', pb)
        if plat_m:
            plats = [p.strip().strip('"').strip("'") for p in plat_m.group(1).split(',')]
            post['platform'] = plats
            
        pillar_m = re.search(r'pillar:\s*"([^"]+)"', pb)
        if pillar_m: post['pillar'] = pillar_m.group(1)
        
        ctype_m = re.search(r'contentType:\s*"([^"]+)"', pb)
        if ctype_m: post['contentType'] = ctype_m.group(1)
        
        title_m = re.search(r'title:\s*"([^"]+)"', pb)
        if title_m: post['title'] = title_m.group(1)
        
        content_m = re.search(r'content:\s*`(.*?)`', pb, flags=re.DOTALL)
        if content_m: post['content'] = content_m.group(1)
        
        img_url_m = re.search(r'imageUrl:\s*"([^"]+)"', pb)
        if img_url_m: post['imageUrl'] = img_url_m.group(1)
        
        img_prmpt_m = re.search(r'imagePrompt:\s*"([^"]+)"', pb)
        if img_prmpt_m: post['imagePrompt'] = img_prmpt_m.group(1)
        
        out_m = re.search(r'expectedOutcome:\s*"([^"]+)"', pb)
        if out_m: post['expectedOutcome'] = out_m.group(1)
        
        cta_m = re.search(r'cta:\s*`(.*?)`', pb, flags=re.DOTALL)
        if cta_m: post['cta'] = cta_m.group(1)
        
        week_m = re.search(r'week:\s*(\d+)', pb)
        if week_m: post['week'] = int(week_m.group(1))
        
        posts.append(post)
        
    print(f"Extracted {len(posts)} posts.")
    with open(json_out, 'w', encoding='utf-8') as f:
        json.dump({"posts": posts}, f, indent=2)

if __name__ == "__main__":
    ts = r"C:\BISMALLAH BIZSYSTEMS INSHA'ALLAH\BISMALLAH_BizMarketing_New_INSHAALLAH\Week 1-4 Social Media Campaign Plan Development\Campaign_Post_Website\campaignData.ts"
    jsn = r"C:\Users\bizit\OneDrive\Documents\BISMALLAH BIZ PROJECTS INSHA'ALLAH\BISMALLAH ETHIOBIZ INSHA'ALLAH\BISMALLAH ETHIOBIZ INSTALLATION INSHA'ALLAH\BISMALLAH ETHIBIZ STAGING INSHA'ALLAH\bizmarketing\campaign_data.json"
    clean_ts_to_json(ts, jsn)
