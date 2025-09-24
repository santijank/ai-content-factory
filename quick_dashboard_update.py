# quick_dashboard_update.py - อัพเดต dashboard ให้มีปุ่มกดได้
import os

def update_dashboard_html():
    """อัพเดต dashboard HTML"""
    os.makedirs('templates', exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>🚀 AI Content Factory</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; font-size: 2.5em; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        .status-bar { background: #4CAF50; color: white; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 30px; }
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 25px; }
        .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
        .card h3 { margin-top: 0; color: #2c3e50; font-size: 1.3em; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .button { background: linear-gradient(45deg, #3498db, #2980b9); color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; margin: 8px 5px; transition: all 0.3s ease; }
        .button:hover { background: linear-gradient(45deg, #2980b9, #3498db); transform: translateY(-2px); }
        .opportunity-item { border-left: 4px solid #e74c3c; padding: 15px; margin: 10px 0; background: #f8f9fa; border-radius: 0 8px 8px 0; }
        .stats { display: flex; justify-content: space-between; font-size: 0.9em; color: #666; margin-top: 8px; }
        .generate-btn { background: linear-gradient(45deg, #e74c3c, #c0392b); float: right; margin-top: 10px; }
        .loading { display: none; text-align: center; padding: 20px; font-style: italic; color: #666; }
        .success { background: #d4edda; color: #155724; padding: 15px; border-radius: 6px; margin: 10px 0; }
        .content-form { background: #e8f5e8; border: 2px solid #4CAF50; border-radius: 8px; padding: 20px; margin: 15px 0; display: none; }
        .content-result { background: #f0f8ff; border: 2px solid #3498db; border-radius: 8px; padding: 20px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">🚀 AI Content Factory</h1>
        <div class="status-bar">✅ System Status: Online (Database Ready)</div>
        
        <div class="dashboard-grid">
            <!-- Trend Monitor -->
            <div class="card">
                <h3>📊 Trend Monitor</h3>
                <p>ปรับปรุง trends จากหลายแหล่งข้อมูล</p>
                <button class="button" onclick="collectTrends()">🔄 Collect Trends</button>
                <button class="button" onclick="alert('Coming Soon!')">👀 View Trends</button>
                <div id="trends-loading" class="loading">🔄 กำลังเก็บข้อมูล...</div>
                <div id="trends-result"></div>
            </div>
            
            <!-- Content Opportunities -->
            <div class="card">
                <h3>💡 Content Opportunities</h3>
                <p>โอกาสสร้างเนื้อหาที่วิเคราะห์แล้ว</p>
                <button class="button" onclick="generateOpportunities()">💡 Generate Ideas</button>
                <button class="button" onclick="showAllOpportunities()">📋 View All</button>
                <div id="opportunities-loading" class="loading">🤖 กำลังวิเคราะห์...</div>
                <div id="opportunities-result"></div>
            </div>
            
            <!-- Content Generator -->
            <div class="card">
                <h3>🎬 Content Generator</h3>
                <p>สร้างเนื้อหาด้วย AI</p>
                <button class="button" onclick="showContentForm()">✨ Create Content</button>
                <button class="button" onclick="alert('Coming Soon!')">📄 View Content</button>
                
                <div id="content-form" class="content-form">
                    <h4>สร้างเนื้อหาใหม่</h4>
                    <label>หัวข้อ:</label><br>
                    <input type="text" id="content-idea" placeholder="เช่น: วิธีการเพิ่มผู้ติดตาม" style="width: 90%; padding: 8px; margin: 5px 0;"><br>
                    <label>Platform:</label><br>
                    <select id="content-platform" style="padding: 8px; margin: 5px 0;">
                        <option value="youtube">YouTube</option>
                        <option value="tiktok">TikTok</option>
                        <option value="instagram">Instagram</option>
                    </select><br>
                    <button class="button generate-btn" onclick="generateContent()">🎬 Generate Script</button>
                </div>
                
                <div id="content-loading" class="loading">🎬 กำลังสร้าง...</div>
                <div id="content-result"></div>
            </div>
        </div>
    </div>

    <script>
        // เก็บ trends
        async function collectTrends() {
            document.getElementById('trends-loading').style.display = 'block';
            try {
                const response = await fetch('/api/collect-trends', { method: 'POST' });
                const data = await response.json();
                document.getElementById('trends-loading').style.display = 'none';
                
                if (data.success) {
                    let html = `<div class="success">✅ เก็บ ${data.trends_collected} trends สำเร็จ!</div>`;
                    data.trends.slice(0, 3).forEach(trend => {
                        html += `<div style="border-left: 4px solid #3498db; padding: 10px; margin: 5px 0; background: #f8f9fa;">
                            <strong>${trend.topic}</strong><br>
                            <small>Score: ${trend.opportunity_score}/10 | Growth: ${trend.growth_rate}%</small>
                        </div>`;
                    });
                    document.getElementById('trends-result').innerHTML = html;
                }
            } catch (error) {
                document.getElementById('trends-loading').style.display = 'none';
                document.getElementById('trends-result').innerHTML = '<div style="color: red;">❌ Error: ' + error.message + '</div>';
            }
        }
        
        // แสดง opportunities
        function generateOpportunities() {
            document.getElementById('opportunities-loading').style.display = 'block';
            setTimeout(() => {
                document.getElementById('opportunities-loading').style.display = 'none';
                let html = '<div class="success">💡 พบ 5 โอกาสใหม่!</div>';
                
                const opportunities = [
                    { title: "Best AI Tools for Content Creators 2025", views: "650K", roi: "4.2" },
                    { title: "Why AI Video Editing Tools is Trending", views: "320K", roi: "4.9" },
                    { title: "Complete Guide to Short Form Video", views: "225K", roi: "4.3" },
                    { title: "Top 5 AI Video Tips for Beginners", views: "180K", roi: "4.1" },
                    { title: "AI Marketing Strategy 2025", views: "95K", roi: "3.8" }
                ];
                
                opportunities.forEach(opp => {
                    html += `<div class="opportunity-item">
                        <strong>${opp.title}</strong>
                        <div class="stats">
                            <span>Views: ${opp.views}</span>
                            <span>ROI: ${opp.roi}</span>
                        </div>
                        <button class="button generate-btn" onclick="selectOpportunity('${opp.title}')">
                            🎬 Create Content
                        </button>
                    </div>`;
                });
                
                document.getElementById('opportunities-result').innerHTML = html;
            }, 2000);
        }
        
        // เลือก opportunity
        function selectOpportunity(title) {
            document.getElementById('content-idea').value = title;
            document.getElementById('content-form').style.display = 'block';
            document.getElementById('content-form').scrollIntoView({ behavior: 'smooth' });
        }
        
        // แสดงฟอร์ม
        function showContentForm() {
            const form = document.getElementById('content-form');
            form.style.display = form.style.display === 'none' ? 'block' : 'none';
        }
        
        // สร้างเนื้อหา
        async function generateContent() {
            const idea = document.getElementById('content-idea').value;
            const platform = document.getElementById('content-platform').value;
            
            if (!idea) {
                alert('กรุณาใส่หัวข้อเนื้อหา');
                return;
            }
            
            document.getElementById('content-loading').style.display = 'block';
            
            try {
                const response = await fetch('/api/generate-content', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ idea: idea, platform: platform })
                });
                
                const data = await response.json();
                document.getElementById('content-loading').style.display = 'none';
                
                if (data.success) {
                    const content = data.content;
                    let html = `<div class="content-result">
                        <h4>🎬 เนื้อหาที่สร้างสำเร็จ!</h4>
                        <p><strong>📺 Title:</strong> ${content.title}</p>
                        <p><strong>📝 Description:</strong> ${content.description}</p>
                        <p><strong>🎯 Hook:</strong> ${content.script.hook}</p>
                        <p><strong>📄 Content:</strong> ${content.script.main_content}</p>
                        <p><strong>📢 CTA:</strong> ${content.script.cta}</p>
                        <p><strong>🏷️ Tags:</strong> ${content.hashtags.join(' ')}</p>
                        <p><strong>⏱️ Duration:</strong> ${content.estimated_duration}</p>
                    </div>`;
                    
                    document.getElementById('content-result').innerHTML = html;
                }
            } catch (error) {
                document.getElementById('content-loading').style.display = 'none';
                document.getElementById('content-result').innerHTML = '<div style="color: red;">❌ Error: ' + error.message + '</div>';
            }
        }
        
        function showAllOpportunities() {
            generateOpportunities();
        }
        
        // เริ่มต้นแสดง opportunities
        window.onload = function() {
            setTimeout(generateOpportunities, 1000);
        };
    </script>
</body>
</html>'''
    
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Dashboard updated with clickable buttons!")
    print("🔄 Please refresh your browser (Ctrl+F5)")

if __name__ == "__main__":
    update_dashboard_html()