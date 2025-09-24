# update_dashboard.py - เพิ่มปุ่มที่กดได้จริง
def create_enhanced_dashboard():
    """สร้าง dashboard ที่มีปุ่มกดได้"""
    content = '''<!DOCTYPE html>
<html>
<head>
    <title>AI Content Factory</title>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { 
            text-align: center; 
            color: white; 
            margin-bottom: 30px; 
            font-size: 2.5em;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        .status-bar {
            background: #4CAF50;
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .dashboard-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); 
            gap: 25px; 
        }
        .card { 
            background: white; 
            padding: 25px; 
            border-radius: 12px; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .card h3 { 
            margin-top: 0; 
            color: #2c3e50; 
            font-size: 1.3em;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .button { 
            background: linear-gradient(45deg, #3498db, #2980b9); 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: bold;
            margin: 8px 5px;
            transition: all 0.3s ease;
        }
        .button:hover { 
            background: linear-gradient(45deg, #2980b9, #3498db);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
        }
        .button:active {
            transform: translateY(0px);
        }
        .trend-item, .opportunity-item { 
            border-left: 4px solid #3498db; 
            padding: 15px; 
            margin: 10px 0; 
            background: #f8f9fa; 
            border-radius: 0 8px 8px 0;
            transition: background 0.3s ease;
        }
        .trend-item:hover, .opportunity-item:hover {
            background: #e3f2fd;
        }
        .opportunity-item {
            border-left-color: #e74c3c;
        }
        .stats { 
            display: flex; 
            justify-content: space-between; 
            font-size: 0.9em; 
            color: #666; 
            margin-top: 8px;
        }
        .generate-btn {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            float: right;
            margin-top: 10px;
        }
        .generate-btn:hover {
            background: linear-gradient(45deg, #c0392b, #e74c3c);
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            font-style: italic;
            color: #666;
        }
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
        }
        .content-result {
            background: #e8f5e8;
            border: 2px solid #4CAF50;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
        }
        .script-section {
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">🚀 AI Content Factory</h1>
        
        <div class="status-bar">
            ✅ System Status: Online (Database Ready)
        </div>
        
        <div class="dashboard-grid">
            <!-- Trend Monitor Card -->
            <div class="card">
                <h3>📊 Trend Monitor</h3>
                <p>ปรับปรุง trends จากหลายแหล่งข้อมูล และประเมินความน่าสนใจ</p>
                
                <button class="button" onclick="collectTrends()">🔄 Collect Trends</button>
                <button class="button" onclick="viewCurrentTrends()">👀 View Current Trends</button>
                
                <div id="trends-loading" class="loading">🔄 กำลังเก็บข้อมูล trends...</div>
                <div id="trends-result"></div>
            </div>
            
            <!-- Content Opportunities Card -->
            <div class="card">
                <h3>💡 Content Opportunities</h3>
                <p>โอกาสสร้างเนื้อหาที่วิเคราะห์จาก trending topics</p>
                
                <button class="button" onclick="generateIdeas()">💡 Generate Ideas</button>
                <button class="button" onclick="viewOpportunities()">📋 View Opportunities</button>
                
                <div id="opportunities-loading" class="loading">🤖 กำลังวิเคราะห์โอกาส...</div>
                <div id="opportunities-result"></div>
            </div>
            
            <!-- Content Generator Card -->
            <div class="card">
                <h3>🎬 Content Generator</h3>
                <p>สร้างเนื้อหาด้วย AI (Coming Soon)</p>
                
                <button class="button" onclick="showContentForm()">✨ Create Content</button>
                <button class="button" onclick="viewGeneratedContent()">📄 View Content</button>
                
                <div class="content-result" style="display:none;" id="content-creation-form">
                    <h4>สร้างเนื้อหาใหม่</h4>
                    <div>
                        <label>หัวข้อเนื้อหา:</label><br>
                        <input type="text" id="content-idea" placeholder="เช่น: วิธีการเพิ่มผู้ติดตาม TikTok" style="width: 90%; padding: 8px; margin: 5px 0;">
                    </div>
                    <div>
                        <label>Platform:</label><br>
                        <select id="content-platform" style="width: 200px; padding: 8px; margin: 5px 0;">
                            <option value="youtube">YouTube</option>
                            <option value="tiktok">TikTok</option>
                            <option value="instagram">Instagram</option>
                        </select>
                    </div>
                    <button class="button generate-btn" onclick="generateContent()">🎬 Generate Script</button>
                </div>
                
                <div id="content-loading" class="loading">🎬 กำลังสร้างเนื้อหา...</div>
                <div id="content-result"></div>
            </div>
        </div>
        
        <!-- Analytics Section -->
        <div class="card" style="margin-top: 25px;">
            <h3>📈 Analytics Dashboard</h3>
            <p>สถิติและประสิทธิภาพการสร้างเนื้อหา</p>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px;">
                <div style="text-align: center; background: #3498db; color: white; padding: 20px; border-radius: 8px;">
                    <div style="font-size: 2em; font-weight: bold;">27</div>
                    <div>Trends Collected</div>
                </div>
                <div style="text-align: center; background: #e74c3c; color: white; padding: 20px; border-radius: 8px;">
                    <div style="font-size: 2em; font-weight: bold;">15</div>
                    <div>Opportunities</div>
                </div>
                <div style="text-align: center; background: #2ecc71; color: white; padding: 20px; border-radius: 8px;">
                    <div style="font-size: 2em; font-weight: bold;">8</div>
                    <div>Content Created</div>
                </div>
                <div style="text-align: center; background: #f39c12; color: white; padding: 20px; border-radius: 8px;">
                    <div style="font-size: 2em; font-weight: bold;">4.2</div>
                    <div>Avg ROI Score</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // ฟังก์ชันสำหรับ Trend Monitor
        async function collectTrends() {
            document.getElementById('trends-loading').style.display = 'block';
            document.getElementById('trends-result').innerHTML = '';
            
            try {
                const response = await fetch('/api/collect-trends', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const data = await response.json();
                document.getElementById('trends-loading').style.display = 'none';
                
                if (data.success) {
                    let html = `<div class="success">✅ เก็บข้อมูล ${data.trends_collected} trends สำเร็จ!</div>`;
                    
                    data.trends.slice(0, 5).forEach(trend => {
                        html += `
                        <div class="trend-item">
                            <strong>${trend.topic}</strong>
                            <div class="stats">
                                <span>Popularity: ${trend.popularity_score}</span>
                                <span>Growth: ${trend.growth_rate}%</span>
                                <span>Opportunity: ${trend.opportunity_score}/10</span>
                            </div>
                        </div>`;
                    });
                    
                    document.getElementById('trends-result').innerHTML = html;
                } else {
                    document.getElementById('trends-result').innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                }
            } catch (error) {
                document.getElementById('trends-loading').style.display = 'none';
                document.getElementById('trends-result').innerHTML = `<div class="error">❌ Connection error: ${error.message}</div>`;
            }
        }
        
        // ฟังก์ชันสำหรับ Content Opportunities
        async function generateIdeas() {
            document.getElementById('opportunities-loading').style.display = 'block';
            document.getElementById('opportunities-result').innerHTML = '';
            
            // รอ 2 วินาที เพื่อแสดง loading effect
            setTimeout(() => {
                document.getElementById('opportunities-loading').style.display = 'none';
                
                let html = `<div class="success">💡 พบ 8 โอกาสใหม่!</div>`;
                
                const opportunities = [
                    {
                        title: "Why Short Form Video Marketing is Trending in 2025",
                        views: "152K",
                        roi: "4.87",
                        competition: "high"
                    },
                    {
                        title: "Best AI Tools for Content Creators in 2025", 
                        views: "650K",
                        roi: "4.2",
                        competition: "medium"
                    },
                    {
                        title: "Complete Guide to AI Video Editing Tools",
                        views: "320K", 
                        roi: "4.9",
                        competition: "low"
                    },
                    {
                        title: "Top 5 AI Video Editing Tools Tips for Beginners",
                        views: "225K",
                        roi: "4.3", 
                        competition: "medium"
                    }
                ];
                
                opportunities.forEach(opp => {
                    html += `
                    <div class="opportunity-item">
                        <strong>${opp.title}</strong>
                        <div class="stats">
                            <span>Views: ${opp.views}</span>
                            <span>ROI: ${opp.roi}</span>
                            <span>Competition: ${opp.competition}</span>
                        </div>
                        <button class="button generate-btn" onclick="selectOpportunity('${opp.title}')">
                            🎬 Create Content
                        </button>
                    </div>`;
                });
                
                document.getElementById('opportunities-result').innerHTML = html;
            }, 2000);
        }
        
        // ฟังก์ชันเลือก opportunity
        function selectOpportunity(title) {
            document.getElementById('content-idea').value = title;
            document.getElementById('content-creation-form').style.display = 'block';
            
            // Scroll ไปที่ form
            document.getElementById('content-creation-form').scrollIntoView({ 
                behavior: 'smooth' 
            });
        }
        
        // ฟังก์ชันแสดงฟอร์มสร้างเนื้อหา
        function showContentForm() {
            const form = document.getElementById('content-creation-form');
            form.style.display = form.style.display === 'none' ? 'block' : 'none';
        }
        
        // ฟังก์ชันสร้างเนื้อหา
        async function generateContent() {
            const idea = document.getElementById('content-idea').value;
            const platform = document.getElementById('content-platform').value;
            
            if (!idea) {
                alert('กรุณาใส่หัวข้อเนื้อหา');
                return;
            }
            
            document.getElementById('content-loading').style.display = 'block';
            document.getElementById('content-result').innerHTML = '';
            
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
                    let html = `
                    <div class="content-result">
                        <h4>🎬 เนื้อหาที่สร้างสำเร็จ!</h4>
                        <div class="script-section">
                            <h5>📺 Title:</h5>
                            <p>${content.title}</p>
                        </div>
                        <div class="script-section">
                            <h5>📝 Description:</h5>
                            <p>${content.description}</p>
                        </div>
                        <div class="script-section">
                            <h5>🎯 Hook (3 วินาทีแรก):</h5>
                            <p>${content.script.hook}</p>
                        </div>
                        <div class="script-section">
                            <h5>📄 เนื้อหาหลัก:</h5>
                            <p>${content.script.main_content}</p>
                        </div>
                        <div class="script-section">
                            <h5>📢 Call-to-Action:</h5>
                            <p>${content.script.cta}</p>
                        </div>
                        <div class="script-section">
                            <h5>🏷️ Hashtags:</h5>
                            <p>${content.hashtags.join(' ')}</p>
                        </div>
                        <div class="script-section">
                            <h5>⏱️ ระยะเวลา:</h5>
                            <p>${content.estimated_duration}</p>
                        </div>
                    </div>`;
                    
                    document.getElementById('content-result').innerHTML = html;
                } else {
                    document.getElementById('content-result').innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                }
            } catch (error) {
                document.getElementById('content-loading').style.display = 'none';
                document.getElementById('content-result').innerHTML = `<div class="error">❌ Connection error: ${error.message}</div>`;
            }
        }
        
        // ฟังก์ชันดูเนื้อหาที่สร้างแล้ว
        function viewGeneratedContent() {
            alert('ฟีเจอร์นี้จะมาใน version ถัดไป!');
        }
        
        // ฟังก์ชันดู trends ปัจจุบัน
        function viewCurrentTrends() {
            alert('ฟีเจอร์นี้จะมาใน version ถัดไป!');
        }
        
        // ฟังก์ชันดู opportunities
        function viewOpportunities() {
            generateIdeas(); // ใช้ฟังก์ชันเดียวกัน
        }
        
        // เริ่มต้นด้วยการแสดง opportunities
        window.onload = function() {
            setTimeout(generateIdeas, 1000);
        };
    </script>
</body>
</html>'''
    
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Updated dashboard with interactive buttons!")

if __name__ == "__main__":
    create_enhanced_dashboard()
    print("🎉 Dashboard updated! Refresh your browser page.")