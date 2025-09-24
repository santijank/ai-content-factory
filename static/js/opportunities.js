/**
 * Opportunities Page JavaScript
 * ตำแหน่งไฟล์: static/js/opportunities.js
 * 
 * จัดการ interactions และ real-time updates สำหรับหน้า Opportunities
 */

let contentCreationModal;
let opportunityDetailModal;
let selectedOpportunities = new Set();
let currentOpportunityData = null;

// Quality tier pricing
const qualityTierPricing = {
    budget: { cost: 25, time: 30, multiplier: 0.8 },
    balanced: { cost: 75, time: 45, multiplier: 1.0 },
    premium: { cost: 200, time: 90, multiplier: 1.3 }
};

document.addEventListener('DOMContentLoaded', function() {
    initializeModals();
    initializeEventListeners();
    updateBulkActions();
});

function initializeModals() {
    contentCreationModal = new bootstrap.Modal(document.getElementById('contentCreationModal'));
    opportunityDetailModal = new bootstrap.Modal(document.getElementById('opportunityDetailModal'));
}

function initializeEventListeners() {
    // Quality tier change handler
    document.getElementById('qualityTier')?.addEventListener('change', updateCostEstimate);
    
    // Platform selection change handler
    document.querySelectorAll('input[id^="platform-"]').forEach(checkbox => {
        checkbox.addEventListener('change', updateCostEstimate);
    });
    
    // Content type change handler
    document.getElementById('contentType')?.addEventListener('change', updateCostEstimate);
}

function clearFilters() {
    const form = document.getElementById('filterForm');
    form.querySelectorAll('select').forEach(select => {
        select.selectedIndex = 0;
    });
    form.querySelector('input[name="search"]').value = '';
    form.submit();
}

function updateBulkActions() {
    const checkboxes = document.querySelectorAll('.opportunity-checkbox:checked');
    const bulkActions = document.getElementById('bulkActions');
    const selectedCount = document.getElementById('selectedCount');
    
    selectedOpportunities.clear();
    checkboxes.forEach(cb => selectedOpportunities.add(cb.value));
    
    selectedCount.textContent = selectedOpportunities.size;
    
    if (selectedOpportunities.size > 0) {
        bulkActions.classList.add('show');
    } else {
        bulkActions.classList.remove('show');
    }
}

function clearSelection() {
    document.querySelectorAll('.opportunity-checkbox').forEach(cb => {
        cb.checked = false;
    });
    updateBulkActions();
}

async function createContentFromOpportunity(opportunityId) {
    try {
        // Load opportunity data
        const response = await fetch(`/api/opportunities/${opportunityId}`);
        const opportunity = await response.json();
        
        if (!response.ok) {
            throw new Error(opportunity.error || 'Failed to load opportunity');
        }
        
        currentOpportunityData = opportunity;
        populateContentCreationModal(opportunity);
        contentCreationModal.show();
        
    } catch (error) {
        showNotification(`ไม่สามารถโหลดข้อมูลได้: ${error.message}`, 'error');
    }
}

function populateContentCreationModal(opportunity) {
    document.getElementById('selectedOpportunityId').value = opportunity.id;
    
    // Populate opportunity summary
    const summaryHtml = `
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <h6 class="mb-1">${opportunity.suggested_angle}</h6>
                <p class="text-muted mb-1">From: ${opportunity.trend?.topic || 'Unknown trend'}</p>
                <div class="d-flex gap-2">
                    <span class="badge bg-success">ROI: ${opportunity.estimated_roi.toFixed(1)}x</span>
                    <span class="badge bg-primary">${opportunity.estimated_views.toLocaleString()} views</span>
                    <span class="badge bg-info">${opportunity.competition_level} competition</span>
                </div>
            </div>
            <div class="text-end">
                <div class="h5 text-primary mb-0">${opportunity.priority_score.toFixed(1)}</div>
                <small class="text-muted">Priority</small>
            </div>
        </div>
    `;
    
    document.getElementById('opportunitySummary').innerHTML = summaryHtml;
    
    // Update cost estimate
    updateCostEstimate();
}

function updateCostEstimate() {
    if (!currentOpportunityData) return;
    
    const qualityTier = document.getElementById('qualityTier')?.value || 'balanced';
    const selectedPlatforms = Array.from(document.querySelectorAll('input[id^="platform-"]:checked')).length;
    
    const basePricing = qualityTierPricing[qualityTier];
    const platformMultiplier = Math.max(1, selectedPlatforms * 0.5);
    const roiMultiplier = currentOpportunityData.estimated_roi || 1;
    
    const estimatedCost = Math.round(basePricing.cost * platformMultiplier);
    const estimatedTime = Math.round(basePricing.time * platformMultiplier);
    const estimatedROI = (roiMultiplier * basePricing.multiplier).toFixed(1);
    
    document.getElementById('estimatedCost').textContent = `฿${estimatedCost}`;
    document.getElementById('estimatedTime').textContent = `${estimatedTime} min`;
    document.getElementById('estimatedROI').textContent = `${estimatedROI}x`;
}

async function submitContentCreation() {
    const opportunityId = document.getElementById('selectedOpportunityId').value;
    const qualityTier = document.getElementById('qualityTier').value;
    const contentType = document.getElementById('contentType').value;
    const customInstructions = document.getElementById('customInstructions').value;
    
    // Get selected platforms
    const platforms = [];
    document.querySelectorAll('input[id^="platform-"]:checked').forEach(checkbox => {
        platforms.push(checkbox.value);
    });
    
    if (platforms.length === 0) {
        showNotification('กรุณาเลือกแพลตฟอร์มอย่างน้อย 1 แพลตฟอร์ม', 'warning');
        return;
    }
    
    contentCreationModal.hide();
    
    try {
        await createContent(opportunityId, qualityTier, platforms, {
            contentType,
            customInstructions
        });
        
        // Update opportunity status to 'selected'
        await updateOpportunityStatus(opportunityId, 'selected');
        
    } catch (error) {
        showNotification(`ไม่สามารถสร้างเนื้อหาได้: ${error.message}`, 'error');
    }
}

async function bulkCreateContent() {
    if (selectedOpportunities.size === 0) {
        showNotification('กรุณาเลือก opportunities ที่ต้องการสร้างเนื้อหา', 'warning');
        return;
    }
    
    if (!confirm(`คุณต้องการสร้างเนื้อหาจาก ${selectedOpportunities.size} opportunities?`)) {
        return;
    }
    
    showLoading('สร้างเนื้อหาจำนวนมาก', `กำลังสร้างเนื้อหา ${selectedOpportunities.size} รายการ...`);
    
    let successCount = 0;
    let failCount = 0;
    
    for (const opportunityId of selectedOpportunities) {
        try {
            await createContent(opportunityId, 'balanced', ['youtube']); // Default settings
            await updateOpportunityStatus(opportunityId, 'selected');
            successCount++;
        } catch (error) {
            console.error(`Failed to create content for ${opportunityId}:`, error);
            failCount++;
        }
    }
    
    hideLoading();
    
    if (successCount > 0) {
        showNotification(`สร้างเนื้อหาสำเร็จ ${successCount} รายการ`, 'success');
    }
    
    if (failCount > 0) {
        showNotification(`ไม่สามารถสร้างเนื้อหาได้ ${failCount} รายการ`, 'warning');
    }
    
    clearSelection();
    setTimeout(() => location.reload(), 2000);
}

async function bulkUpdateStatus(newStatus) {
    if (selectedOpportunities.size === 0) {
        showNotification('กรุณาเลือก opportunities ที่ต้องการอัปเดต', 'warning');
        return;
    }
    
    try {
        const promises = Array.from(selectedOpportunities).map(id => 
            updateOpportunityStatus(id, newStatus)
        );
        
        await Promise.all(promises);
        
        showNotification(`อัปเดตสถานะเป็น ${newStatus} สำเร็จ`, 'success');
        clearSelection();
        setTimeout(() => location.reload(), 1000);
        
    } catch (error) {
        showNotification('ไม่สามารถอัปเดตสถานะได้', 'error');
    }
}

async function updateOpportunityStatus(opportunityId, status) {
    const response = await fetch(`/api/opportunities/${opportunityId}/status`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to update status');
    }
    
    return response.json();
}

async function analyzeOpportunity(opportunityId) {
    showLoading('วิเคราะห์โอกาส', 'กำลังวิเคราะห์โอกาสนี้เพิ่มเติม...');
    
    try {
        const response = await fetch(`/api/opportunities/${opportunityId}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze opportunity');
        }
        
        hideLoading();
        showNotification('เริ่มการวิเคราะห์แล้ว ผลลัพธ์จะแสดงเมื่อเสร็จสิ้น', 'info');
        
    } catch (error) {
        hideLoading();
        showNotification(`ไม่สามารถวิเคราะห์ได้: ${error.message}`, 'error');
    }
}

async function viewOpportunityDetail(opportunityId) {
    try {
        const response = await fetch(`/api/opportunities/${opportunityId}`);
        const opportunity = await response.json();
        
        if (!response.ok) {
            throw new Error(opportunity.error || 'Failed to load opportunity');
        }
        
        displayOpportunityDetail(opportunity);
        opportunityDetailModal.show();
        
    } catch (error) {
        showNotification(`ไม่สามารถโหลดรายละเอียดได้: ${error.message}`, 'error');
    }
}

function displayOpportunityDetail(opportunity) {
    const content = document.getElementById('opportunityDetailContent');
    
    const analysisData = opportunity.analysis_data || {};
    const trend = opportunity.trend || {};
    
    content.innerHTML = `
        <div class="row">
            <div class="col-md-8">
                <div class="card mb-4">
                    <div class="card-body">
                        <h5 class="card-title">${opportunity.suggested_angle}</h5>
                        <p class="text-muted">Status: <span class="badge bg-primary">${opportunity.status}</span></p>
                        
                        <h6 class="mt-4">Content Strategy</h6>
                        <div class="bg-light p-3 rounded">
                            ${analysisData.strategy || 'ยังไม่มีกลยุทธ์เนื้อหา'}
                        </div>
                        
                        <h6 class="mt-4">Target Keywords</h6>
                        <div>
                            ${analysisData.keywords ? 
                                analysisData.keywords.map(k => `<span class="badge bg-secondary me-1">${k}</span>`).join('') :
                                'ยังไม่มี keywords'
                            }
                        </div>
                        
                        <h6 class="mt-4">Content Ideas</h6>
                        <ul class="list-unstyled">
                            ${analysisData.content_ideas ? 
                                analysisData.content_ideas.map(idea => `<li class="mb-2"><i class="fas fa-lightbulb text-warning me-2"></i>${idea}</li>`).join('') :
                                '<li>ยังไม่มีไอเดียเนื้อหา</li>'
                            }
                        </ul>
                        
                        <h6 class="mt-4">Competition Analysis</h6>
                        <div class="bg-light p-3 rounded">
                            ${analysisData.competition_analysis || 'ยังไม่มีการวิเคราะห์คู่แข่ง'}
                        </div>
                    </div>
                </div>
                
                ${trend.topic ? `
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">Source Trend</h6>
                        <h5>${trend.topic}</h5>
                        <p class="text-muted">Category: ${trend.category || 'ไม่มีหมวดหมู่'}</p>
                        <p class="text-muted">Source: ${trend.source}</p>
                        
                        <div class="row">
                            <div class="col-6">
                                <div class="text-center">
                                    <div class="h4 text-primary">${trend.popularity_score?.toFixed(1) || '0'}/10</div>
                                    <div class="small text-muted">Popularity</div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="text-center">
                                    <div class="h4 text-success">+${trend.growth_rate?.toFixed(1) || '0'}%</div>
                                    <div class="small text-muted">Growth</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>
            
            <div class="col-md-4">
                <div class="card mb-3">
                    <div class="card-body">
                        <h6 class="card-title">Metrics</h6>
                        
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Priority Score</span>
                                <strong class="text-primary">${opportunity.priority_score.toFixed(1)}/10</strong>
                            </div>
                            <div class="progress mt-1">
                                <div class="progress-bar" style="width: ${opportunity.priority_score * 10}%"></div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Estimated ROI</span>
                                <strong class="text-success">${opportunity.estimated_roi.toFixed(1)}x</strong>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Estimated Views</span>
                                <strong class="text-info">${opportunity.estimated_views.toLocaleString()}</strong>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Production Cost</span>
                                <strong class="text-warning">฿${opportunity.production_cost.toFixed(0)}</strong>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Competition</span>
                                <span class="badge bg-secondary">${opportunity.competition_level}</span>
                            </div>
                        </div>
                        
                        <hr>
                        
                        <div class="text-center">
                            <div class="h5 text-success">฿${(opportunity.estimated_views * opportunity.estimated_roi * 0.001).toFixed(0)}</div>
                            <div class="small text-muted">Estimated Revenue</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">Quick Actions</h6>
                        <div class="d-grid gap-2">
                            ${opportunity.status === 'ready' ? `
                                <button class="btn btn-success btn-sm" onclick="createContentFromDetailModal()">
                                    <i class="fas fa-play me-1"></i>Create Content
                                </button>
                            ` : `
                                <button class="btn btn-primary btn-sm" onclick="analyzeOpportunity('${opportunity.id}')">
                                    <i class="fas fa-brain me-1"></i>Analyze More
                                </button>
                            `}
                            <button class="btn btn-outline-secondary btn-sm" onclick="shareOpportunity('${opportunity.id}')">
                                <i class="fas fa-share me-1"></i>Share
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Set up create content button
    document.getElementById('createFromDetail').onclick = () => {
        opportunityDetailModal.hide();
        createContentFromOpportunity(opportunity.id);
    };
}

function createContentFromDetailModal() {
    opportunityDetailModal.hide();
    // Opportunity ID will be passed through the modal data
    const opportunityId = currentOpportunityData?.id;
    if (opportunityId) {
        createContentFromOpportunity(opportunityId);
    }
}

async function shareOpportunity(opportunityId) {
    const url = `${window.location.origin}/opportunities?id=${opportunityId}`;
    
    if (navigator.share) {
        try {
            await navigator.share({
                title: 'Content Opportunity',
                text: 'Check out this content opportunity!',
                url: url
            });
        } catch (error) {
            console.log('Share failed:', error);
            fallbackShare(url);
        }
    } else {
        fallbackShare(url);
    }
}

function fallbackShare(url) {
    navigator.clipboard.writeText(url).then(() => {
        showNotification('URL copied to clipboard', 'success');
    }).catch(() => {
        prompt('Copy this URL:', url);
    });
}

async function editOpportunity(opportunityId) {
    // Implement edit functionality
    showNotification('Edit functionality coming soon', 'info');
}

async function duplicateOpportunity(opportunityId) {
    try {
        const response = await fetch(`/api/opportunities/${opportunityId}/duplicate`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to duplicate opportunity');
        }
        
        showNotification('Opportunity duplicated successfully', 'success');
        setTimeout(() => location.reload(), 1000);
        
    } catch (error) {
        showNotification(`ไม่สามารถ duplicate ได้: ${error.message}`, 'error');
    }
}

async function deleteOpportunity(opportunityId) {
    if (!confirm('คุณแน่ใจว่าต้องการลบโอกาสนี้?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/opportunities/${opportunityId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to delete opportunity');
        }
        
        showNotification('Opportunity deleted successfully', 'success');
        
        // Remove the card from DOM
        const card = document.querySelector(`[data-opp-id="${opportunityId}"]`);
        if (card) {
            card.closest('.col-lg-6').remove();
        }
        
    } catch (error) {
        showNotification(`ไม่สามารถลบได้: ${error.message}`, 'error');
    }
}

// Helper functions
function getPriorityLevel(score) {
    if (score >= 8) return 'high';
    if (score >= 5) return 'medium';
    return 'low';
}

function getStatusColor(status) {
    const colors = {
        pending: 'secondary',
        analyzing: 'primary',
        ready: 'success',
        selected: 'warning',
        completed: 'info'
    };
    return colors[status] || 'secondary';
}

// Override functions from base template for opportunities-specific behavior
function updateOpportunitiesDisplay(opportunities) {
    const grid = document.getElementById('opportunitiesGrid');
    
    opportunities.forEach(opp => {
        const oppElement = createOpportunityCard(opp);
        grid.insertBefore(oppElement, grid.children[0]);
    });
    
    showNotification(`เพิ่ม ${opportunities.length} opportunities ใหม่`, 'success');
}

function createOpportunityCard(opp) {
    const div = document.createElement('div');
    div.className = 'col-lg-6 col-xl-4 mb-4';
    div.innerHTML = `
        <div class="opportunity-card priority-${getPriorityLevel(opp.priority)} animate__animated animate__fadeInUp" 
             data-opp-id="${opp.id || 'new'}">
            <div class="priority-indicator"></div>
            <div class="card-body p-4">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div class="form-check">
                        <input class="form-check-input opportunity-checkbox" type="checkbox" 
                               value="${opp.id || 'new'}" onchange="updateBulkActions()">
                    </div>
                    <div class="text-end">
                        <div class="priority-score">${opp.priority.toFixed(1)}</div>
                        <small class="text-muted">Priority</small>
                    </div>
                </div>
                
                <h5 class="card-title mb-3">${opp.title}</h5>
                
                <div class="row g-2 mb-3">
                    <div class="col-4">
                        <div class="metric-item">
                            <div class="roi-badge small">${opp.roi.toFixed(1)}x</div>
                            <div class="small text-muted mt-1">ROI</div>
                        </div>
                    </div>
                    <div class="col-8">
                        <div class="status-badge status-ready">New</div>
                    </div>
                </div>
                
                <div class="text-muted small mb-3">
                    <i class="fas fa-clock me-1"></i>Just created
                </div>
                
                <div class="d-grid">
                    <button class="btn btn-success" onclick="createContentFromOpportunity('${opp.id || 'new'}')">
                        <i class="fas fa-play me-2"></i>Create Content
                    </button>
                </div>
            </div>
        </div>
    `;
    return div;
}

// WebSocket event handlers
socket.on('analysis_completed', function(data) {
    if (data.opportunities_count > 0) {
        updateOpportunitiesDisplay(data.best_opportunities);
    }
});

socket.on('content_created', function(data) {
    showNotification(`เนื้อหา "${data.title}" ถูกสร้างเสร็จแล้ว`, 'success');
    
    // Update opportunity status in UI
    const oppCard = document.querySelector(`[data-opp-id="${data.opportunity_id}"]`);
    if (oppCard) {
        const statusBadge = oppCard.querySelector('.status-badge');
        if (statusBadge) {
            statusBadge.className = 'status-badge status-completed';
            statusBadge.textContent = 'Content Created';
        }
    }
});