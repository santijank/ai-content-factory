# api/content_api.py
"""
Content Management API - จัดการเนื้อหาและการสร้างเนื้อหา
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path, Body
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import asyncio
import json

from database.repositories.content_repository import ContentRepository
from database.repositories.opportunity_repository import OpportunityRepository
from content_engine.services.ai_director import AIDirector
from content_engine.services.content_pipeline import ContentPipeline
from content_engine.services.service_registry import ServiceManager
from shared.utils.logger import setup_logger
from shared.models.service_status import ServiceStatus

router = APIRouter(prefix="/api/content", tags=["content"])
logger = setup_logger("content_api")


# Dependency injection
async def get_content_repo() -> ContentRepository:
    return ContentRepository()

async def get_opportunity_repo() -> OpportunityRepository:
    return OpportunityRepository()

async def get_service_manager() -> ServiceManager:
    return ServiceManager("config/ai_models.yaml")

async def get_ai_director() -> AIDirector:
    service_manager = await get_service_manager()
    return AIDirector(service_manager)


@router.get("/", response_model=Dict[str, Any])
async def get_content_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    sort: str = Query("created_desc"),
    content_repo: ContentRepository = Depends(get_content_repo)
):
    """ดึงรายการเนื้อหาทั้งหมด"""
    
    try:
        # Build filters
        filters = {}
        if status:
            filters['status'] = status
        
        # Get content items
        items, total = await content_repo.get_paginated(
            skip=skip,
            limit=limit,
            filters=filters,
            sort=sort
        )
        
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_next": skip + limit < total
        }
        
    except Exception as e:
        logger.error(f"Failed to get content items: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve content items")


@router.get("/{content_id}", response_model=Dict[str, Any])
async def get_content_item(
    content_id: str = Path(...),
    content_repo: ContentRepository = Depends(get_content_repo)
):
    """ดึงข้อมูลเนื้อหาแต่ละรายการ"""
    
    try:
        content_item = await content_repo.get_by_id(content_id)
        
        if not content_item:
            raise HTTPException(status_code=404, detail="Content item not found")
        
        # Include related data
        content_dict = content_item.to_dict()
        content_dict['uploads'] = [upload.to_dict() for upload in content_item.uploads]
        content_dict['analytics'] = [analytics.to_dict() for analytics in content_item.analytics]
        
        return content_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get content item {content_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve content item")


@router.post("/create", response_model=Dict[str, Any])
async def create_content(
    background_tasks: BackgroundTasks,
    opportunity_id: str = Body(..., embed=True),
    quality_tier: str = Body("balanced", embed=True),
    custom_config: Optional[Dict[str, Any]] = Body(None, embed=True),
    content_repo: ContentRepository = Depends(get_content_repo),
    opportunity_repo: OpportunityRepository = Depends(get_opportunity_repo),
    ai_director: AIDirector = Depends(get_ai_director)
):
    """สร้างเนื้อหาจาก opportunity"""
    
    try:
        # Validate opportunity exists
        opportunity = await opportunity_repo.get_by_id(opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        if opportunity.status != 'selected':
            raise HTTPException(status_code=400, detail="Opportunity must be selected first")
        
        # Create content item record
        content_item = await content_repo.create({
            'opportunity_id': opportunity_id,
            'status': 'creating',
            'quality_tier': quality_tier,
            'custom_config': custom_config or {}
        })
        
        # Start background content creation
        background_tasks.add_task(
            _create_content_background,
            content_item.id,
            opportunity,
            quality_tier,
            custom_config or {},
            ai_director,
            content_repo
        )
        
        logger.info(f"Started content creation for opportunity {opportunity_id}")
        
        return {
            "content_id": str(content_item.id),
            "status": "creating",
            "message": "Content creation started",
            "estimated_time_minutes": 5
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create content: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start content creation")


async def _create_content_background(
    content_id: str,
    opportunity: Any,
    quality_tier: str,
    custom_config: Dict[str, Any],
    ai_director: AIDirector,
    content_repo: ContentRepository
):
    """Background task สำหรับสร้างเนื้อหา"""
    
    try:
        logger.info(f"Starting background content creation for {content_id}")
        
        # Update status
        await content_repo.update(content_id, {'status': 'generating'})
        
        # Create content plan
        content_plan = await ai_director.create_content_plan(
            opportunity.to_dict(),
            quality_tier=quality_tier,
            custom_config=custom_config
        )
        
        # Update with content plan
        await content_repo.update(content_id, {
            'content_plan': content_plan,
            'status': 'generating_assets'
        })
        
        # Generate content assets
        pipeline = ContentPipeline(quality_tier=quality_tier)
        assets = await pipeline.generate_content_assets(content_plan)
        
        # Store final result
        await content_repo.update(content_id, {
            'assets': assets,
            'status': 'completed',
            'completed_at': datetime.now(timezone.utc)
        })
        
        logger.info(f"Content creation completed for {content_id}")
        
    except Exception as e:
        logger.error(f"Background content creation failed for {content_id}: {str(e)}")
        
        # Update status to failed
        await content_repo.update(content_id, {
            'status': 'failed',
            'error_message': str(e),
            'completed_at': datetime.now(timezone.utc)
        })


@router.get("/{content_id}/plan", response_model=Dict[str, Any])
async def get_content_plan(
    content_id: str = Path(...),
    content_repo: ContentRepository = Depends(get_content_repo)
):
    """ดึงแผนการสร้างเนื้อหา"""
    
    try:
        content_item = await content_repo.get_by_id(content_id)
        
        if not content_item:
            raise HTTPException(status_code=404, detail="Content item not found")
        
        if not content_item.content_plan:
            raise HTTPException(status_code=404, detail="Content plan not available yet")
        
        return {
            "content_id": content_id,
            "plan": content_item.content_plan,
            "status": content_item.status,
            "created_at": content_item.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get content plan {content_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve content plan")


@router.post("/{content_id}/regenerate", response_model=Dict[str, Any])
async def regenerate_content(
    background_tasks: BackgroundTasks,
    content_id: str = Path(...),
    component: str = Body(..., embed=True),  # script, images, audio, all
    config: Optional[Dict[str, Any]] = Body(None, embed=True),
    content_repo: ContentRepository = Depends(get_content_repo),
    ai_director: AIDirector = Depends(get_ai_director)
):
    """สร้างส่วนประกอบของเนื้อหาใหม่"""
    
    try:
        content_item = await content_repo.get_by_id(content_id)
        
        if not content_item:
            raise HTTPException(status_code=404, detail="Content item not found")
        
        if content_item.status not in ['completed', 'failed']:
            raise HTTPException(status_code=400, detail="Content is still being created")
        
        # Start background regeneration
        background_tasks.add_task(
            _regenerate_content_background,
            content_id,
            component,
            config or {},
            ai_director,
            content_repo
        )
        
        # Update status
        await content_repo.update(content_id, {'status': 'regenerating'})
        
        return {
            "content_id": content_id,
            "status": "regenerating",
            "component": component,
            "message": f"Regenerating {component}..."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate content {content_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start regeneration")


async def _regenerate_content_background(
    content_id: str,
    component: str,
    config: Dict[str, Any],
    ai_director: AIDirector,
    content_repo: ContentRepository
):
    """Background task สำหรับสร้างเนื้อหาใหม่"""
    
    try:
        content_item = await content_repo.get_by_id(content_id)
        
        if component == 'all':
            # Regenerate everything
            pipeline = ContentPipeline(quality_tier=content_item.quality_tier)
            new_assets = await pipeline.generate_content_assets(content_item.content_plan)
            
            await content_repo.update(content_id, {
                'assets': new_assets,
                'status': 'completed'
            })
            
        else:
            # Regenerate specific component
            current_assets = content_item.assets or {}
            
            if component == 'script':
                new_script = await ai_director.generate_script(content_item.content_plan, config)
                current_assets['script'] = new_script
                
            elif component == 'images':
                new_images = await ai_director.generate_images(content_item.content_plan, config)
                current_assets['images'] = new_images
                
            elif component == 'audio':
                new_audio = await ai_director.generate_audio(content_item.content_plan, config)
                current_assets['audio'] = new_audio
            
            await content_repo.update(content_id, {
                'assets': current_assets,
                'status': 'completed'
            })
        
        logger.info(f"Content regeneration completed for {content_id}, component: {component}")
        
    except Exception as e:
        logger.error(f"Background content regeneration failed for {content_id}: {str(e)}")
        
        await content_repo.update(content_id, {
            'status': 'failed',
            'error_message': str(e)
        })


@router.delete("/{content_id}", response_model=Dict[str, Any])
async def delete_content(
    content_id: str = Path(...),
    content_repo: ContentRepository = Depends(get_content_repo)
):
    """ลบเนื้อหา"""
    
    try:
        content_item = await content_repo.get_by_id(content_id)
        
        if not content_item:
            raise HTTPException(status_code=404, detail="Content item not found")
        
        # Check if content is uploaded
        if content_item.uploads and any(upload.status == 'completed' for upload in content_item.uploads):
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete content that has been uploaded. Please remove uploads first."
            )
        
        await content_repo.delete(content_id)
        
        return {
            "message": "Content deleted successfully",
            "content_id": content_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete content {content_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete content")


@router.get("/{content_id}/download/{asset_type}")
async def download_content_asset(
    content_id: str = Path(...),
    asset_type: str = Path(...),  # script, image, audio, video
    content_repo: ContentRepository = Depends(get_content_repo)
):
    """ดาวน์โหลด asset ของเนื้อหา"""
    
    try:
        content_item = await content_repo.get_by_id(content_id)
        
        if not content_item:
            raise HTTPException(status_code=404, detail="Content item not found")
        
        if not content_item.assets or asset_type not in content_item.assets:
            raise HTTPException(status_code=404, detail=f"Asset {asset_type} not found")
        
        asset_data = content_item.assets[asset_type]
        
        # Return appropriate response based on asset type
        if asset_type == 'script':
            return {
                "content_id": content_id,
                "asset_type": asset_type,
                "data": asset_data
            }
        else:
            # For binary assets, return streaming response
            # Implementation depends on how assets are stored
            raise HTTPException(status_code=501, detail="Binary asset download not implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download asset {asset_type} for {content_id}: {str(e)}")