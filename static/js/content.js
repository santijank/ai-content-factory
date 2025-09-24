/**
 * Content Page JavaScript
 * ตำแหน่งไฟล์: static/js/content.js
 * 
 * จัดการ interactions และ real-time updates สำหรับหน้า Content Management
 */

let uploadProgressModal;
let contentDetailModal;
let contentPreviewModal;
let selectedContent = new Set();
let currentContentData = null;
let uploadPollingInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeModals();
    initializeEventListeners();
    startPerformancePolling();
    updateBulkActions();
});

function initializeModals() {
    uploadProgressModal = new bootstrap.Modal(document.getElementById('uploadProgressModal'));
    contentDetailModal = new bootstrap.Modal(document.getElementById('contentDetailModal'));
    contentPreviewModal = new bootstrap.Modal(document.getElementById('contentPreviewModal'));
}

function initializeEventListeners() {
    // Refresh content grid every 30 seconds
    setInterval(refreshContentGrid, 30000);
    
    // Listen for upload completion
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            refreshContentGrid();
        }
    });
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
    const checkboxes = document.querySelectorAll('.content-checkbox:checked');
    const bulkActions = document.getElementById('bulkActions');
    const selectedCount = document.getElementById('selectedCount');
    
    selectedContent.clear();
    checkboxes.forEach(cb => selectedContent.add(cb.value));
    
    selectedCount.textContent = selectedContent.size;
    
    if (selectedContent.size > 0) {
        bulkActions.classList.add('show');
    } else {
        bulkActions.classList.remove('show');
    }
}

function clearSelection() {
    document.querySelectorAll('.content-checkbox').forEach(cb => {
        cb.checked = false;
    });
    updateBulkActions();
}

async function uploadContent(contentId, platforms = null) {
    try {
        // Get content data first
        const contentResponse = await fetch(`/api/content/${contentId}`);
        const content = await contentResponse.json();
        
        if (!contentResponse.ok) {
            throw new Error(content.error || 'Failed to load content');
        }
        
        // Use target platforms if not specified
        if (!platforms) {
            platforms = content.target_platforms || ['youtube'];
        }
        
        // Show upload progress modal
        showUploadProgress([{
            content_id: contentId,
            title: content.title,
            platforms: platforms,
            status: 'starting'
        }]);
        
        // Start upload
        const uploadResponse = await fetch('/api/upload-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content_id: contentId,
                platforms: platforms
            })
        });
        
        const uploadData = await uploadResponse.json();
        
        if (!uploadResponse.ok) {
            throw new Error(uploadData.error || 'Failed to start upload');
        }
        
        // Update progress modal
        updateUploadProgress(contentId, 'uploading', 'การอัปโหลดเริ่มต้นแล้ว...');
        
        // Start polling for progress
        startUploadPolling([contentId]);
        
    } catch (error) {
        hideLoading();
        showNotification(`ไม่สามารถลบได้: ${error.message}`, 'error');
    }
}

async function bulkDelete() {
    if (selectedContent.size === 0) {
        showNotification('กรุณาเลือกเนื้อหาที่ต้องการลบ', 'warning');
        return;
    }
    
    if (!confirm(`คุณแน่ใจว่าต้องการลบ ${selectedContent.size} เนื้อหา?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/content/bulk-delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content_ids: Array.from(selectedContent)
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to delete content');
        }
        
        showNotification(`ลบเนื้อหาสำเร็จ ${data.deleted_count} รายการ`, 'success');
        
        // Remove cards from DOM
        selectedContent.forEach(contentId => {
            const card = document.querySelector(`[data-content-id="${contentId}"]`);
            if (card) {
                card.closest('.col-lg-6').remove();
            }
        });
        
        clearSelection();
        
    } catch (error) {
        showNotification(`ไม่สามารถลบได้: ${error.message}`, 'error');
    }
}

async function createContentQuick() {
    // Redirect to opportunities page
    window.location.href = '/opportunities';
}

function startPerformancePolling() {
    // Poll for updated performance metrics every 2 minutes
    setInterval(async () => {
        try {
            const response = await fetch('/api/content/performance-update');
            const data = await response.json();
            
            if (response.ok && data.updates) {
                data.updates.forEach(update => {
                    updateContentPerformance(update.content_id, update.metrics);
                });
            }
        } catch (error) {
            console.log('Performance polling failed:', error);
        }
    }, 120000); // Every 2 minutes
}

function updateContentPerformance(contentId, metrics) {
    const card = document.querySelector(`[data-content-id="${contentId}"]`);
    if (!card) return;
    
    const metricsGrid = card.querySelector('.metrics-grid');
    if (metricsGrid && metrics) {
        const viewsElement = metricsGrid.querySelector('.metric-item:first-child .fw-bold');
        const likesElement = metricsGrid.querySelector('.metric-item:last-child .fw-bold');
        
        if (viewsElement && metrics.total_views !== undefined) {
            animateNumber(viewsElement, parseInt(viewsElement.textContent.replace(/,/g, '')) || 0, metrics.total_views);
        }
        
        if (likesElement && metrics.total_likes !== undefined) {
            animateNumber(likesElement, parseInt(likesElement.textContent.replace(/,/g, '')) || 0, metrics.total_likes);
        }
    }
}

async function refreshContentGrid() {
    try {
        const response = await fetch('/api/content/grid-update');
        const data = await response.json();
        
        if (response.ok && data.updates) {
            data.updates.forEach(update => {
                updateContentCard(update);
            });
        }
    } catch (error) {
        console.log('Grid refresh failed:', error);
    }
}

function updateContentCard(contentData) {
    const card = document.querySelector(`[data-content-id="${contentData.id}"]`);
    if (!card) return;
    
    // Update status
    if (contentData.production_status) {
        card.className = card.className.replace(/status-\w+/, `status-${contentData.production_status}`);
        
        const progressBar = card.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.className = `progress-bar progress-${contentData.production_status}`;
        }
        
        const statusBadge = card.querySelector('.badge');
        if (statusBadge) {
            statusBadge.textContent = contentData.production_status.charAt(0).toUpperCase() + contentData.production_status.slice(1);
            statusBadge.className = `badge bg-${getStatusColor(contentData.production_status)}`;
        }
    }
    
    // Update upload info if available
    if (contentData.uploads && contentData.uploads.length > 0) {
        const uploadSection = card.querySelector('.mt-3:last-child');
        if (uploadSection) {
            const uploadsHtml = contentData.uploads.map(upload => `
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="platform-badge platform-${upload.platform} small">
                        ${upload.platform.toUpperCase()}
                    </span>
                    ${upload.url ? `
                        <a href="${upload.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-external-link-alt"></i>
                        </a>
                    ` : `
                        <span class="badge bg-warning">Processing</span>
                    `}
                </div>
            `).join('');
            
            uploadSection.innerHTML = `
                <h6 class="small text-muted mb-2">Published on:</h6>
                ${uploadsHtml}
            `;
        }
    }
}

// Helper functions
function getStatusColor(status) {
    const colors = {
        pending: 'secondary',
        generating: 'primary',
        completed: 'success',
        failed: 'danger',
        uploaded: 'info'
    };
    return colors[status] || 'secondary';
}

function animateNumber(element, start, end, duration = 1000) {
    const startTime = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(start + (end - start) * progress);
        
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

// Override functions from base template for content-specific behavior
function updateContentDisplay(newContent) {
    const grid = document.getElementById('contentGrid');
    
    newContent.forEach(content => {
        const contentElement = createContentCard(content);
        grid.insertBefore(contentElement, grid.children[0]);
    });
    
    showNotification(`เพิ่ม ${newContent.length} เนื้อหาใหม่`, 'success');
}

function createContentCard(content) {
    const div = document.createElement('div');
    div.className = 'col-lg-6 col-xl-4 mb-4';
    div.innerHTML = `
        <div class="content-card status-${content.status} animate__animated animate__fadeInUp" 
             data-content-id="${content.id || 'new'}">
            <div class="status-indicator"></div>
            <div class="card-body p-4">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div class="form-check">
                        <input class="form-check-input content-checkbox" type="checkbox" 
                               value="${content.id || 'new'}" onchange="updateBulkActions()">
                    </div>
                    <div class="quality-badge quality-${content.quality || 'balanced'}">
                        ${(content.quality || 'balanced').charAt(0).toUpperCase() + (content.quality || 'balanced').slice(1)}
                    </div>
                </div>
                
                <div class="content-thumbnail">
                    <i class="fas fa-video"></i>
                    <div class="overlay">
                        <button class="btn btn-light btn-sm" onclick="previewContent('${content.id || 'new'}')">
                            <i class="fas fa-play me-1"></i>Preview
                        </button>
                    </div>
                </div>
                
                <h5 class="card-title mb-2">${content.title}</h5>
                
                <div class="platform-badges">
                    ${(content.platforms || ['youtube']).map(platform => 
                        `<span class="platform-badge platform-${platform}">${platform.toUpperCase()}</span>`
                    ).join('')}
                </div>
                
                <div class="progress-container">
                    <div class="progress-bar progress-${content.status || 'pending'}"></div>
                </div>
                
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <span class="badge bg-${getStatusColor(content.status || 'pending')}">
                        ${(content.status || 'pending').charAt(0).toUpperCase() + (content.status || 'pending').slice(1)}
                    </span>
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i>Just created
                    </small>
                </div>
                
                <div class="d-grid">
                    <button class="btn btn-outline-primary" onclick="viewContentDetail('${content.id || 'new'}')">
                        <i class="fas fa-eye me-2"></i>View Details
                    </button>
                </div>
            </div>
        </div>
    `;
    return div;
}

// WebSocket event handlers for real-time updates
socket.on('content_created', function(data) {
    showNotification(`เนื้อหา "${data.title}" ถูกสร้างเสร็จแล้ว`, 'success');
    
    // Update content card if it exists
    const card = document.querySelector(`[data-content-id="${data.content_id}"]`);
    if (card) {
        updateContentCard({
            id: data.content_id,
            production_status: 'completed',
            completed_at: data.timestamp
        });
    } else {
        // Add new content card
        setTimeout(() => refreshContentGrid(), 1000);
    }
});

socket.on('content_uploaded', function(data) {
    showNotification(`เนื้อหาอัปโหลดสำเร็จไป ${data.platforms.join(', ')}`, 'success');
    
    // Update upload progress if modal is open
    if (uploadProgressModal._isShown) {
        updateUploadProgress(data.content_id, 'completed', 'อัปโหลดสำเร็จ!', 100);
    }
    
    // Update content card
    updateContentCard({
        id: data.content_id,
        production_status: 'uploaded',
        uploads: data.results
    });
});

socket.on('upload_progress', function(data) {
    // Real-time upload progress updates
    if (uploadProgressModal._isShown) {
        updateUploadProgress(
            data.content_id, 
            data.status, 
            data.message, 
            data.progress
        );
    }
});

socket.on('content_generation_progress', function(data) {
    // Real-time content generation progress
    const card = document.querySelector(`[data-content-id="${data.content_id}"]`);
    if (card) {
        const progressBar = card.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${data.progress}%`;
        }
        
        // Update status message if available
        if (data.message) {
            const statusBadge = card.querySelector('.badge');
            if (statusBadge) {
                statusBadge.textContent = data.message;
            }
        }
    }
});

socket.on('performance_update', function(data) {
    // Real-time performance metrics updates
    if (data.content_id && data.metrics) {
        updateContentPerformance(data.content_id, data.metrics);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (uploadPollingInterval) {
        clearInterval(uploadPollingInterval);
    }
});

// Auto-refresh every 5 minutes
setInterval(() => {
    if (!document.hidden) {
        refreshContentGrid();
    }
}, 5 * 60 * 1000);

// Initialize drag and drop for file uploads (future feature)
function initializeDragDrop() {
    const dropZone = document.getElementById('contentGrid');
    
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('drag-over');
    });
    
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            showNotification('File upload feature coming soon!', 'info');
        }
    });
}

// Initialize features
document.addEventListener('DOMContentLoaded', function() {
    initializeDragDrop();
});
อัปโหลดได้: ${error.message}`, 'error');
        console.error('Upload error:', error);
    }
}

async function bulkUpload() {
    if (selectedContent.size === 0) {
        showNotification('กรุณาเลือกเนื้อหาที่ต้องการอัปโหลด', 'warning');
        return;
    }
    
    if (!confirm(`คุณต้องการอัปโหลด ${selectedContent.size} เนื้อหา?`)) {
        return;
    }
    
    try {
        // Prepare upload items
        const uploadItems = [];
        for (const contentId of selectedContent) {
            const contentResponse = await fetch(`/api/content/${contentId}`);
            const content = await contentResponse.json();
            
            if (contentResponse.ok && content.production_status === 'completed') {
                uploadItems.push({
                    content_id: contentId,
                    title: content.title,
                    platforms: content.target_platforms || ['youtube'],
                    status: 'pending'
                });
            }
        }
        
        if (uploadItems.length === 0) {
            showNotification('ไม่มีเนื้อหาที่พร้อมอัปโหลด', 'warning');
            return;
        }
        
        // Show progress modal
        showUploadProgress(uploadItems);
        
        // Start uploads
        for (const item of uploadItems) {
            try {
                updateUploadProgress(item.content_id, 'starting', 'เริ่มการอัปโหลด...');
                
                const uploadResponse = await fetch('/api/upload-content', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        content_id: item.content_id,
                        platforms: item.platforms
                    })
                });
                
                const uploadData = await uploadResponse.json();
                
                if (uploadResponse.ok) {
                    updateUploadProgress(item.content_id, 'uploading', 'กำลังอัปโหลด...');
                } else {
                    updateUploadProgress(item.content_id, 'error', uploadData.error || 'เกิดข้อผิดพลาด');
                }
                
                // Small delay between uploads
                await new Promise(resolve => setTimeout(resolve, 1000));
                
            } catch (error) {
                updateUploadProgress(item.content_id, 'error', error.message);
            }
        }
        
        // Start polling for all uploads
        startUploadPolling(uploadItems.map(item => item.content_id));
        clearSelection();
        
    } catch (error) {
        showNotification(`เกิดข้อผิดพลาดในการอัปโหลด: ${error.message}`, 'error');
    }
}

function showUploadProgress(uploadItems) {
    const content = document.getElementById('uploadProgressContent');
    content.innerHTML = '';
    
    uploadItems.forEach(item => {
        const itemHtml = `
            <div class="upload-item pending" id="upload-${item.content_id}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-1">${item.title}</h6>
                    <span class="badge bg-secondary" id="status-${item.content_id}">Pending</span>
                </div>
                <div class="small text-muted mb-2">
                    Platforms: ${item.platforms.join(', ')}
                </div>
                <div class="progress mb-2">
                    <div class="progress-bar" id="progress-${item.content_id}" role="progressbar" style="width: 0%"></div>
                </div>
                <div class="small text-muted" id="message-${item.content_id}">กำลังเตรียม...</div>
            </div>
        `;
        content.insertAdjacentHTML('beforeend', itemHtml);
    });
    
    uploadProgressModal.show();
}

function updateUploadProgress(contentId, status, message, progress = null) {
    const uploadItem = document.getElementById(`upload-${contentId}`);
    const statusBadge = document.getElementById(`status-${contentId}`);
    const progressBar = document.getElementById(`progress-${contentId}`);
    const messageDiv = document.getElementById(`message-${contentId}`);
    
    if (!uploadItem) return;
    
    // Update status
    statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    messageDiv.textContent = message;
    
    // Update progress bar
    if (progress !== null) {
        progressBar.style.width = `${progress}%`;
    } else {
        // Default progress based on status
        const progressMap = {
            'pending': 0,
            'starting': 10,
            'uploading': 50,
            'processing': 75,
            'completed': 100,
            'error': 100
        };
        progressBar.style.width = `${progressMap[status] || 0}%`;
    }
    
    // Update item class
    uploadItem.className = `upload-item ${status}`;
    
    // Update status badge color
    const badgeColors = {
        'pending': 'bg-secondary',
        'starting': 'bg-primary',
        'uploading': 'bg-info',
        'processing': 'bg-warning',
        'completed': 'bg-success',
        'error': 'bg-danger'
    };
    statusBadge.className = `badge ${badgeColors[status] || 'bg-secondary'}`;
}

function startUploadPolling(contentIds) {
    if (uploadPollingInterval) {
        clearInterval(uploadPollingInterval);
    }
    
    uploadPollingInterval = setInterval(async () => {
        let allCompleted = true;
        
        for (const contentId of contentIds) {
            try {
                const response = await fetch(`/api/content/${contentId}/upload-status`);
                const data = await response.json();
                
                if (response.ok) {
                    const status = data.upload_status || 'pending';
                    const message = data.message || 'กำลังประมวลผล...';
                    const progress = data.progress;
                    
                    updateUploadProgress(contentId, status, message, progress);
                    
                    if (status !== 'completed' && status !== 'error') {
                        allCompleted = false;
                    }
                } else {
                    updateUploadProgress(contentId, 'error', 'ไม่สามารถตรวจสอบสถานะได้');
                }
            } catch (error) {
                updateUploadProgress(contentId, 'error', 'เกิดข้อผิดพลาดในการตรวจสอบ');
            }
        }
        
        // Stop polling if all uploads completed
        if (allCompleted) {
            clearInterval(uploadPollingInterval);
            uploadPollingInterval = null;
            
            // Refresh content grid
            setTimeout(() => {
                refreshContentGrid();
            }, 2000);
        }
    }, 3000); // Poll every 3 seconds
}

async function retryGeneration(contentId) {
    if (!confirm('คุณต้องการสร้างเนื้อหานี้ใหม่?')) {
        return;
    }
    
    try {
        showLoading('สร้างเนื้อหาใหม่', 'กำลังเริ่มการสร้างเนื้อหาใหม่...');
        
        const response = await fetch(`/api/content/${contentId}/retry`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to retry generation');
        }
        
        hideLoading();
        showNotification('เริ่มการสร้างเนื้อหาใหม่แล้ว', 'success');
        
        // Update card status
        const card = document.querySelector(`[data-content-id="${contentId}"]`);
        if (card) {
            card.className = card.className.replace(/status-\w+/, 'status-generating');
            const progressBar = card.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.className = 'progress-bar progress-generating';
            }
        }
        
    } catch (error) {
        hideLoading();
        showNotification(`ไม่สามารถสร้างใหม่ได้: ${error.message}`, 'error');
    }
}

async function viewContentDetail(contentId) {
    try {
        const response = await fetch(`/api/content/${contentId}`);
        const content = await response.json();
        
        if (!response.ok) {
            throw new Error(content.error || 'Failed to load content');
        }
        
        currentContentData = content;
        displayContentDetail(content);
        contentDetailModal.show();
        
    } catch (error) {
        showNotification(`ไม่สามารถโหลดรายละเอียดได้: ${error.message}`, 'error');
    }
}

function displayContentDetail(content) {
    const contentElement = document.getElementById('contentDetailContent');
    
    const contentPlan = content.content_plan || {};
    const assets = content.assets || {};
    const costBreakdown = content.cost_breakdown || {};
    
    contentElement.innerHTML = `
        <div class="row">
            <div class="col-md-8">
                <div class="card mb-4">
                    <div class="card-body">
                        <h5 class="card-title">${content.title}</h5>
                        <p class="text-muted">${content.description || 'ไม่มีคำอธิบาย'}</p>
                        
                        ${contentPlan.script ? `
                        <h6 class="mt-4">Script</h6>
                        <div class="bg-light p-3 rounded">
                            <div class="mb-2">
                                <strong>Hook:</strong><br>
                                ${contentPlan.script.hook || 'ไม่มีข้อมูล'}
                            </div>
                            <div class="mb-2">
                                <strong>Main Content:</strong><br>
                                ${contentPlan.script.main_content || 'ไม่มีข้อมูล'}
                            </div>
                            <div>
                                <strong>Call to Action:</strong><br>
                                ${contentPlan.script.cta || 'ไม่มีข้อมูล'}
                            </div>
                        </div>
                        ` : ''}
                        
                        ${contentPlan.visual_plan ? `
                        <h6 class="mt-4">Visual Plan</h6>
                        <div class="bg-light p-3 rounded">
                            <div class="mb-2">
                                <strong>Style:</strong> ${contentPlan.visual_plan.style || 'ไม่ระบุ'}
                            </div>
                            <div class="mb-2">
                                <strong>Scenes:</strong><br>
                                ${contentPlan.visual_plan.scenes ? 
                                    contentPlan.visual_plan.scenes.map((scene, i) => `${i + 1}. ${scene}`).join('<br>') :
                                    'ไม่มีข้อมูล'
                                }
                            </div>
                        </div>
                        ` : ''}
                        
                        ${Object.keys(assets).length > 0 ? `
                        <h6 class="mt-4">Generated Assets</h6>
                        <div class="row">
                            ${assets.thumbnail ? `
                            <div class="col-md-6 mb-3">
                                <div class="card">
                                    <img src="${assets.thumbnail}" class="card-img-top" alt="Thumbnail">
                                    <div class="card-body">
                                        <h6 class="card-title">Thumbnail</h6>
                                    </div>
                                </div>
                            </div>
                            ` : ''}
                            
                            ${assets.video_file ? `
                            <div class="col-md-6 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h6 class="card-title">Video File</h6>
                                        <a href="${assets.video_file}" class="btn btn-sm btn-primary" download>
                                            <i class="fas fa-download me-1"></i>Download
                                        </a>
                                    </div>
                                </div>
                            </div>
                            ` : ''}
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                ${content.uploads && content.uploads.length > 0 ? `
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">Upload History</h6>
                        ${content.uploads.map(upload => `
                            <div class="d-flex justify-content-between align-items-center mb-2 p-2 bg-light rounded">
                                <div>
                                    <strong>${upload.platform.toUpperCase()}</strong>
                                    <br>
                                    <small class="text-muted">
                                        ${upload.uploaded_at ? new Date(upload.uploaded_at).toLocaleString('th-TH') : 'Processing...'}
                                    </small>
                                </div>
                                <div>
                                    ${upload.url ? `
                                        <a href="${upload.url}" target="_blank" class="btn btn-sm btn-primary">
                                            <i class="fas fa-external-link-alt me-1"></i>View
                                        </a>
                                    ` : `
                                        <span class="badge bg-warning">Processing</span>
                                    `}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
            
            <div class="col-md-4">
                <div class="card mb-3">
                    <div class="card-body">
                        <h6 class="card-title">Content Info</h6>
                        
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Status:</span>
                                <span class="badge bg-${getStatusColor(content.production_status)}">${content.production_status}</span>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Quality:</span>
                                <span class="badge bg-info">${content.quality_tier}</span>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Platforms:</span>
                                <div>
                                    ${content.target_platforms.map(p => 
                                        `<span class="badge bg-secondary me-1">${p}</span>`
                                    ).join('')}
                                </div>
                            </div>
                        </div>
                        
                        ${content.completed_at ? `
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Completed:</span>
                                <span class="small">${new Date(content.completed_at).toLocaleString('th-TH')}</span>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                ${Object.keys(costBreakdown).length > 0 ? `
                <div class="card mb-3">
                    <div class="card-body">
                        <h6 class="card-title">Cost Breakdown</h6>
                        
                        ${costBreakdown.text_generation ? `
                        <div class="d-flex justify-content-between mb-2">
                            <span>Text Generation:</span>
                            <span>฿${costBreakdown.text_generation}</span>
                        </div>
                        ` : ''}
                        
                        ${costBreakdown.image_generation ? `
                        <div class="d-flex justify-content-between mb-2">
                            <span>Image Generation:</span>
                            <span>฿${costBreakdown.image_generation}</span>
                        </div>
                        ` : ''}
                        
                        ${costBreakdown.audio_generation ? `
                        <div class="d-flex justify-content-between mb-2">
                            <span>Audio Generation:</span>
                            <span>฿${costBreakdown.audio_generation}</span>
                        </div>
                        ` : ''}
                        
                        <hr>
                        <div class="d-flex justify-content-between">
                            <strong>Total:</strong>
                            <strong>฿${costBreakdown.total || 0}</strong>
                        </div>
                    </div>
                </div>
                ` : ''}
                
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">Quick Actions</h6>
                        <div class="d-grid gap-2">
                            ${content.production_status === 'completed' && !content.uploads?.length ? `
                                <button class="btn btn-success btn-sm" onclick="uploadContentFromDetail()">
                                    <i class="fas fa-cloud-upload me-1"></i>Upload Now
                                </button>
                            ` : ''}
                            
                            ${content.assets?.video_file ? `
                                <button class="btn btn-primary btn-sm" onclick="previewContent('${content.id}')">
                                    <i class="fas fa-play me-1"></i>Preview
                                </button>
                                <button class="btn btn-outline-secondary btn-sm" onclick="downloadContent('${content.id}')">
                                    <i class="fas fa-download me-1"></i>Download
                                </button>
                            ` : ''}
                            
                            <button class="btn btn-outline-secondary btn-sm" onclick="shareContent('${content.id}')">
                                <i class="fas fa-share me-1"></i>Share
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Setup action button
    const actionButton = document.getElementById('actionFromDetail');
    if (content.production_status === 'completed' && !content.uploads?.length) {
        actionButton.innerHTML = '<i class="fas fa-cloud-upload me-1"></i>Upload';
        actionButton.onclick = () => {
            contentDetailModal.hide();
            uploadContent(content.id);
        };
    } else if (content.assets?.video_file) {
        actionButton.innerHTML = '<i class="fas fa-download me-1"></i>Download';
        actionButton.onclick = () => downloadContent(content.id);
    } else {
        actionButton.style.display = 'none';
    }
}

function uploadContentFromDetail() {
    contentDetailModal.hide();
    if (currentContentData) {
        uploadContent(currentContentData.id);
    }
}

async function previewContent(contentId) {
    try {
        const response = await fetch(`/api/content/${contentId}`);
        const content = await response.json();
        
        if (!response.ok) {
            throw new Error(content.error || 'Failed to load content');
        }
        
        const previewBody = document.getElementById('contentPreviewBody');
        
        if (content.assets && content.assets.video_file) {
            previewBody.innerHTML = `
                <video controls class="w-100" style="max-height: 500px;">
                    <source src="${content.assets.video_file}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
                <h6 class="mt-3">${content.title}</h6>
                <p class="text-muted">${content.description || ''}</p>
            `;
        } else if (content.assets && content.assets.thumbnail) {
            previewBody.innerHTML = `
                <img src="${content.assets.thumbnail}" class="img-fluid mb-3" alt="Content thumbnail">
                <h6>${content.title}</h6>
                <p class="text-muted">${content.description || ''}</p>
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    วิดีโอยังไม่พร้อม - แสดงเฉพาะ thumbnail
                </div>
            `;
        } else {
            previewBody.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-video fa-3x text-muted mb-3"></i>
                    <h6>${content.title}</h6>
                    <p class="text-muted">ไม่มีไฟล์ preview</p>
                </div>
            `;
        }
        
        contentPreviewModal.show();
        
    } catch (error) {
        showNotification(`ไม่สามารถโหลด preview ได้: ${error.message}`, 'error');
    }
}

async function downloadContent(contentId) {
    try {
        const response = await fetch(`/api/content/${contentId}/download`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to download');
        }
        
        // Create download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `content-${contentId}.mp4`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showNotification('เริ่มการดาวน์โหลดแล้ว', 'success');
        
    } catch (error) {
        showNotification(`ไม่สามารถดาวน์โหลดได้: ${error.message}`, 'error');
    }
}

async function bulkDownload() {
    if (selectedContent.size === 0) {
        showNotification('กรุณาเลือกเนื้อหาที่ต้องการดาวน์โหลด', 'warning');
        return;
    }
    
    showLoading('เตรียมการดาวน์โหลด', 'กำลังเตรียมไฟล์...');
    
    try {
        const response = await fetch('/api/content/bulk-download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content_ids: Array.from(selectedContent)
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to prepare download');
        }
        
        // Download zip file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `content-batch-${Date.now()}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        hideLoading();
        showNotification('เริ่มการดาวน์โหลดแล้ว', 'success');
        clearSelection();
        
    } catch (error) {
        hideLoading();
        showNotification(`ไม่สามารถดาวน์โหลดได้: ${error.message}`, 'error');
    }
}

async function shareContent(contentId) {
    const url = `${window.location.origin}/content?id=${contentId}`;
    
    if (navigator.share) {
        try {
            await navigator.share({
                title: 'AI Generated Content',
                text: 'Check out this AI-generated content!',
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

async function editContent(contentId) {
    // Implement edit functionality
    showNotification('Edit functionality coming soon', 'info');
}

async function duplicateContent(contentId) {
    try {
        const response = await fetch(`/api/content/${contentId}/duplicate`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to duplicate content');
        }
        
        showNotification('Content duplicated successfully', 'success');
        setTimeout(() => location.reload(), 1000);
        
    } catch (error) {
        showNotification(`ไม่สามารถ duplicate ได้: ${error.message}`, 'error');
    }
}

async function deleteContent(contentId) {
    if (!confirm('คุณแน่ใจว่าต้องการลบเนื้อหานี้?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/content/${contentId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to delete content');
        }
        
        showNotification('Content deleted successfully', 'success');
        
        // Remove card from DOM
        const card = document.querySelector(`[data-content-id="${contentId}"]`);
        if (card) {
            card.closest('.col-lg-6').remove();
        }
        
    } catch (error) {
        showNotification(`ไม่สามารถ