"""Routes — Buddy System"""
from fastapi import APIRouter, Depends
from services.buddy.buddy_service import (
    create_group, join_group, leave_group,
    update_member_location, record_checkin,
    get_group_status, is_checkin_overdue,
)
from services.auth_service import get_current_user
from pydantic import BaseModel

router = APIRouter()


class GroupCreate(BaseModel):
    group_name: str
    city: str = "MUM"


class LocationUpdate(BaseModel):
    group_id:     str
    lat:          float
    lng:          float
    danger_score: float = 0.0


@router.post("/groups")
async def create(payload: GroupCreate, user=Depends(get_current_user)):
    return await create_group(user["user_id"], payload.group_name, payload.city)


@router.post("/groups/{group_id}/join")
async def join(group_id: str, user=Depends(get_current_user)):
    ok = await join_group(group_id, user["user_id"])
    return {"joined": ok, "group_id": group_id}


@router.delete("/groups/{group_id}/leave")
async def leave(group_id: str, user=Depends(get_current_user)):
    await leave_group(group_id, user["user_id"])
    return {"left": True}


@router.post("/groups/location")
async def update_location(payload: LocationUpdate, user=Depends(get_current_user)):
    alerts = await update_member_location(
        payload.group_id, user["user_id"],
        payload.lat, payload.lng, payload.danger_score,
    )
    return {"alerts": alerts, "alert_count": len(alerts)}


@router.post("/checkin")
async def checkin(user=Depends(get_current_user)):
    return await record_checkin(user["user_id"])


@router.get("/checkin/status")
async def checkin_status(user=Depends(get_current_user)):
    overdue = await is_checkin_overdue(user["user_id"])
    return {"overdue": overdue, "user_id": user["user_id"]}


@router.get("/groups/{group_id}/status")
async def group_status(group_id: str, user=Depends(get_current_user)):
    return await get_group_status(group_id)
