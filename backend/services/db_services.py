from typing import Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta, timezone
import json
from models import Employee, Asset, Category, License, Repair, RepairUpdate, Announcement, Guideline, Notification, ActivityLog
from services.auth_service import get_password_hash

# --- UTILITIES: ACTIVITY LOGS & NOTIFICATIONS ---

IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now() -> datetime:
    return datetime.now(IST)

def format_relative_time(created_at: Optional[datetime], static_time: Optional[str] = None) -> str:
    if not created_at:
        return static_time or "Just now"
    
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
        
    diff = now - created_at
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        mins = int(seconds // 60)
        return f"{mins} min ago" if mins == 1 else f"{mins} mins ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour ago" if hours == 1 else f"{hours} hours ago"
    elif seconds < 2592000:
        days = int(seconds // 86400)
        return f"{days} day ago" if days == 1 else f"{days} days ago"
    else:
        months = int(seconds // 2592000)
        return f"{months} month ago" if months == 1 else f"{months} months ago"


def log_activity(db: Session, user: str, activity: str, details: str, ip_address: str = "192.168.1.10"):
    now_str = get_ist_now().strftime("%d %b %Y, %I:%M %p")
    # Generate unique ID safely
    count = db.execute(text("SELECT COUNT(*) FROM activity_log")).scalar() or 0
    n = count + 1
    while True:
        act_id = f"ACT{str(n).zfill(3)}"
        exists = db.execute(text("SELECT id FROM activity_log WHERE id = :id"), {"id": act_id}).first()
        if not exists:
            break
        n += 1
    
    query = text("""
        INSERT INTO activity_log (id, "user", activity, details, ip_address, date_time)
        VALUES (:id, :user, :activity, :details, :ip_address, :date_time)
    """)
    db.execute(query, {
        "id": act_id,
        "user": user,
        "activity": activity,
        "details": details,
        "ip_address": ip_address,
        "date_time": now_str
    })
    db.commit()

def create_notification(db: Session, title: str, message: str, notif_type: str, employee_id: Optional[str] = None):
    try:
        count = db.execute(text("SELECT COUNT(*) FROM notifications")).scalar() or 0
        n = count + 1
        while True:
            notif_id = f"NT{str(n).zfill(3)}"
            exists = db.execute(text("SELECT id FROM notifications WHERE id = :id"), {"id": notif_id}).first()
            if not exists:
                break
            n += 1
        
        query = text("""
            INSERT INTO notifications (id, title, message, time, read, type, employee_id)
            VALUES (:id, :title, :message, :time, :read, :type, :employee_id)
        """)
        db.execute(query, {
            "id": notif_id,
            "title": title,
            "message": message,
            "time": "Just now",
            "read": False,
            "type": notif_type,
            "employee_id": employee_id
        })
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Notification Service Warning] Failed to create notification: {e}")



# --- EMPLOYEE SERVICES ---

def get_employees(db: Session, search: Optional[str] = None, department: Optional[str] = None, status: Optional[str] = None):
    sql = "SELECT * FROM employees WHERE 1=1"
    params = {}
    if search:
        sql += " AND (id ILIKE :search OR name ILIKE :search OR email ILIKE :search OR department ILIKE :search)"
        params["search"] = f"%{search}%"
    if department and department != "All":
        sql += " AND department = :department"
        params["department"] = department
    if status and status != "All":
        sql += " AND status = :status"
        params["status"] = status
    sql += " ORDER BY id"
    return db.execute(text(sql), params).all()

def get_employee_by_id(db: Session, emp_id: str):
    sql = "SELECT * FROM employees WHERE id = :id"
    return db.execute(text(sql), {"id": emp_id}).first()

def get_employee_by_username_or_email(db: Session, login_name: str):
    sql = "SELECT * FROM employees WHERE email = :login OR username = :login OR name = :login OR id = :login"
    return db.execute(text(sql), {"login": login_name}).first()

def create_employee(db: Session, emp_data: dict, operator_name: str):
    emp_id = emp_data["id"].strip().upper()
    role = emp_data.get("role") or "Employee"
    default_pwd = "admin123" if str(role).strip().lower() == "admin" else "employee123"
    hashed = get_password_hash(emp_data.get("password") or default_pwd)
    
    query = text("""
        INSERT INTO employees (id, name, department, designation, email, username, phone, status, role, avatar, joining_date, location, password_hash)
        VALUES (:id, :name, :department, :designation, :email, :username, :phone, :status, :role, :avatar, :joining_date, :location, :password_hash)
    """)
    db.execute(query, {
        "id": emp_id,
        "name": emp_data["name"],
        "department": emp_data["department"],
        "designation": emp_data["designation"],
        "email": emp_data["email"],
        "username": emp_data.get("username") or emp_data["email"].split('@')[0],
        "phone": emp_data.get("phone"),
        "status": emp_data.get("status") or "Active",
        "role": role,
        "avatar": emp_data.get("avatar") or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop&crop=faces",
        "joining_date": emp_data.get("joining_date") or datetime.now().strftime("%d %b %Y"),
        "location": emp_data.get("location") or "Hyderabad, India",
        "password_hash": hashed
    })
    db.commit()
    log_activity(db, operator_name, "Add Employee", f"Added new employee {emp_data['name']} ({emp_id})")
    return get_employee_by_id(db, emp_id)

def update_employee(db: Session, emp_id: str, emp_data: dict, operator_name: str):
    sql = "UPDATE employees SET "
    updates = []
    params = {"id": emp_id}
    
    for key, value in emp_data.items():
        if key in ["name", "department", "designation", "email", "username", "phone", "status", "role", "avatar", "joining_date", "location"]:
            updates.append(f"{key} = :{key}")
            params[key] = value
            
    if emp_data.get("role") and str(emp_data["role"]).strip().lower() == "admin":
        updates.append("password_hash = :password_hash")
        params["password_hash"] = get_password_hash("admin123")
        
    sql += ", ".join(updates) + " WHERE id = :id"
    db.execute(text(sql), params)
    db.commit()
    
    log_activity(db, operator_name, "Update Employee", f"Updated employee profile for {emp_data.get('name') or emp_id}")
    return get_employee_by_id(db, emp_id)

def delete_employee(db: Session, emp_id: str, operator_name: str):
    employee = get_employee_by_id(db, emp_id)
    if not employee:
        return False
    try:
        # Unassign assets assigned to this employee and reset status
        db.execute(
            text("UPDATE assets SET assigned_to = NULL, status = 'Available', assigned_date = 'N/A' WHERE assigned_to = :id"),
            {"id": emp_id}
        )
        # Clear reported_by reference in repairs
        db.execute(
            text("UPDATE repairs SET reported_by = NULL WHERE reported_by = :id"),
            {"id": emp_id}
        )
        # Delete employee notifications
        db.execute(
            text("DELETE FROM notifications WHERE employee_id = :id"),
            {"id": emp_id}
        )
        # Delete employee record
        db.execute(text("DELETE FROM employees WHERE id = :id"), {"id": emp_id})
        db.commit()
        log_activity(db, operator_name, "Delete Employee", f"Deleted employee {emp_id}")
        return True
    except Exception as e:
        db.rollback()
        raise e

def change_employee_password(db: Session, emp_id: str, new_password: str):
    hashed = get_password_hash(new_password)
    db.execute(text("UPDATE employees SET password_hash = :hash WHERE id = :id"), {"hash": hashed, "id": emp_id})
    db.commit()


# --- CATEGORY SERVICES ---

def get_categories(db: Session):
    return db.execute(text("SELECT * FROM categories ORDER BY id")).all()

def create_category(db: Session, cat_data: dict, operator_name: str):
    query = text("""
        INSERT INTO categories (id, name, description, icon_name, "group", scope, owner_entity)
        VALUES (:id, :name, :description, :icon_name, :group, :scope, :owner_entity)
    """)
    db.execute(query, {
        "id": cat_data["id"],
        "name": cat_data["name"],
        "description": cat_data.get("description"),
        "icon_name": cat_data.get("icon_name"),
        "group": cat_data["group"],
        "scope": cat_data["scope"],
        "owner_entity": cat_data["owner_entity"]
    })
    db.commit()
    log_activity(db, operator_name, "Add Category", f"Added new asset category {cat_data['name']}")
    return db.execute(text("SELECT * FROM categories WHERE id = :id"), {"id": cat_data["id"]}).first()

def update_category(db: Session, cat_id: str, cat_data: dict, operator_name: str):
    sql = "UPDATE categories SET "
    updates = []
    params = {"id": cat_id}
    for key, val in cat_data.items():
        if key in ["name", "description", "icon_name", "group", "scope", "owner_entity"]:
            updates.append(f'"{key}" = :{key}' if key == 'group' else f"{key} = :{key}")
            params[key] = val
    sql += ", ".join(updates) + " WHERE id = :id"
    db.execute(text(sql), params)
    db.commit()
    log_activity(db, operator_name, "Update Category", f"Updated category {cat_data.get('name') or cat_id}")
    return db.execute(text("SELECT * FROM categories WHERE id = :id"), {"id": cat_id}).first()

def delete_category(db: Session, cat_id: str, operator_name: str):
    category = db.execute(text("SELECT * FROM categories WHERE id = :id"), {"id": cat_id}).first()
    if category:
        db.execute(text("DELETE FROM categories WHERE id = :id"), {"id": cat_id})
        db.commit()
        log_activity(db, operator_name, "Delete Category", f"Deleted asset category {category.name}")
        return True
    return False


# --- ASSET SERVICES ---

def get_assets(db: Session, search: Optional[str] = None, type_filter: Optional[str] = None, scope_filter: Optional[str] = None):
    sql = "SELECT * FROM assets WHERE type != 'Desktop'"
    params = {}
    if search:
        sql += " AND (id ILIKE :search OR brand ILIKE :search OR model ILIKE :search OR serial_number ILIKE :search)"
        params["search"] = f"%{search}%"
    if type_filter and type_filter != "All":
        sql += " AND type = :type"
        params["type"] = type_filter
    if scope_filter and scope_filter != "All":
        if scope_filter == "Assigned":
            sql += " AND status = 'Assigned'"
        else:
            sql += " AND status != 'Assigned'"
            
    sql += " ORDER BY id"
    return db.execute(text(sql), params).all()

def get_asset_by_id(db: Session, asset_id: str):
    return db.execute(text("SELECT * FROM assets WHERE id = :id"), {"id": asset_id}).first()

def create_asset(db: Session, asset_data: dict, operator_name: str):
    query = text("""
        INSERT INTO assets (id, type, brand, model, serial_number, status, ownership, "group", charger_serial_number, condition, assigned_to, purchase_date, warranty_end_date, assigned_date, assigned_at, image)
        VALUES (:id, :type, :brand, :model, :serial_number, :status, :ownership, :group, :charger_serial_number, :condition, :assigned_to, :purchase_date, :warranty_end_date, :assigned_date, :assigned_at, :image)
    """)
    db.execute(query, {
        "id": asset_data["id"],
        "type": asset_data["type"],
        "brand": asset_data["brand"],
        "model": asset_data["model"],
        "serial_number": asset_data["serial_number"],
        "status": asset_data.get("status") or "Available",
        "ownership": asset_data.get("ownership") or "Quadrant IT Services",
        "group": asset_data.get("group") or "IT",
        "charger_serial_number": asset_data.get("charger_serial_number") or "N/A",
        "condition": asset_data.get("condition") or "Good",
        "assigned_to": asset_data.get("assigned_to"),
        "purchase_date": asset_data.get("purchase_date") or datetime.now().strftime("%d %b %Y"),
        "warranty_end_date": asset_data.get("warranty_end_date") or (datetime.now() + timedelta(days=3*365)).strftime("%d %b %Y"),
        "assigned_date": asset_data.get("assigned_date") or "N/A",
        "assigned_at": asset_data.get("assigned_at"),
        "image": asset_data.get("image") or "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=80&h=80&fit=crop"
    })
    db.commit()
    log_activity(db, operator_name, "Add Asset", f"Added new asset {asset_data['brand']} {asset_data['model']} ({asset_data['id']})")
    return get_asset_by_id(db, asset_data["id"])

def update_asset(db: Session, asset_id: str, asset_data: dict, operator_name: str):
    sql = "UPDATE assets SET "
    updates = []
    params = {"id": asset_id}
    for key, val in asset_data.items():
        if key in ["type", "brand", "model", "serial_number", "status", "ownership", "group", "charger_serial_number", "condition", "assigned_to", "purchase_date", "warranty_end_date", "assigned_date", "assigned_at", "image"]:
            updates.append(f'"{key}" = :{key}' if key == 'group' else f"{key} = :{key}")
            params[key] = val
    sql += ", ".join(updates) + " WHERE id = :id"
    db.execute(text(sql), params)
    db.commit()
    log_activity(db, operator_name, "Update Asset", f"Updated asset details for {asset_id}")
    return get_asset_by_id(db, asset_id)

def delete_asset(db: Session, asset_id: str, operator_name: str):
    asset = get_asset_by_id(db, asset_id)
    if asset:
        db.execute(text("DELETE FROM assets WHERE id = :id"), {"id": asset_id})
        db.commit()
        log_activity(db, operator_name, "Delete Asset", f"Deleted asset {asset_id}")
        return True
    return False

def assign_assets_service(db: Session, emp_id: str, asset_ids: list, assign_date: Optional[str] = None, remarks: Optional[str] = None, operator_name: str = "System"):
    employee = get_employee_by_id(db, emp_id)
    if not employee:
        return False
        
    now_iso = datetime.utcnow()
    date_formatted = datetime.strptime(assign_date, "%Y-%m-%d").strftime("%d %b %Y") if assign_date else datetime.now().strftime("%d %b %Y")
    
    for aid in asset_ids:
        db.execute(text("""
            UPDATE assets 
            SET status = 'Assigned', assigned_to = :emp_id, assigned_date = :assign_date, assigned_at = :assigned_at 
            WHERE id = :id
        """), {
            "emp_id": emp_id,
            "assign_date": date_formatted,
            "assigned_at": now_iso,
            "id": aid
        })
        log_activity(db, operator_name, "Assign Asset", f"Assigned asset {aid} to {employee.name} ({emp_id})")
        
    db.commit()
    create_notification(db, "Assets Assigned", f"{len(asset_ids)} assets successfully assigned to {employee.name}.", "info")
    return True

def return_assets_service(db: Session, emp_id: str, asset_ids: list, return_date: Optional[str] = None, return_condition: Optional[str] = None, remarks: Optional[str] = None, operator_name: str = "System"):
    employee = get_employee_by_id(db, emp_id)
    if not employee:
        return False
        
    next_status = "Under Repair" if return_condition in ["Under Repair", "Damaged"] else "Available"
    
    for aid in asset_ids:
        db.execute(text("""
            UPDATE assets 
            SET status = :status, assigned_to = NULL, assigned_date = 'N/A', assigned_at = NULL 
            WHERE id = :id
        """), {
            "status": next_status,
            "id": aid
        })
        log_activity(db, operator_name, "Return Asset", f"Returned asset {aid} from {employee.name} (Condition: {return_condition})")
        
        if next_status == "Under Repair":
            # Generate repair ticket
            count = db.execute(text("SELECT COUNT(*) FROM repairs")).scalar() or 0
            rep_id = f"REP{str(count + 1).zfill(5)}"
            req_date = datetime.now().strftime("%d %b %Y %I:%M %p")
            
            db.execute(text("""
                INSERT INTO repairs (id, asset_id, reported_by, issue, description, request_date, priority, assigned_to, estimated_completion, status)
                VALUES (:id, :asset_id, :reported_by, :issue, :description, :request_date, :priority, :assigned_to, :est_completion, :status)
            """), {
                "id": rep_id,
                "asset_id": aid,
                "reported_by": emp_id,
                "issue": f"Returned in {return_condition} condition. {remarks or ''}",
                "description": f"Asset returned in {return_condition} condition by employee. Remarks: {remarks or 'None'}",
                "request_date": req_date,
                "priority": "Medium",
                "assigned_to": "IT Support Team",
                "est_completion": "Awaiting inspection",
                "status": "In Progress"
            })
            
            # Insert first update
            db.execute(text("""
                INSERT INTO repair_updates (repair_id, date, message)
                VALUES (:rep_id, :date, :message)
            """), {
                "rep_id": rep_id,
                "date": req_date,
                "message": f"Repair request generated on return by {employee.name}."
            })
            
            log_activity(db, operator_name, "Create Repair", f"Generated repair request {rep_id} for returned asset {aid}")

    db.commit()
    create_notification(db, "Assets Returned", f"{len(asset_ids)} assets successfully returned by {employee.name}.", "success")
    return True


# --- LICENSE SERVICES ---

def get_licenses(db: Session):
    return db.execute(text("SELECT * FROM licenses ORDER BY id")).all()

def get_license_by_id(db: Session, lic_id: str):
    return db.execute(text("SELECT * FROM licenses WHERE id = :id"), {"id": lic_id}).first()

def create_license(db: Session, lic_data: dict, operator_name: str):
    count = db.execute(text("SELECT COUNT(*) FROM licenses")).scalar() or 0
    lic_id = lic_data.get("id") or f"LIC{str(count + 1).zfill(3)}"
    
    query = text("""
        INSERT INTO licenses (id, name, status, vendor, license_key, seats, cost, start_date, end_date, alert_days_before, admin_email, description)
        VALUES (:id, :name, :status, :vendor, :license_key, :seats, :cost, :start_date, :end_date, :alert_days_before, :admin_email, :description)
    """)
    db.execute(query, {
        "id": lic_id,
        "name": lic_data["name"],
        "status": lic_data.get("status") or "Available",
        "vendor": lic_data.get("vendor") or "Subscription",
        "license_key": lic_data.get("license_key") or "N/A",
        "seats": lic_data.get("seats") or 1,
        "cost": lic_data.get("cost") or "N/A",
        "start_date": lic_data.get("start_date") or datetime.now().strftime("%d %b %Y"),
        "end_date": lic_data["end_date"],
        "alert_days_before": lic_data.get("alert_days_before") or 30,
        "admin_email": lic_data["admin_email"],
        "description": lic_data.get("description")
    })
    db.commit()
    log_activity(db, operator_name, "Add License", f"Added new software license: {lic_data['name']}")
    return get_license_by_id(db, lic_id)

def update_license(db: Session, lic_id: str, lic_data: dict, operator_name: str):
    sql = "UPDATE licenses SET "
    updates = []
    params = {"id": lic_id}
    for key, val in lic_data.items():
        if key in ["name", "status", "vendor", "license_key", "seats", "cost", "start_date", "end_date", "alert_days_before", "admin_email", "description"]:
            updates.append(f"{key} = :{key}")
            params[key] = val
    sql += ", ".join(updates) + " WHERE id = :id"
    db.execute(text(sql), params)
    db.commit()
    log_activity(db, operator_name, "Update License", f"Updated software license: {lic_data.get('name') or lic_id}")
    return get_license_by_id(db, lic_id)

def delete_license(db: Session, lic_id: str, operator_name: str):
    license = get_license_by_id(db, lic_id)
    if license:
        db.execute(text("DELETE FROM licenses WHERE id = :id"), {"id": lic_id})
        db.commit()
        log_activity(db, operator_name, "Delete License", f"Deleted software license: {license.name}")
        return True
    return False


# --- REPAIR / TICKET SERVICES ---

def get_repairs(db: Session, reported_by: Optional[str] = None):
    sql = "SELECT * FROM repairs"
    params = {}
    if reported_by:
        sql += " WHERE reported_by = :reported_by"
        params["reported_by"] = reported_by
    sql += " ORDER BY id DESC"
    return db.execute(text(sql), params).all()

def get_repair_by_id(db: Session, rep_id: str):
    return db.execute(text("SELECT * FROM repairs WHERE id = :id"), {"id": rep_id}).first()

def get_repair_updates(db: Session, rep_id: str):
    return db.execute(text("SELECT * FROM repair_updates WHERE repair_id = :rep_id ORDER BY id"), {"rep_id": rep_id}).all()

def create_repair(db: Session, rep_data: dict, operator_name: str):
    count = db.execute(text("SELECT COUNT(*) FROM repairs")).scalar() or 0
    n = count + 1
    while True:
        rep_id = f"TKT{str(n).zfill(4)}"
        exists = db.execute(text("SELECT id FROM repairs WHERE id = :id"), {"id": rep_id}).first()
        if not exists:
            break
        n += 1
    req_date = get_ist_now().strftime("%d %b %Y, %I:%M %p")
    
    # Safely validate asset_id against assets table
    raw_asset_id = rep_data.get("asset_id")
    valid_asset_id = None
    if raw_asset_id:
        asset_exists = db.execute(text("SELECT id FROM assets WHERE id = :id"), {"id": raw_asset_id}).first()
        if asset_exists:
            valid_asset_id = raw_asset_id
    
    db.execute(text("""
        INSERT INTO repairs (id, asset_id, reported_by, issue, description, request_date, priority, assigned_to, estimated_completion, status)
        VALUES (:id, :asset_id, :reported_by, :issue, :description, :request_date, :priority, :assigned_to, :est_completion, :status)
    """), {
        "id": rep_id,
        "asset_id": valid_asset_id,
        "reported_by": rep_data["reported_by"],
        "issue": rep_data["issue"],
        "description": rep_data.get("description") or f"Reported fault: {rep_data['issue']}",
        "request_date": req_date,
        "priority": rep_data.get("priority") or "Medium",
        "assigned_to": rep_data.get("assigned_to") or "IT Support Team",
        "est_completion": rep_data.get("estimated_completion") or "Awaiting inspection",
        "status": "In Progress"
    })
    
    # Insert first update
    db.execute(text("""
        INSERT INTO repair_updates (repair_id, date, message)
        VALUES (:rep_id, :date, :message)
    """), {
        "rep_id": rep_id,
        "date": req_date,
        "message": "Repair request created."
    })
    
    # Update asset status to Under Repair only if valid asset exists and not a new asset request
    if valid_asset_id and not str(rep_data.get("issue", "")).startswith("New Asset Request"):
        db.execute(text("UPDATE assets SET status = 'Under Repair' WHERE id = :asset_id"), {"asset_id": valid_asset_id})
    
    db.commit()
    log_activity(db, operator_name, "Create Repair", f"Created repair request {rep_id} for asset {valid_asset_id or 'General Request'}")
    
    is_new_asset = str(rep_data.get("issue", "")).startswith("New Asset Request") or "new ticket" in str(rep_data.get("issue", "")).lower() or "request new" in str(rep_data.get("issue", "")).lower()
    if is_new_asset:
        notif_title = "New IT Equipment Ticket Raised"
        notif_msg = f"New Ticket {rep_id} raised by {operator_name}: '{rep_data['issue']}'"
    else:
        notif_title = "New Support Ticket Raised"
        notif_msg = f"Ticket {rep_id} raised by {operator_name} for asset {valid_asset_id or 'N/A'}: '{rep_data['issue']}'"

    # Create Broadcast Notification for Admin (employee_id = None)
    create_notification(
        db,
        notif_title,
        notif_msg,
        "warning",
        None
    )

    # Trigger Email Dispatch Asynchronously
    try:
        from services.email_service import send_email_async
        from app.config import settings
        # Collect recipient emails for Admin notification (DB Admins + default SMTP_USER)
        admin_emails = set()
        default_admin = getattr(settings, "SMTP_USER", "helloquad05@gmail.com")
        if default_admin:
            admin_emails.add(default_admin)
        
        try:
            admin_rows = db.execute(text("SELECT email FROM employees WHERE role = 'Admin' AND email IS NOT NULL AND email != ''")).all()
            for r in admin_rows:
                if r.email:
                    admin_emails.add(r.email)
        except Exception as e_adm:
            print(f"[create_repair] Warning: Failed fetching DB admin emails: {e_adm}")

        email_subject = f"[QITS Ticket {rep_id}] {notif_title}"
        email_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="background-color: #0f172a; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
              <h2 style="margin:0;">QITS IT Asset Management Desk</h2>
            </div>
            <div style="padding: 20px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 8px 8px;">
              <h3 style="color: #2563eb;">{notif_title}</h3>
              <p><strong>Ticket ID:</strong> {rep_id}</p>
              <p><strong>Raised By:</strong> {operator_name} (Employee ID: {rep_data['reported_by']})</p>
              <p><strong>Issue / Item:</strong> {rep_data['issue']}</p>
              <p><strong>Priority:</strong> {rep_data.get('priority', 'Medium')}</p>
              <p><strong>Description / Details:</strong> {rep_data.get('description', 'N/A')}</p>
              <p><strong>Request Date (IST):</strong> {req_date}</p>
              <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
              <p style="font-size: 12px; color: #64748b;">This is an automated notification from Quadrant IT Services Management System.</p>
            </div>
          </body>
        </html>
        """
        for admin_email in admin_emails:
            send_email_async(admin_email, email_subject, email_body)

        # Send confirmation email to Employee if email exists
        emp = db.execute(text("SELECT email FROM employees WHERE id = :id"), {"id": rep_data['reported_by']}).first()
        if emp and emp.email:
            emp_subject = f"[QITS Ticket {rep_id}] Ticket Submitted Successfully ({notif_title})"
            emp_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="background-color: #0f172a; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                  <h2 style="margin:0;">Quadrant IT Support Desk</h2>
                </div>
                <div style="padding: 20px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 8px 8px;">
                  <h3 style="color: #16a34a;">Ticket Submission Received</h3>
                  <p>Hello {operator_name},</p>
                  <p>Your ticket request (Ticket ID: <strong>{rep_id}</strong>) has been successfully logged. Our IT Support team has been notified and will review your request shortly.</p>
                  <p><strong>Ticket Category:</strong> {notif_title}</p>
                  <p><strong>Summary / Requested Item:</strong> {rep_data['issue']}</p>
                  <p><strong>Priority:</strong> {rep_data.get('priority', 'Medium')}</p>
                  <p><strong>Description:</strong> {rep_data.get('description', 'N/A')}</p>
                  <p><strong>Status:</strong> In Progress / Awaiting Review</p>
                  <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
                  <p style="font-size: 12px; color: #64748b;">Quadrant IT Services Asset Management System</p>
                </div>
              </body>
            </html>
            """
            send_email_async(emp.email, emp_subject, emp_body)
    except Exception as email_err:
        print(f"[Email Dispatch Warning] {email_err}")

    return get_repair_by_id(db, rep_id)

def add_repair_update_service(db: Session, rep_id: str, status: str, message: str, operator_name: str):
    repair = get_repair_by_id(db, rep_id)
    if not repair:
        return False
        
    now_str = get_ist_now().strftime("%d %b %Y, %I:%M %p")
    
    # Insert update
    db.execute(text("""
        INSERT INTO repair_updates (repair_id, date, message)
        VALUES (:rep_id, :date, :message)
    """), {
        "rep_id": rep_id,
        "date": now_str,
        "message": message
    })
    
    # Update status
    db.execute(text("UPDATE repairs SET status = :status WHERE id = :id"), {"status": status, "id": rep_id})
    
    # If completed or cancelled, make asset available again
    if status in ["Completed", "Cancelled"]:
        if repair.asset_id:
            db.execute(text("UPDATE assets SET status = 'Available' WHERE id = :asset_id"), {"asset_id": repair.asset_id})
        log_activity(db, operator_name, f"Resolve/Cancel Repair", f"Status of repair request {rep_id} set to {status}")
    else:
        log_activity(db, operator_name, "Update Repair", f"Updated repair status of {rep_id} to {status}")
        
    db.commit()
    if repair and repair.reported_by:
        create_notification(
            db,
            f"Update on Repair Ticket {rep_id}",
            f"Status: {status}. {message}",
            "info" if status != "Completed" else "success",
            repair.reported_by
        )
    return True

def accept_repair_service(db: Session, rep_id: str, admin_name: str):
    repair = get_repair_by_id(db, rep_id)
    if not repair:
        return False
        
    now_str = get_ist_now().strftime("%d %b %Y, %I:%M %p")
    
    db.execute(text("""
        UPDATE repairs 
        SET accepted_by = :admin, accepted_date = :adate, assigned_to = :admin, status = 'In Progress'
        WHERE id = :id
    """), {
        "admin": admin_name,
        "adate": now_str,
        "id": rep_id
    })
    
    db.execute(text("""
        INSERT INTO repair_updates (repair_id, date, message)
        VALUES (:rep_id, :date, :message)
    """), {
        "rep_id": rep_id,
        "date": now_str,
        "message": f"Accepted by {admin_name} and assigned for resolution."
    })
    
    if repair.asset_id:
        db.execute(text("UPDATE assets SET status = 'Under Repair' WHERE id = :asset_id"), {"asset_id": repair.asset_id})
    
    db.commit()
    log_activity(db, admin_name, "Accept Repair", f"Admin {admin_name} accepted repair ticket {rep_id}")
    if repair and repair.reported_by:
        create_notification(
            db,
            f"Repair Ticket {rep_id} Accepted",
            f"Your repair ticket for asset {repair.asset_id or 'General Request'} has been accepted by {admin_name}.",
            "info",
            repair.reported_by
        )
    return True

def reject_repair_service(db: Session, rep_id: str, admin_name: str):
    repair = get_repair_by_id(db, rep_id)
    if not repair:
        return False
        
    now_str = get_ist_now().strftime("%d %b %Y, %I:%M %p")
    
    db.execute(text("UPDATE repairs SET status = 'Cancelled' WHERE id = :id"), {"id": rep_id})
    
    db.execute(text("""
        INSERT INTO repair_updates (repair_id, date, message)
        VALUES (:rep_id, :date, :message)
    """), {
        "rep_id": rep_id,
        "date": now_str,
        "message": f"Rejected / Cancelled by {admin_name}."
    })
    
    if repair.asset_id:
        db.execute(text("UPDATE assets SET status = 'Available' WHERE id = :asset_id"), {"asset_id": repair.asset_id})
    
    db.commit()
    log_activity(db, admin_name, "Reject Repair", f"Admin {admin_name} rejected repair ticket {rep_id}")
    if repair and repair.reported_by:
        create_notification(
            db,
            f"Repair Ticket {rep_id} Cancelled",
            f"Your repair ticket for asset {repair.asset_id or 'General Request'} has been cancelled by {admin_name}.",
            "danger",
            repair.reported_by
        )
    return True


# --- ANNOUNCEMENT SERVICES ---

def get_announcements(db: Session):
    return db.execute(text("SELECT * FROM announcements ORDER BY id DESC")).all()

def create_announcement(db: Session, ann_data: dict, operator_name: str):
    count = db.execute(text("SELECT COUNT(*) FROM announcements")).scalar() or 0
    ann_id = f"ANN{str(count + 1).zfill(3)}"
    now_date = datetime.now().strftime("%d %b %Y")
    
    query = text("""
        INSERT INTO announcements (id, title, message, date, author, type, priority)
        VALUES (:id, :title, :message, :date, :author, :type, :priority)
    """)
    db.execute(query, {
        "id": ann_id,
        "title": ann_data["title"],
        "message": ann_data["message"],
        "date": now_date,
        "author": operator_name,
        "type": ann_data.get("type") or "General",
        "priority": ann_data.get("priority") or "Medium"
    })
    db.commit()
    log_activity(db, operator_name, "Post Announcement", f"Admin posted announcement: \"{ann_data['title']}\"")
    return db.execute(text("SELECT * FROM announcements WHERE id = :id"), {"id": ann_id}).first()

def delete_announcement(db: Session, ann_id: str, operator_name: str):
    ann = db.execute(text("SELECT * FROM announcements WHERE id = :id"), {"id": ann_id}).first()
    if ann:
        db.execute(text("DELETE FROM announcements WHERE id = :id"), {"id": ann_id})
        db.commit()
        log_activity(db, operator_name, "Delete Announcement", f"Deleted announcement: \"{ann.title}\"")
        return True
    return False


# --- GUIDELINE SERVICES ---

def get_guideline(db: Session):
    return db.execute(text("SELECT * FROM guidelines WHERE id = 'SYSTEM_GUIDELINE'")).first()

def update_guideline(db: Session, guide_data: dict, operator_name: str):
    current = get_guideline(db)
    now_date = datetime.now().strftime("%d %b %Y")
    
    sql = "UPDATE guidelines SET uploaded_date = :u_date, "
    updates = []
    params = {"u_date": now_date}
    
    for key, val in guide_data.items():
        if key in ["title", "version", "summary", "content", "file_name", "size", "download_url"]:
            updates.append(f"{key} = :{key}")
            params[key] = val
            
    sql += ", ".join(updates) + " WHERE id = 'SYSTEM_GUIDELINE'"
    db.execute(text(sql), params)
    db.commit()
    log_activity(db, operator_name, "Update Guidelines PDF", f"Admin posted updated Asset Guidelines PDF")
    return get_guideline(db)


# --- NOTIFICATION SERVICES ---

def get_notifications(db: Session, emp_id: Optional[str] = None):
    sql = "SELECT * FROM notifications WHERE employee_id IS NULL"
    params = {}
    if emp_id:
        sql += " OR employee_id = :emp_id"
        params["emp_id"] = emp_id
    sql += " ORDER BY created_at DESC"
    rows = db.execute(text(sql), params).mappings().all()
    result = []
    for r in rows:
        item = dict(r)
        item["time"] = format_relative_time(item.get("created_at"), item.get("time"))
        result.append(item)
    return result

def mark_notification_read(db: Session, notif_id: str):
    db.execute(text("UPDATE notifications SET read = TRUE WHERE id = :id"), {"id": notif_id})
    db.commit()

def mark_all_notifications_read(db: Session, emp_id: Optional[str] = None):
    sql = "UPDATE notifications SET read = TRUE WHERE read = FALSE"
    params = {}
    if emp_id:
        sql += " AND (employee_id = :emp_id OR employee_id IS NULL)"
        params["emp_id"] = emp_id
    db.execute(text(sql), params)
    db.commit()


# --- ACTIVITY LOG SERVICES ---

def get_activities(db: Session, user_email: Optional[str] = None, user_name: Optional[str] = None):
    sql = "SELECT * FROM activity_log"
    params = {}
    if user_email or user_name:
        sql += " WHERE \"user\" = :email OR \"user\" = :name"
        params["email"] = user_email
        params["name"] = user_name
    sql += " ORDER BY created_at DESC"
    return db.execute(text(sql), params).all()
