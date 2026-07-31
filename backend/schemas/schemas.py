from pydantic import BaseModel, EmailStr, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import List, Optional
from datetime import datetime

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

# --- AUTH SCHEMAS ---
class LoginRequest(CamelModel):
    username: str
    password: str
    role: Optional[str] = "Employee"

class TokenResponse(CamelModel):
    access_token: str
    token_type: str
    user: dict

class ChangePasswordRequest(CamelModel):
    current_password: str
    new_password: str

# --- EMPLOYEE SCHEMAS ---
class EmployeeBase(CamelModel):
    id: str
    name: str
    department: str
    designation: str
    email: str
    username: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = "Active"
    role: Optional[str] = "Employee"
    avatar: Optional[str] = None
    joining_date: Optional[str] = None
    location: Optional[str] = "Hyderabad, India"

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
import re

class EmployeeCreate(EmployeeBase):
    password: Optional[str] = None

    @field_validator('id')
    @classmethod
    def validate_employee_id(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r'^[A-Z0-9_-]{3,20}$', v):
            raise ValueError('Employee ID must be between 3 and 20 alphanumeric characters (e.g. QEMP001, EMP101, 121234)')
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v:
            clean_v = re.sub(r'\D', '', v)
            if len(clean_v) != 10:
                raise ValueError('Phone number must be exactly 10 digits')
            return clean_v
        return v

    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Please enter a valid email address (e.g. employee@quadrantitservices.com)')
        return v

class EmployeeUpdate(CamelModel):
    name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None
    avatar: Optional[str] = None
    joining_date: Optional[str] = None
    location: Optional[str] = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v:
            clean_v = re.sub(r'\D', '', v)
            if len(clean_v) != 10:
                raise ValueError('Phone number must be exactly 10 digits')
            return clean_v
        return v

class EmployeeOut(EmployeeBase):
    created_at: Optional[datetime] = None

# --- CATEGORY SCHEMAS ---
class CategoryBase(CamelModel):
    id: str
    name: str
    description: Optional[str] = None
    icon_name: Optional[str] = None
    group: str  # IT, Non-IT
    scope: str  # Employee, Organization
    owner_entity: str

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon_name: Optional[str] = None
    group: Optional[str] = None
    scope: Optional[str] = None
    owner_entity: Optional[str] = None

class CategoryOut(CategoryBase):
    created_at: Optional[datetime] = None

# --- ASSET SCHEMAS ---
class AssetBase(CamelModel):
    id: str
    type: str
    brand: str
    model: str
    serial_number: str
    status: Optional[str] = "Available"
    ownership: Optional[str] = "Quadrant IT Services"
    group: Optional[str] = "IT"
    charger_serial_number: Optional[str] = "N/A"
    condition: Optional[str] = "Good"
    assigned_to: Optional[str] = None
    purchase_date: Optional[str] = None
    warranty_end_date: Optional[str] = None
    assigned_date: Optional[str] = "N/A"
    assigned_at: Optional[datetime] = None
    image: Optional[str] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(CamelModel):
    type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    status: Optional[str] = None
    ownership: Optional[str] = None
    group: Optional[str] = None
    charger_serial_number: Optional[str] = None
    condition: Optional[str] = None
    assigned_to: Optional[str] = None
    purchase_date: Optional[str] = None
    warranty_end_date: Optional[str] = None
    assigned_date: Optional[str] = None
    assigned_at: Optional[datetime] = None
    image: Optional[str] = None

class AssetOut(AssetBase):
    created_at: Optional[datetime] = None

class AssetAssignRequest(CamelModel):
    employee_id: str
    asset_ids: List[str]
    assign_date: Optional[str] = None
    remarks: Optional[str] = None

class AssetReturnRequest(CamelModel):
    employee_id: str
    asset_ids: List[str]
    return_date: Optional[str] = None
    condition: Optional[str] = "Good"
    remarks: Optional[str] = None

# --- LICENSE SCHEMAS ---
class LicenseBase(CamelModel):
    name: str
    status: Optional[str] = "Available"
    vendor: Optional[str] = "Subscription"
    license_key: Optional[str] = "N/A"
    seats: Optional[int] = 1
    cost: Optional[str] = "N/A"
    start_date: Optional[str] = None
    end_date: str
    alert_days_before: Optional[int] = 30
    admin_email: str
    description: Optional[str] = None

class LicenseCreate(LicenseBase):
    id: Optional[str] = None

class LicenseUpdate(CamelModel):
    name: Optional[str] = None
    status: Optional[str] = None
    vendor: Optional[str] = None
    license_key: Optional[str] = None
    seats: Optional[int] = None
    cost: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    alert_days_before: Optional[int] = None
    admin_email: Optional[str] = None
    description: Optional[str] = None

class LicenseOut(LicenseBase):
    id: str
    created_at: Optional[datetime] = None

# --- REPAIR SCHEMAS ---
class RepairUpdateSchema(CamelModel):
    status: str
    message: str

class RepairCreate(CamelModel):
    asset_id: Optional[str] = None
    reported_by: str
    issue: str
    description: Optional[str] = ""
    priority: Optional[str] = "Medium"
    assigned_to: Optional[str] = "IT Support Team"
    estimated_completion: Optional[str] = "Awaiting inspection"

class RepairUpdateOut(CamelModel):
    id: int
    repair_id: str
    date: str
    message: str
    created_at: Optional[datetime] = None

class RepairOut(CamelModel):
    id: str
    asset_id: Optional[str] = None
    reported_by: Optional[str] = None
    issue: str
    description: Optional[str] = None
    request_date: str
    priority: str
    assigned_to: Optional[str] = None
    estimated_completion: Optional[str] = None
    status: str
    accepted_by: Optional[str] = None
    accepted_date: Optional[str] = None
    updates: List[RepairUpdateOut] = []
    created_at: Optional[datetime] = None

# --- ANNOUNCEMENT SCHEMAS ---
class AnnouncementBase(CamelModel):
    title: str
    message: str
    type: Optional[str] = "General"
    priority: Optional[str] = "Medium"

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementOut(AnnouncementBase):
    id: str
    date: str
    author: str
    created_at: Optional[datetime] = None

# --- GUIDELINE SCHEMAS ---
class GuidelineBase(CamelModel):
    title: str
    version: str
    summary: Optional[str] = None
    content: Optional[str] = None
    file_name: Optional[str] = None
    size: Optional[str] = None
    download_url: Optional[str] = None

class GuidelineUpdate(CamelModel):
    title: Optional[str] = None
    version: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    file_name: Optional[str] = None
    size: Optional[str] = None
    download_url: Optional[str] = None

class GuidelineOut(GuidelineBase):
    id: str
    uploaded_date: str
    created_at: Optional[datetime] = None

# --- NOTIFICATION SCHEMAS ---
class NotificationBase(CamelModel):
    title: str
    message: str
    type: str  # info, success, warning, danger, alert
    employee_id: Optional[str] = None

class NotificationOut(NotificationBase):
    id: str
    time: str
    read: bool
    created_at: Optional[datetime] = None

# --- ACTIVITY LOG SCHEMAS ---
class ActivityLogOut(CamelModel):
    id: str
    user: str
    activity: str
    details: str
    ip_address: str
    date_time: str
    created_at: Optional[datetime] = None

class ActivityLogCreate(CamelModel):
    activity: str
    details: str
