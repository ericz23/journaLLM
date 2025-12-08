"""
WHOOP API client for fetching user health data.

API Reference:
- Cycle: https://developer.whoop.com/docs/developing/user-data/cycle
- Sleep: https://developer.whoop.com/docs/developing/user-data/sleep
- Recovery: https://developer.whoop.com/docs/developing/user-data/recovery
- Workout: https://developer.whoop.com/docs/developing/user-data/workout
- User: https://developer.whoop.com/docs/developing/user-data/user
"""

from datetime import date, datetime
from typing import Optional, List, Any

import httpx
from pydantic import BaseModel, Field

from backend.core.config import WHOOP_API_BASE_URL


# =============================================================================
# Pydantic Models for WHOOP API Responses
# =============================================================================

class UserProfile(BaseModel):
    """User basic profile information."""
    user_id: int
    email: str
    first_name: str
    last_name: str


class BodyMeasurement(BaseModel):
    """User body measurements."""
    height_meter: float
    weight_kilogram: float
    max_heart_rate: int


class CycleScore(BaseModel):
    """Cycle score data."""
    strain: float
    kilojoule: float
    average_heart_rate: int
    max_heart_rate: int


class Cycle(BaseModel):
    """Physiological cycle data."""
    id: int
    user_id: int
    start: datetime
    end: Optional[datetime] = None
    timezone_offset: str
    score_state: str
    score: Optional[CycleScore] = None


class SleepStageSummary(BaseModel):
    """Sleep stage breakdown in milliseconds."""
    total_in_bed_time_milli: int
    total_awake_time_milli: int
    total_no_data_time_milli: int = 0
    total_light_sleep_time_milli: int
    total_slow_wave_sleep_time_milli: int
    total_rem_sleep_time_milli: int
    sleep_cycle_count: int
    disturbance_count: int


class SleepNeeded(BaseModel):
    """Sleep need breakdown."""
    baseline_milli: int
    need_from_sleep_debt_milli: int
    need_from_recent_strain_milli: int
    need_from_recent_nap_milli: int = 0


class SleepScore(BaseModel):
    """Sleep score data."""
    stage_summary: SleepStageSummary
    sleep_needed: SleepNeeded
    respiratory_rate: float
    sleep_performance_percentage: Optional[float] = None
    sleep_consistency_percentage: Optional[float] = None
    sleep_efficiency_percentage: Optional[float] = None


class Sleep(BaseModel):
    """Sleep activity data."""
    id: str
    user_id: int
    cycle_id: int
    start: datetime
    end: datetime
    timezone_offset: str
    nap: bool
    score_state: str
    score: Optional[SleepScore] = None


class RecoveryScore(BaseModel):
    """Recovery score data."""
    user_calibrating: bool
    recovery_score: float
    resting_heart_rate: float
    hrv_rmssd_milli: float
    spo2_percentage: Optional[float] = None
    skin_temp_celsius: Optional[float] = None


class Recovery(BaseModel):
    """Recovery data."""
    cycle_id: int
    sleep_id: str
    user_id: int
    score_state: str
    score: Optional[RecoveryScore] = None


class WorkoutZoneDurations(BaseModel):
    """Heart rate zone durations."""
    zone_zero_milli: Optional[int] = 0
    zone_one_milli: Optional[int] = 0
    zone_two_milli: Optional[int] = 0
    zone_three_milli: Optional[int] = 0
    zone_four_milli: Optional[int] = 0
    zone_five_milli: Optional[int] = 0


class WorkoutScore(BaseModel):
    """Workout score data."""
    strain: float
    average_heart_rate: int
    max_heart_rate: int
    kilojoule: float
    percent_recorded: Optional[float] = None
    distance_meter: Optional[float] = None
    altitude_gain_meter: Optional[float] = None
    altitude_change_meter: Optional[float] = None
    zone_durations: Optional[WorkoutZoneDurations] = None


class Workout(BaseModel):
    """Workout activity data."""
    id: str
    user_id: int
    start: datetime
    end: datetime
    timezone_offset: str
    sport_name: str
    sport_id: Optional[int] = None
    score_state: str
    score: Optional[WorkoutScore] = None


class PaginatedResponse(BaseModel):
    """Generic paginated response from WHOOP API."""
    records: List[Any]
    next_token: Optional[str] = None


# =============================================================================
# WHOOP API Client
# =============================================================================

class WhoopClient:
    """
    Client for interacting with the WHOOP API.
    
    Usage:
        from backend.api.whoop_oauth import get_access_token
        
        token = get_access_token()
        client = WhoopClient(token)
        profile = await client.get_profile()
    """
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = WHOOP_API_BASE_URL
    
    def _headers(self) -> dict:
        """Build authorization headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
    
    async def _get(self, endpoint: str, params: dict = None, debug: bool = False) -> dict:
        """Make a GET request to the WHOOP API."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers(), params=params)
            if debug:
                print(f"[DEBUG] {endpoint} -> {response.status_code}: {response.text[:500]}")
            # Some endpoints return 404 when no data exists for the query
            if response.status_code == 404:
                return {"records": []}
            response.raise_for_status()
            return response.json()
    
    async def debug_endpoints(self) -> dict:
        """Test various endpoint paths to find the correct ones."""
        endpoints_to_test = [
            "/v1/cycle",
            "/v1/recovery", 
            "/v1/sleep",
            "/v1/workout",
            "/v1/activity/sleep",
            "/v1/activity/workout",
            "/v2/cycle",
            "/v2/recovery",
            "/v2/sleep", 
            "/v2/workout",
            "/v2/activity/sleep",
            "/v2/activity/workout",
        ]
        
        results = {}
        async with httpx.AsyncClient() as client:
            for endpoint in endpoints_to_test:
                url = f"{self.base_url}{endpoint}"
                try:
                    response = await client.get(
                        url, 
                        headers=self._headers(), 
                        params={"limit": 1}
                    )
                    results[endpoint] = {
                        "status": response.status_code,
                        "preview": response.text[:200] if response.status_code == 200 else response.text[:100]
                    }
                except Exception as e:
                    results[endpoint] = {"status": "error", "preview": str(e)}
        
        return results
    
    # -------------------------------------------------------------------------
    # User Endpoints
    # -------------------------------------------------------------------------
    
    async def get_profile(self) -> UserProfile:
        """
        Get user's basic profile information.
        GET /v1/user/profile/basic
        """
        data = await self._get("/v1/user/profile/basic")
        return UserProfile(**data)
    
    async def get_body_measurement(self) -> BodyMeasurement:
        """
        Get user's body measurements.
        GET /v1/user/measurement/body
        """
        data = await self._get("/v1/user/measurement/body")
        return BodyMeasurement(**data)
    
    # -------------------------------------------------------------------------
    # Cycle Endpoints
    # -------------------------------------------------------------------------
    
    async def get_cycles(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 25,
        next_token: Optional[str] = None,
    ) -> tuple[List[Cycle], Optional[str]]:
        """
        Get physiological cycles.
        GET /v1/cycle
        
        Returns:
            Tuple of (list of cycles, next_token for pagination)
        """
        params = {"limit": limit}
        if start_date:
            params["start"] = f"{start_date}T00:00:00.000Z"
        if end_date:
            params["end"] = f"{end_date}T23:59:59.999Z"
        if next_token:
            params["nextToken"] = next_token
        
        data = await self._get("/v1/cycle", params)
        cycles = [Cycle(**record) for record in data.get("records", [])]
        return cycles, data.get("next_token")
    
    # -------------------------------------------------------------------------
    # Sleep Endpoints
    # -------------------------------------------------------------------------
    
    async def get_sleep(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 25,
        next_token: Optional[str] = None,
    ) -> tuple[List[Sleep], Optional[str]]:
        """
        Get sleep activities.
        GET /v2/activity/sleep
        
        Returns:
            Tuple of (list of sleep records, next_token for pagination)
        """
        params = {"limit": limit}
        if start_date:
            params["start"] = f"{start_date}T00:00:00.000Z"
        if end_date:
            params["end"] = f"{end_date}T23:59:59.999Z"
        if next_token:
            params["nextToken"] = next_token
        
        data = await self._get("/v2/activity/sleep", params)
        sleep_records = [Sleep(**record) for record in data.get("records", [])]
        return sleep_records, data.get("next_token")
    
    # -------------------------------------------------------------------------
    # Recovery Endpoints
    # -------------------------------------------------------------------------
    
    async def get_recovery(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 25,
        next_token: Optional[str] = None,
    ) -> tuple[List[Recovery], Optional[str]]:
        """
        Get recovery scores.
        GET /v2/recovery
        
        Returns:
            Tuple of (list of recovery records, next_token for pagination)
        """
        params = {"limit": limit}
        if start_date:
            params["start"] = f"{start_date}T00:00:00.000Z"
        if end_date:
            params["end"] = f"{end_date}T23:59:59.999Z"
        if next_token:
            params["nextToken"] = next_token
        
        data = await self._get("/v2/recovery", params)
        recovery_records = [Recovery(**record) for record in data.get("records", [])]
        return recovery_records, data.get("next_token")
    
    # -------------------------------------------------------------------------
    # Workout Endpoints
    # -------------------------------------------------------------------------
    
    async def get_workouts(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 25,
        next_token: Optional[str] = None,
    ) -> tuple[List[Workout], Optional[str]]:
        """
        Get workout activities.
        GET /v2/activity/workout
        
        Returns:
            Tuple of (list of workouts, next_token for pagination)
        """
        params = {"limit": limit}
        if start_date:
            params["start"] = f"{start_date}T00:00:00.000Z"
        if end_date:
            params["end"] = f"{end_date}T23:59:59.999Z"
        if next_token:
            params["nextToken"] = next_token
        
        data = await self._get("/v2/activity/workout", params)
        workouts = [Workout(**record) for record in data.get("records", [])]
        return workouts, data.get("next_token")
    
    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------
    
    async def get_all_cycles(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Cycle]:
        """Fetch all cycles with automatic pagination."""
        all_cycles = []
        next_token = None
        
        while True:
            cycles, next_token = await self.get_cycles(
                start_date=start_date,
                end_date=end_date,
                next_token=next_token,
            )
            all_cycles.extend(cycles)
            if not next_token:
                break
        
        return all_cycles
    
    async def get_all_sleep(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Sleep]:
        """Fetch all sleep records with automatic pagination."""
        all_sleep = []
        next_token = None
        
        while True:
            sleep_records, next_token = await self.get_sleep(
                start_date=start_date,
                end_date=end_date,
                next_token=next_token,
            )
            all_sleep.extend(sleep_records)
            if not next_token:
                break
        
        return all_sleep
    
    async def get_all_recovery(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Recovery]:
        """Fetch all recovery records with automatic pagination."""
        all_recovery = []
        next_token = None
        
        while True:
            recovery_records, next_token = await self.get_recovery(
                start_date=start_date,
                end_date=end_date,
                next_token=next_token,
            )
            all_recovery.extend(recovery_records)
            if not next_token:
                break
        
        return all_recovery
    
    async def get_all_workouts(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Workout]:
        """Fetch all workouts with automatic pagination."""
        all_workouts = []
        next_token = None
        
        while True:
            workouts, next_token = await self.get_workouts(
                start_date=start_date,
                end_date=end_date,
                next_token=next_token,
            )
            all_workouts.extend(workouts)
            if not next_token:
                break
        
        return all_workouts
