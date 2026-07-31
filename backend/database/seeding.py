import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from database.connection import Base, engine
from services.auth_service import get_password_hash

def seed_database(db: Session):
    # 1. Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # 2. Check if DB is already seeded
    print("Running database seeding/verification...")
    
    employees_count = db.execute(text("SELECT COUNT(*) FROM employees")).scalar()
    assets_count = db.execute(text("SELECT COUNT(*) FROM assets")).scalar()
    categories_count = db.execute(text("SELECT COUNT(*) FROM categories")).scalar()
    
    if employees_count and employees_count > 0 and assets_count and assets_count > 0 and categories_count and categories_count > 0:
        print(f"Database already initialized ({employees_count} employees, {assets_count} assets, {categories_count} categories). Skipping full seed.")
        return
        
    print("Database is empty or missing core collections. Seeding initial data from JSON files...")
    
    # Paths to JSON files (relative to backend directory)
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "..", "frontend", "src", "data")
    
    # helper to load JSON
    def load_json(filename):
        path = os.path.join(data_dir, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    # 3. Seed Guidelines (Singleton)
    guidelines_count = db.execute(text("SELECT COUNT(*) FROM guidelines")).scalar()
    if guidelines_count == 0:
        db.execute(text("""
            INSERT INTO guidelines (id, title, version, uploaded_date, size, file_name, summary, content, download_url)
            VALUES ('SYSTEM_GUIDELINE', 'Quadrant IT Services - Asset Policy & Usage Guidelines 2026', 'v2.4', '20 Jul 2026', '2.4 MB', 'Quadrant_IT_Asset_Policy_2026.pdf', 'Official company policy guidelines governing hardware usage, security protocols, return policies, and maintenance procedures.', '1. All assigned hardware assets remain the property of Quadrant IT Services.\n2. Employees are responsible for physical care and security of assigned laptops, monitors, and peripherals.\n3. Any hardware fault or damage must be reported immediately via the Raise Ticket portal.\n4. Assets must be returned intact upon offboarding or department transfer.', '#')
        """))
        db.commit()

    # 4. Seed Employees
    employees_data = load_json("employees.json")
    # Generate up to 125 employees if the JSON is small
    # (The frontend hook useAssetManager generates them dynamically. We should replicate that or import what we can)
    depts = ["IT", "Finance", "HR", "Marketing", "Sales"]
    designations = {
        "IT": ["System Engineer", "Network Engineer", "Technical Support", "DevOps Engineer", "Database Admin"],
        "Finance": ["Accounts Executive", "Finance Analyst", "Auditor"],
        "HR": ["HR Executive", "Talent Acquisition", "HR Manager"],
        "Marketing": ["Marketing Manager", "SEO Specialist", "Content Writer"],
        "Sales": ["Sales Manager", "Account Executive"]
    }
    
    names = [
        "Vikram Reddy", "Sneha Iyer", "Karan Johar", "Alia Bhatt", "Deepika Padukone",
        "Ranveer Singh", "Ranbir Kapoor", "Ayushmann Khurrana", "Rajkummar Rao", "Vicky Kaushal",
        "Kiara Advani", "Siddharth Malhotra", "Kriti Sanon", "Varun Dhawan", "Sara Ali Khan",
        "Janhvi Kapoor", "Ananya Panday", "Ishaan Khatter", "Kartik Aaryan", "Rashmika Mandanna",
        "Vijay Deverakonda", "Samantha Ruth", "Nayanthara", "Dulquer Salmaan", "Fahadh Faasil",
        "Allu Arjun", "Ram Charan", "NTR Jr", "Prabhas", "Mahesh Babu", "Yash", "Rishab Shetty"
    ]
    
    # We will construct a seed list of employees
    seed_employees = []
    # Add initial JSON employees first
    for emp in employees_data:
        role = "Admin" if emp["id"] in ["EMP001", "EMP000", "EMP002"] else "Employee"
        username = emp.get("username") or (emp["email"].split('@')[0] if "email" in emp else emp["name"].lower().replace(' ', '.'))
        
        # Override EMP001 name
        name = "Rakesh Reddy" if emp["id"] == "EMP001" else emp["name"]
        email = "rakesh.reddy@company.com" if emp["id"] == "EMP001" else emp.get("email", f"{username}@company.com")
        
        seed_employees.append({
            "id": emp["id"],
            "name": name,
            "department": emp.get("department", "IT"),
            "designation": emp.get("designation", "Specialist"),
            "email": email,
            "username": username,
            "phone": emp.get("phone", "+91 98765 43210"),
            "status": emp.get("status", "Active"),
            "role": role,
            "avatar": emp.get("avatar"),
            "joining_date": emp.get("joiningDate") or emp.get("joining_date") or "01 Jan 2024",
            "location": emp.get("location", "Hyderabad, India"),
            "password_hash": get_password_hash("admin123" if role == "Admin" else "employee123")
        })
        
    # Fill up to 125 employees for pagination demo
    for i in range(len(seed_employees) + 1, 126):
        name = names[i % len(names)] + " " + chr(65 + (i % 26))
        dept = depts[i % len(depts)]
        desList = designations[dept]
        des = desList[i % len(desList)]
        status = "Active" if i <= 110 else "Inactive"
        username = name.lower().replace(' ', '.')
        
        seed_employees.append({
            "id": f"EMP{str(i).zfill(3)}",
            "name": name,
            "department": dept,
            "designation": des,
            "email": f"{username}@company.com",
            "username": username,
            "phone": f"+91 9{str(100000000 + i * 37)[:9]}",
            "status": status,
            "role": "Employee",
            "avatar": f"https://images.unsplash.com/photo-{1500000000000 + i * 100000}?w=100&h=100&fit=crop&crop=faces",
            "joining_date": f"{str(1 + (i % 28)).zfill(2)} {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i % 12]} 2024",
            "location": "Hyderabad, India",
            "password_hash": get_password_hash("employee123")
        })

    # Always ensure rakesh.reddy (EMP1005) exists as in frontend hook
    if not any(e["id"] == "EMP1005" for e in seed_employees):
        seed_employees.append({
            "id": "EMP1005",
            "name": "Rakesh kore",
            "department": "IT Development",
            "designation": "Software Developer",
            "email": "rakesh.kore@company.com",
            "username": "rakesh.kore",
            "phone": "+91 98765 43210",
            "status": "Active",
            "role": "Employee",
            "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=faces",
            "joining_date": "10 May 2024",
            "location": "Hyderabad, India",
            "password_hash": get_password_hash("employee123")
        })

    # Batch insert employees
    for emp in seed_employees:
        try:
            # Check duplicate ID
            existing = db.execute(text("SELECT id FROM employees WHERE id = :id"), {"id": emp["id"]}).first()
            if not existing:
                # Check duplicate email or username
                conflict = db.execute(text("SELECT id FROM employees WHERE email = :email OR username = :username"), {"email": emp["email"], "username": emp["username"]}).first()
                if conflict:
                    emp["username"] = f"{emp['username']}_{emp['id']}"
                    emp["email"] = f"{emp['username']}@company.com"
                db.execute(text("""
                    INSERT INTO employees (id, name, department, designation, email, username, phone, status, role, avatar, joining_date, location, password_hash)
                    VALUES (:id, :name, :department, :designation, :email, :username, :phone, :status, :role, :avatar, :joining_date, :location, :password_hash)
                """), emp)
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Skipping employee {emp['id']}: {e}")
    print(f"Seeded {len(seed_employees)} employees.")

    # 5. Seed Categories
    # We will seed the standard categories used in the frontend
    initial_categories = [
      { "id": 'CAT001', "name": 'Laptop', "description": 'Portable computer devices assigned to individual employees for daily work', "icon_name": 'Laptop', "group": 'IT', "scope": 'Employee', "owner_entity": 'Quadrant IT Services Asset' },
      { "id": 'CAT002', "name": 'Monitor', "description": 'External high-res display screens for desktop setups and workstations', "icon_name": 'Monitor', "group": 'IT', "scope": 'Organization', "owner_entity": 'Quadrant IT Services Asset' },
      { "id": 'CAT003', "name": 'Mouse', "description": 'Wireless and optical ergonomic pointing devices for workers', "icon_name": 'Mouse', "group": 'IT', "scope": 'Employee', "owner_entity": 'Quadrant IT Services Asset' },
      { "id": 'CAT004', "name": 'Keyboard', "description": 'Mechanical and membrane keyboards assigned to employees', "icon_name": 'Keyboard', "group": 'IT', "scope": 'Employee', "owner_entity": 'Quadrant IT Services Asset' },
      { "id": 'CAT005', "name": 'Headphones', "description": 'Audio headsets and noise-cancelling headphones for workers', "icon_name": 'Headphones', "group": 'IT', "scope": 'Employee', "owner_entity": 'Quadrant IT Services Asset' },
      { "id": 'CAT006', "name": 'Printer', "description": 'Shared department laser printers and corporate office hardware', "icon_name": 'Printer', "group": 'IT', "scope": 'Organization', "owner_entity": 'Quadrant IT Services Asset' },
      { "id": 'CAT007', "name": 'Cpu', "description": 'Central processing units, servers, and corporate IT workstations', "icon_name": 'Cpu', "group": 'IT', "scope": 'Organization', "owner_entity": 'Quadrant IT Services Asset' },
      { "id": 'CAT008', "name": 'Chairs', "description": 'Ergonomic mesh office chairs and executive seating', "icon_name": 'Briefcase', "group": 'Non-IT', "scope": 'Organization', "owner_entity": 'Quadrant IT Services Asset' },
      { "id": 'CAT009', "name": 'Tables', "description": 'Modular office desks, conference and standing tables', "icon_name": 'Grid', "group": 'Non-IT', "scope": 'Organization', "owner_entity": 'Quadrant IT Services Asset' },
      { "id": 'CAT010', "name": 'Whiteboards', "description": 'Magnetic dry-erase boards and presentation panels', "icon_name": 'Grid', "group": 'Non-IT', "scope": 'Organization', "owner_entity": 'Quadrant IT Services Asset' },
      { "id": 'CAT011', "name": 'Storage Cabinets', "description": 'Filing cabinets, lockers and pedestal drawers', "icon_name": 'Box', "group": 'Non-IT', "scope": 'Organization', "owner_entity": 'Quadrant IT Services Asset' },
      { "id": 'CAT012', "name": 'DSV Laptop', "description": 'DSV Logistics client hardware & laptops', "icon_name": 'Laptop', "group": 'IT', "scope": 'Employee', "owner_entity": 'DSV Asset' },
      { "id": 'CAT013', "name": 'DSV Barcode Scanner', "description": 'DSV Warehouse hand-held inventory scanners', "icon_name": 'Cpu', "group": 'IT', "scope": 'Organization', "owner_entity": 'DSV Asset' },
      { "id": 'CAT014', "name": 'DSV Pallet Rack', "description": 'DSV Industrial storage racking systems', "icon_name": 'Box', "group": 'Non-IT', "scope": 'Organization', "owner_entity": 'DSV Asset' },
      { "id": 'CAT015', "name": 'DHL Laptop', "description": 'DHL Logistics client hardware & laptops', "icon_name": 'Laptop', "group": 'IT', "scope": 'Employee', "owner_entity": 'DHL Asset' },
      { "id": 'CAT016', "name": 'DHL Barcode Scanner', "description": 'DHL Warehouse hand-held inventory scanners', "icon_name": 'Cpu', "group": 'IT', "scope": 'Organization', "owner_entity": 'DHL Asset' },
      { "id": 'CAT017', "name": 'DHL Pallet Rack', "description": 'DHL Industrial storage racking systems', "icon_name": 'Box', "group": 'Non-IT', "scope": 'Organization', "owner_entity": 'DHL Asset' }
    ]
    for cat in initial_categories:
        try:
            existing = db.execute(text("SELECT id FROM categories WHERE id = :id"), {"id": cat["id"]}).first()
            if not existing:
                db.execute(text("""
                    INSERT INTO categories (id, name, description, icon_name, "group", scope, owner_entity)
                    VALUES (:id, :name, :description, :icon_name, :group, :scope, :owner_entity)
                """), cat)
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Skipping category {cat['id']}: {e}")

    # 6. Seed Assets
    assets_data = load_json("assets.json")
    seed_assets = []
    
    types = ["Laptop", "Monitor", "Mouse", "Keyboard", "Headset", "Printer", "Docking Station"]
    brands = {
        "Laptop": ["Dell", "HP", "Apple", "Lenovo"],
        "Monitor": ["Dell", "HP", "Samsung", "LG"],
        "Mouse": ["Logitech", "Dell", "HP", "Apple"],
        "Keyboard": ["Dell", "Logitech", "HP", "Lenovo"],
        "Headset": ["HP", "JBL", "Logitech", "Sony"],
        "Printer": ["HP", "Canon", "Epson"],
        "Docking Station": ["Dell", "Lenovo", "HP"]
    }
    models = {
        "Laptop": ["Latitude 5440", "ProBook 450", "MacBook Pro 14", "ThinkPad E14"],
        "Monitor": ["P2419H", "E2420H", "SyncMaster", "UltraFine"],
        "Mouse": ["M185", "MS116", "Essential Mouse", "Magic Mouse"],
        "Keyboard": ["KB216", "K120", "Classic Keyboard", "Preferred Pro"],
        "Headset": ["H200", "Quantum 100", "H111", "MDR-ZX110"],
        "Printer": ["LaserJet 1020", "LBP6030w", "L3210"],
        "Docking Station": ["WD19S", "ThinkPad Dock", "USB-C G5 Dock"]
    }
    images = {
        "Laptop": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=80&h=80&fit=crop",
        "Monitor": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=80&h=80&fit=crop",
        "Mouse": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=80&h=80&fit=crop",
        "Keyboard": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=80&h=80&fit=crop",
        "Headset": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=80&h=80&fit=crop",
        "Printer": "https://images.unsplash.com/photo-1612815154858-60aa4c59eaa6?w=80&h=80&fit=crop",
        "Docking Station": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=80&h=80&fit=crop"
    }

    qitsCounter = 1
    dsvCounter = 1
    dhlCounter = 1

    # Format JSON assets
    for idx, asset in enumerate(assets_data):
        if asset.get("type") == "Desktop":
            continue
            
        ownership = asset.get("ownership")
        if not ownership:
            if idx % 5 == 0: ownership = "DSV"
            elif idx % 7 == 0: ownership = "DHL"
            else: ownership = "Quadrant IT Services"

        prefix = "QITS"
        if ownership == "DSV":
            prefix = "DSV"
            num = dsvCounter
            dsvCounter += 1
        elif ownership == "DHL":
            prefix = "DHL"
            num = dhlCounter
            dhlCounter += 1
        else:
            prefix = "QITS"
            num = qitsCounter
            qitsCounter += 1

        asset_id = asset.get("id") or f"{prefix}{str(num).zfill(4)}"
        
        # Ensure assignedTo refers to actual employee ID or is null
        assigned_to = asset.get("assignedTo")
        if assigned_to and not any(e["id"] == assigned_to for e in seed_employees):
            assigned_to = None

        seed_assets.append({
            "id": asset_id,
            "type": asset.get("type", "Laptop"),
            "brand": asset.get("brand", "Dell"),
            "model": asset.get("model", "Latitude"),
            "serial_number": asset.get("serialNumber") or f"SN{idx}TEST",
            "status": asset.get("status") or "Available",
            "ownership": ownership,
            "group": asset.get("group") or ("Non-IT" if asset.get("type") in ["Chairs", "Tables", "Cabinets"] else "IT"),
            "charger_serial_number": asset.get("chargerSerialNumber") or "N/A",
            "condition": asset.get("condition") or "Good",
            "assigned_to": assigned_to,
            "purchase_date": asset.get("purchaseDate") or "10 May 2024",
            "warranty_end_date": asset.get("warrantyEndDate") or "10 May 2027",
            "assigned_date": asset.get("assignedDate") or "N/A",
            "assigned_at": datetime.utcnow() if asset.get("status") == "Assigned" else None,
            "image": asset.get("image") or images.get(asset.get("type", "Laptop"))
        })

    # Fill up to 260 assets as in frontend hook
    for i in range(len(seed_assets) + 1, 261):
        type_ = types[i % len(types)]
        brand = brands[type_][i % len(brands[type_])]
        model = models[type_][i % len(models[type_])]
        
        status = "Available"
        assigned_to = None
        if i <= 180:
            status = "Assigned"
            assigned_to = f"EMP{str(1 + (i % 110)).zfill(3)}"
            # Verify assigned_to exists
            if not any(e["id"] == assigned_to for e in seed_employees):
                assigned_to = "EMP001"
        elif i <= 230:
            status = "Available"
        elif i <= 250:
            status = "Under Repair"
        else:
            status = "Disposed"

        ownership = "Quadrant IT Services"
        prefix = "QITS"
        if i % 5 == 0:
            ownership = "DSV"
            prefix = "DSV"
            num = dsvCounter
            dsvCounter += 1
        elif i % 7 == 0:
            ownership = "DHL"
            prefix = "DHL"
            num = dhlCounter
            dhlCounter += 1
        else:
            ownership = "Quadrant IT Services"
            prefix = "QITS"
            num = qitsCounter
            qitsCounter += 1

        p_date = f"{str(1 + (i % 28)).zfill(2)} {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i % 12]} 2024"
        w_date = f"{str(1 + (i % 28)).zfill(2)} {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i % 12]} 2027"
        c_sn = f"CHG-SN-{str(80000000 + i * 93)[:8]}" if type_ == 'Laptop' else 'N/A'
        cond = 'Poor' if i % 12 == 0 else 'Working' if i % 4 == 0 else 'Good'
        a_date = f"{str(1 + ((i + 5) % 28)).zfill(2)} {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][(i + 1) % 12]} 2024" if status == 'Assigned' else 'N/A'

        seed_assets.append({
            "id": f"{prefix}{str(num).zfill(4)}",
            "type": type_,
            "brand": brand,
            "model": model,
            "serial_number": f"SN{str(10000000 + i * 87)[:8]}",
            "status": status,
            "ownership": ownership,
            "group": "IT",
            "charger_serial_number": c_sn,
            "condition": cond,
            "assigned_to": assigned_to,
            "purchase_date": p_date,
            "warranty_end_date": w_date,
            "assigned_date": a_date,
            "assigned_at": datetime.utcnow() if status == "Assigned" else None,
            "image": images[type_]
        })

    # Add Rakesh Reddy's personal test assets (id QITS9001 to QITS9005)
    rakesh_test_assets = [
        {
          "id": "QITS9001",
          "type": "Laptop",
          "brand": "Dell",
          "model": "Latitude 5420",
          "serial_number": "DELL5420X1",
          "status": "Assigned",
          "ownership": "Quadrant IT Services",
          "group": "IT",
          "charger_serial_number": "CHG-DELL-5420X1",
          "condition": "Good",
          "assigned_to": "EMP1005",
          "purchase_date": "10 May 2024",
          "warranty_end_date": "10 May 2027",
          "assigned_date": "12 May 2024",
          "assigned_at": datetime.utcnow(),
          "image": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=80&h=80&fit=crop"
        },
        {
          "id": "QITS9002",
          "type": "Monitor",
          "brand": "LG",
          "model": '24" Full HD Monitor',
          "serial_number": "LG24FHDX2",
          "status": "Assigned",
          "ownership": "Quadrant IT Services",
          "group": "IT",
          "charger_serial_number": "N/A",
          "condition": "Good",
          "assigned_to": "EMP1005",
          "purchase_date": "10 May 2024",
          "warranty_end_date": "10 May 2027",
          "assigned_date": "12 May 2024",
          "assigned_at": datetime.utcnow(),
          "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=80&h=80&fit=crop"
        },
        {
          "id": "QITS9003",
          "type": "Keyboard",
          "brand": "Logitech",
          "model": "Wireless Keyboard",
          "serial_number": "LOGIWKBX3",
          "status": "Assigned",
          "ownership": "Quadrant IT Services",
          "group": "IT",
          "charger_serial_number": "N/A",
          "condition": "Good",
          "assigned_to": "EMP1005",
          "purchase_date": "10 May 2024",
          "warranty_end_date": "10 May 2027",
          "assigned_date": "12 May 2024",
          "assigned_at": datetime.utcnow(),
          "image": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=80&h=80&fit=crop"
        },
        {
          "id": "QITS9004",
          "type": "Mouse",
          "brand": "Dell",
          "model": "Wireless Mouse",
          "serial_number": "DELLMSX4",
          "status": "Assigned",
          "ownership": "Quadrant IT Services",
          "group": "IT",
          "charger_serial_number": "N/A",
          "condition": "Good",
          "assigned_to": "EMP1005",
          "purchase_date": "10 May 2024",
          "warranty_end_date": "10 May 2027",
          "assigned_date": "12 May 2024",
          "assigned_at": datetime.utcnow(),
          "image": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=80&h=80&fit=crop"
        },
        {
          "id": "QITS9005",
          "type": "Headset",
          "brand": "Jabra",
          "model": "Evolve 20 Headset",
          "serial_number": "JABRAE20X5",
          "status": "Assigned",
          "ownership": "Quadrant IT Services",
          "group": "IT",
          "charger_serial_number": "N/A",
          "condition": "Good",
          "assigned_to": "EMP1005",
          "purchase_date": "10 May 2024",
          "warranty_end_date": "10 May 2027",
          "assigned_date": "12 May 2024",
          "assigned_at": datetime.utcnow(),
          "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=80&h=80&fit=crop"
        }
    ]
    seed_assets.extend(rakesh_test_assets)

    # Insert assets
    for asset in seed_assets:
        try:
            existing = db.execute(text("SELECT id FROM assets WHERE id = :id"), {"id": asset["id"]}).first()
            if not existing:
                sn_exists = db.execute(text("SELECT id FROM assets WHERE serial_number = :sn"), {"sn": asset["serial_number"]}).first()
                if sn_exists:
                    asset["serial_number"] = f"{asset['serial_number']}_{asset['id']}"
                db.execute(text("""
                    INSERT INTO assets (id, type, brand, model, serial_number, status, ownership, "group", charger_serial_number, condition, assigned_to, purchase_date, warranty_end_date, assigned_date, assigned_at, image)
                    VALUES (:id, :type, :brand, :model, :serial_number, :status, :ownership, :group, :charger_serial_number, :condition, :assigned_to, :purchase_date, :warranty_end_date, :assigned_date, :assigned_at, :image)
                """), asset)
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Skipping asset {asset['id']}: {e}")
    print(f"Seeded {len(seed_assets)} assets.")

    # 7. Seed Licenses
    licenses_data = load_json("licenses.json")
    for idx, lic in enumerate(licenses_data):
        lic_id = lic.get("id") or f"LIC{str(idx + 1).zfill(3)}"
        try:
            existing = db.execute(text("SELECT id FROM licenses WHERE id = :id"), {"id": lic_id}).first()
            if not existing:
                db.execute(text("""
                    INSERT INTO licenses (id, name, status, vendor, license_key, seats, cost, start_date, end_date, alert_days_before, admin_email, description)
                    VALUES (:id, :name, :status, :vendor, :license_key, :seats, :cost, :start_date, :end_date, :alert_days_before, :admin_email, :description)
                """), {
                    "id": lic_id,
                    "name": lic["name"],
                    "status": lic.get("status") or "Available",
                    "vendor": lic.get("vendor") or "Subscription",
                    "license_key": lic.get("licenseKey") or "N/A",
                    "seats": lic.get("seats") or 10,
                    "cost": lic.get("cost") or "N/A",
                    "start_date": lic.get("startDate") or "10 May 2024",
                    "end_date": lic["endDate"],
                    "alert_days_before": lic.get("alertDaysBefore") or 30,
                    "admin_email": lic.get("adminEmail") or "rakesh.reddy@company.com",
                    "description": lic.get("description") or "License subscription."
                })
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Skipping license {lic_id}: {e}")

    # 8. Seed Repairs
    repairs_data = load_json("repairs.json")
    seed_repairs = []
    
    # We will seed repairs based on the JSON
    for idx, rep in enumerate(repairs_data):
        rep_id = rep["id"]
        # Ensure reportedBy refers to actual employee ID or is null
        reported_by = rep.get("reportedBy") or rep.get("reported_by")
        if reported_by and not any(e["id"] == reported_by for e in seed_employees):
            reported_by = "EMP001"
            
        # Ensure asset_id exists in assets
        asset_id = rep.get("assetId") or rep.get("asset_id")
        if asset_id and not any(a["id"] == asset_id for a in seed_assets):
            continue

        seed_repairs.append({
            "id": rep_id,
            "asset_id": asset_id,
            "reported_by": reported_by,
            "issue": rep["issue"],
            "description": rep.get("description") or rep.get("issue"),
            "request_date": rep.get("requestDate") or rep.get("request_date") or "18 May 2024 11:45 AM",
            "priority": rep.get("priority", "Medium"),
            "assigned_to": rep.get("assignedTo") or "IT Support Team",
            "estimated_completion": rep.get("estimatedCompletion") or "Awaiting inspection",
            "status": rep.get("status") or "Pending",
            "accepted_by": rep.get("acceptedBy") or ("Rakesh Reddy (Admin)" if idx % 2 == 0 else None),
            "accepted_date": rep.get("acceptedDate") or (rep.get("requestDate") or "18 May 2024 11:45 AM" if idx % 2 == 0 else None)
        })

    for rep in seed_repairs:
        try:
            existing = db.execute(text("SELECT id FROM repairs WHERE id = :id"), {"id": rep["id"]}).first()
            if not existing:
                db.execute(text("""
                    INSERT INTO repairs (id, asset_id, reported_by, issue, description, request_date, priority, assigned_to, estimated_completion, status, accepted_by, accepted_date)
                    VALUES (:id, :asset_id, :reported_by, :issue, :description, :request_date, :priority, :assigned_to, :estimated_completion, :status, :accepted_by, :accepted_date)
                """), rep)
                
                # Add updates for these repairs
                db.execute(text("""
                    INSERT INTO repair_updates (repair_id, date, message)
                    VALUES (:rep_id, :date, :message)
                """), {
                    "rep_id": rep["id"],
                    "date": rep["request_date"],
                    "message": "Repair request created."
                })
                if rep["accepted_by"]:
                    db.execute(text("""
                        INSERT INTO repair_updates (repair_id, date, message)
                        VALUES (:rep_id, :date, :message)
                    """), {
                        "rep_id": rep["id"],
                        "date": rep["accepted_date"],
                        "message": f"Accepted by {rep['accepted_by']} and assigned for resolution."
                    })
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Skipping repair {rep['id']}: {e}")

    # 9. Seed Announcements
    # Standard initial announcements from Hook
    default_announcements = [
      {
        "id": "ANN001",
        "title": "System Maintenance Schedule",
        "message": "Central IT servers will be under scheduled maintenance this Sunday from 2:00 AM to 4:00 AM. Access to internal software repositories may be briefly interrupted.",
        "date": "20 Jul 2026",
        "author": "IT Admin Desk",
        "type": "Maintenance",
        "priority": "Medium"
      },
      {
        "id": "ANN002",
        "title": "Quarterly Asset Verification Audit",
        "message": "All department employees must verify their assigned hardware items (serial number and condition) before the end-of-quarter audit.",
        "date": "18 Jul 2026",
        "author": "IT Operations",
        "type": "General",
        "priority": "High"
      }
    ]
    for ann in default_announcements:
        try:
            existing = db.execute(text("SELECT id FROM announcements WHERE id = :id"), {"id": ann["id"]}).first()
            if not existing:
                db.execute(text("""
                    INSERT INTO announcements (id, title, message, date, author, type, priority)
                    VALUES (:id, :title, :message, :date, :author, :type, :priority)
                """), ann)
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Skipping announcement {ann['id']}: {e}")

    # 10. Seed Notifications
    notifs_data = load_json("notifications.json")
    for idx, notif in enumerate(notifs_data):
        notif_id = notif.get("id") or f"NOTF{str(idx+1).zfill(3)}"
        try:
            existing = db.execute(text("SELECT id FROM notifications WHERE id = :id"), {"id": notif_id}).first()
            if not existing:
                db.execute(text("""
                    INSERT INTO notifications (id, title, message, time, read, type)
                    VALUES (:id, :title, :message, :time, :read, :type)
                """), {
                    "id": notif_id,
                    "title": notif["title"],
                    "message": notif["message"],
                    "time": notif.get("time") or notif.get("date") or "Just now",
                    "read": notif.get("read") or False,
                    "type": notif.get("type") or "info"
                })
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Skipping notification {notif_id}: {e}")

    # 11. Seed Activities
    activities_data = load_json("activity.json")
    for idx, act in enumerate(activities_data):
        act_id = act.get("id") or f"ACT{str(idx+1).zfill(3)}"
        try:
            existing = db.execute(text("SELECT id FROM activity_log WHERE id = :id"), {"id": act_id}).first()
            if not existing:
                db.execute(text("""
                    INSERT INTO activity_log (id, "user", activity, details, ip_address, date_time)
                    VALUES (:id, :user, :activity, :details, :ip_address, :date_time)
                """), {
                    "id": act_id,
                    "user": "Rakesh Reddy" if act.get("user") == "Rakesh Kumar" else act.get("user", "System"),
                    "activity": act.get("activity", "System Action"),
                    "details": act.get("details", "").replace("Rakesh Kumar", "Rakesh Reddy"),
                    "ip_address": act.get("ipAddress") or "192.168.1.10",
                    "date_time": act.get("dateTime") or "10 May 2024, 09:15 AM"
                })
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Skipping activity log {act_id}: {e}")

    # 12. Align legacy database records
    # Assign existing repairs and assets that have NULL/None to EMP010 (Rakesh Kore) so they display correctly
    print("Aligning legacy database records...")
    db.execute(text("UPDATE repairs SET reported_by = 'EMP010' WHERE reported_by IS NULL"))
    db.execute(text("UPDATE assets SET assigned_to = 'EMP010' WHERE status = 'Assigned' AND assigned_to IS NULL"))
    db.commit()
    
    print("Database seeding completed successfully.")
