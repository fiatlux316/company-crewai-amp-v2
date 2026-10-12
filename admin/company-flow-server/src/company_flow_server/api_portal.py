from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from .distributed.db import SessionLocal, User, Team, PortalService, ServiceTeamAccess
from .auth.rbac import Principal, current_principal, require

router = APIRouter(prefix="/api/v1/portal", tags=["portal"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ServiceUpdateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    order_num: Optional[int] = 0
    is_active: Optional[bool] = True

class ServiceCreateRequest(BaseModel):
    service_code: str
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    order_num: Optional[int] = 0

class ServiceTeamAccessRequest(BaseModel):
    team_ids: List[str]

@router.get("/my-services")
def get_my_services(
    db: Session = Depends(get_db),
    p: Principal = Depends(current_principal)
):
    """
    현재 로그인 사용자의 팀이 접근 가능한 서비스 목록 조회.
    platform_admin 이거나 AUTH_DISABLED 인 경우 활성화된 모든 서비스를 반환.
    """
    all_active_services = db.query(PortalService).filter(PortalService.is_active == True).order_by(PortalService.order_num.asc()).all()
    
    # 관리자는 전체 접근 가능
    if "platform_admin" in p.roles:
        return [
            {
                "id": s.id,
                "service_code": s.service_code,
                "name": s.name,
                "description": s.description,
                "url": s.url,
                "order_num": s.order_num
            }
            for s in all_active_services
        ]
    
    # 일반 사용자는 본인 team_id 에 매핑된 서비스만 조회
    user = db.query(User).filter(User.user_id == p.subject).first()
    if not user or not user.team_id:
        # 팀이 없는 경우 기본적으로 agent-platform 은 접근 허용
        accessible_codes = {"agent-platform"}
    else:
        access_rows = db.query(ServiceTeamAccess).filter(ServiceTeamAccess.team_id == user.team_id).all()
        accessible_service_ids = {a.service_id for a in access_rows}
        accessible_codes = {s.service_code for s in all_active_services if s.id in accessible_service_ids}
        # 최소한 agent-platform은 포함하도록 보장
        accessible_codes.add("agent-platform")

    result = [
        {
            "id": s.id,
            "service_code": s.service_code,
            "name": s.name,
            "description": s.description,
            "url": s.url,
            "order_num": s.order_num
        }
        for s in all_active_services
        if s.service_code in accessible_codes
    ]
    return result

@router.get("/services")
def list_services_for_admin(
    db: Session = Depends(get_db),
    p: Principal = Depends(current_principal)
):
    """
    관리자용 서비스 목록 및 각 서비스별 접근 허용 팀 ID 목록 조회
    """
    if "platform_admin" not in p.roles:
        raise HTTPException(status_code=403, detail="Admin permission required")
        
    services = db.query(PortalService).order_by(PortalService.order_num.asc()).all()
    all_accesses = db.query(ServiceTeamAccess).all()
    
    access_map = {}
    for acc in all_accesses:
        access_map.setdefault(acc.service_id, []).append(acc.team_id)
        
    return [
        {
            "id": s.id,
            "service_code": s.service_code,
            "name": s.name,
            "description": s.description,
            "url": s.url,
            "order_num": s.order_num,
            "is_active": s.is_active,
            "allowed_team_ids": access_map.get(s.id, [])
        }
        for s in services
    ]

@router.post("/services")
def create_service(
    req: ServiceCreateRequest,
    db: Session = Depends(get_db),
    p: Principal = Depends(current_principal)
):
    if "platform_admin" not in p.roles:
        raise HTTPException(status_code=403, detail="Admin permission required")
        
    if db.query(PortalService).filter(PortalService.service_code == req.service_code).first():
        raise HTTPException(status_code=400, detail="Service code already exists")
        
    new_svc = PortalService(
        service_code=req.service_code,
        name=req.name,
        description=req.description,
        url=req.url,
        order_num=req.order_num,
        is_active=True
    )
    db.add(new_svc)
    db.commit()
    db.refresh(new_svc)
    return {"message": "Service created", "service": {"id": new_svc.id, "service_code": new_svc.service_code, "name": new_svc.name, "url": new_svc.url}}

@router.put("/services/{service_id}")
def update_service(
    service_id: str,
    req: ServiceUpdateRequest,
    db: Session = Depends(get_db),
    p: Principal = Depends(current_principal)
):
    if "platform_admin" not in p.roles:
        raise HTTPException(status_code=403, detail="Admin permission required")
        
    svc = db.query(PortalService).filter(PortalService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
        
    svc.name = req.name
    if req.description is not None:
        svc.description = req.description
    if req.url is not None:
        svc.url = req.url
    if req.order_num is not None:
        svc.order_num = req.order_num
    if req.is_active is not None:
        svc.is_active = req.is_active
        
    db.commit()
    return {"message": "Service updated"}

@router.put("/services/{service_id}/teams")
def update_service_team_access(
    service_id: str,
    req: ServiceTeamAccessRequest,
    db: Session = Depends(get_db),
    p: Principal = Depends(current_principal)
):
    """
    특정 서비스에 접근 가능한 팀 목록을 통째로 동기화
    """
    if "platform_admin" not in p.roles:
        raise HTTPException(status_code=403, detail="Admin permission required")
        
    svc = db.query(PortalService).filter(PortalService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
        
    # 기존 접근 권한 삭제
    db.query(ServiceTeamAccess).filter(ServiceTeamAccess.service_id == service_id).delete()
    
    # 신규 권한 등록
    for tid in req.team_ids:
        db.add(ServiceTeamAccess(service_id=service_id, team_id=tid))
        
    db.commit()
    return {"message": "Service team access updated", "service_id": service_id, "team_ids": req.team_ids}
