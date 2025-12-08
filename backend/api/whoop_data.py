"""
REST API endpoints for fetching WHOOP health data.
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.api.whoop_oauth import get_access_token
from backend.services.whoop_client import (
    WhoopClient,
    UserProfile,
    BodyMeasurement,
    Cycle,
    Sleep,
    Recovery,
    Workout,
)

router = APIRouter(prefix="/api/whoop/data", tags=["whoop-data"])


def _get_client() -> WhoopClient:
    """Get an authenticated WHOOP client."""
    token = get_access_token()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated with WHOOP. Please login at /api/whoop/login"
        )
    return WhoopClient(token)


# =============================================================================
# Response Models
# =============================================================================

class ProfileResponse(BaseModel):
    profile: UserProfile
    body: Optional[BodyMeasurement] = None


class HealthSummary(BaseModel):
    """Combined health summary for a date range."""
    start_date: date
    end_date: date
    cycles: List[Cycle]
    sleep: List[Sleep]
    recovery: List[Recovery]
    workouts: List[Workout]


# =============================================================================
# User Endpoints
# =============================================================================

@router.get("/debug")
async def debug_endpoints():
    """
    Debug endpoint to test which WHOOP API paths work.
    """
    client = _get_client()
    return await client.debug_endpoints()


@router.get("/profile", response_model=ProfileResponse)
async def get_profile():
    """
    Get user profile and body measurements.
    
    Note: Body measurements require the 'read:body_measurement' scope.
    If not authorized, only profile data will be returned.
    """
    client = _get_client()
    
    try:
        profile = await client.get_profile()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Body measurement is optional (requires separate scope)
    body = None
    try:
        body = await client.get_body_measurement()
    except Exception:
        pass  # Scope not granted or other error - continue without body data
    
    return ProfileResponse(profile=profile, body=body)


# =============================================================================
# Cycle Endpoints
# =============================================================================

@router.get("/cycles", response_model=List[Cycle])
async def get_cycles(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(25, ge=1, le=100, description="Max records to return"),
):
    """
    Get physiological cycles for a date range.
    
    Cycles represent the body's biological rhythm (wake-sleep-wake).
    Each cycle includes strain, kilojoules, and heart rate data.
    """
    client = _get_client()
    
    try:
        cycles, _ = await client.get_cycles(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return cycles


# =============================================================================
# Sleep Endpoints
# =============================================================================

@router.get("/sleep", response_model=List[Sleep])
async def get_sleep(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(25, ge=1, le=100, description="Max records to return"),
):
    """
    Get sleep records for a date range.
    
    Includes sleep stages (light, deep, REM), efficiency, and performance.
    """
    client = _get_client()
    
    try:
        sleep_records, _ = await client.get_sleep(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return sleep_records


# =============================================================================
# Recovery Endpoints
# =============================================================================

@router.get("/recovery", response_model=List[Recovery])
async def get_recovery(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(25, ge=1, le=100, description="Max records to return"),
):
    """
    Get recovery scores for a date range.
    
    Recovery is a daily measure (0-100%) of how prepared your body is to perform.
    Includes HRV, resting heart rate, SpO2, and skin temperature.
    """
    client = _get_client()
    
    try:
        recovery_records, _ = await client.get_recovery(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return recovery_records


# =============================================================================
# Workout Endpoints
# =============================================================================

@router.get("/workouts", response_model=List[Workout])
async def get_workouts(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(25, ge=1, le=100, description="Max records to return"),
):
    """
    Get workout activities for a date range.
    
    Includes sport type, strain score, heart rate, and distance.
    """
    client = _get_client()
    
    try:
        workouts, _ = await client.get_workouts(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return workouts


# =============================================================================
# Combined Summary Endpoint
# =============================================================================

@router.get("/summary", response_model=HealthSummary)
async def get_health_summary(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
):
    """
    Get a combined health summary including cycles, sleep, recovery, and workouts.
    
    This fetches all data types for the given date range in a single request.
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date"
        )
    
    client = _get_client()
    
    try:
        cycles = await client.get_all_cycles(start_date=start_date, end_date=end_date)
        sleep = await client.get_all_sleep(start_date=start_date, end_date=end_date)
        recovery = await client.get_all_recovery(start_date=start_date, end_date=end_date)
        workouts = await client.get_all_workouts(start_date=start_date, end_date=end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return HealthSummary(
        start_date=start_date,
        end_date=end_date,
        cycles=cycles,
        sleep=sleep,
        recovery=recovery,
        workouts=workouts,
    )
