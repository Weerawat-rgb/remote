# Standard library imports
import logging
import io
import os
import subprocess
from logging.handlers import RotatingFileHandler
from datetime import datetime


# Third-party imports
import pandas as pd
from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = '5e3d17fba71924d29490882d7bfb694f23c1a2ae720c2878'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://sa:admin123@nart:1433/RemoteAccessDB?driver=ODBC+Driver+17+for+SQL+Server&charset=utf8'
app.config['JSON_AS_ASCII'] = False

# UTF-8 configuration
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Logging configuration
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler
file_handler = RotatingFileHandler('logs/app.log', maxBytes=1024*1024, backupCount=10)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
# Models
class Customer(db.Model):
    __tablename__ = 'Customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(100), nullable=False)
    logo = db.Column(db.LargeBinary)
    logo_mimetype = db.Column(db.String(50))
    hq_contact_name = db.Column(db.Unicode(100))
    hq_contact_phone = db.Column(db.Unicode(20))
    hq_contact_email = db.Column(db.Unicode(120))
    hq_address = db.Column(db.Unicode(500))
    tax_number = db.Column(db.Unicode(100), nullable=True)
    isactive = db.Column(db.Boolean, nullable = False, default=True)
    branches = db.relationship('Branch', backref='customer', lazy=True)
    @property
    def active_branches_count(self):
        return len([branch for branch in self.branches if branch.isactive == 1])

class Branch(db.Model):
    __tablename__ = 'Branches'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    branch_code = db.Column(db.String(100))
    address = db.Column(db.String(200))
    contact_name = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))
    devices = db.relationship('Device', backref='branch', lazy=True)
    isactive = db.Column(db.Boolean, nullable=True, default=True)

class Device(db.Model):
    __tablename__ = 'Devices'
    
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('Branches.id'), nullable=False)
    machine_type = db.Column(db.String(50))
    teamviewer_id = db.Column(db.String(50))
    teamviewer_pwd = db.Column(db.String(50))
    anydesk_id = db.Column(db.String(50))
    anydesk_pwd = db.Column(db.String(50))
    notes = db.Column(db.Text)
    isactive = db.Column(db.Boolean, nullable=True, default=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
        
# Routes


@app.route('/')
def index():
    try:
        customers = Customer.query.filter_by(isactive=1).all()
        # ทดสอบ print ค่า
        for customer in customers:
            print(f"Customer name: {customer.hq_contact_name}")
        return render_template('index.html', customers=customers)
    except Exception as e:
        print(f"Error: {str(e)}")
        return str(e)
    
@app.route('/live-search')
def live_search():
    search_term = request.args.get('q', '')
    
    if search_term:
        results = db.session.query(Customer, Branch).join(
            Branch, Customer.id == Branch.customer_id
        ).filter(
            and_(
                Customer.isactive == True,
                Branch.isactive == True,
                or_(
                    Branch.name.ilike(f'%{search_term}%'),
                    Branch.branch_code.ilike(f'%{search_term}%'),
                    Customer.name.ilike(f'%{search_term}%')
                )
            )
        ).limit(5).all()
        
        search_results = [{
            'customer_id': customer.id,
            'branch_id': branch.id,
            'customer_name': customer.name,
            'branch_name': branch.name,
            'branch_code': branch.branch_code
        } for customer, branch in results]
        
        return jsonify(search_results)
    
    return jsonify([])
    
@app.route('/api/customers/<int:customer_id>')
def get_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'hq_contact_name': customer.hq_contact_name,
        'hq_contact_phone': customer.hq_contact_phone,
        'hq_contact_email': customer.hq_contact_email,
        'hq_address': customer.hq_address,
        'has_logo': customer.logo is not None,  
        'tax_number': customer.tax_number,  
        'logo_mimetype': customer.logo_mimetype if customer.logo else None
    })
    
@app.route('/customer-logo/<int:customer_id>')
def customer_logo(customer_id):
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Debug print
        print(f"Fetching logo for customer {customer_id}")
        print(f"Logo exists: {customer.logo is not None}")
        print(f"Mimetype: {customer.logo_mimetype}")
        
        if customer.logo:
            # สร้าง BytesIO object จาก binary data
            logo_data = io.BytesIO(customer.logo)
            # Reset pointer to start of file
            logo_data.seek(0)
            
            # ส่งไฟล์กลับไปพร้อม mimetype
            return send_file(
                logo_data,
                mimetype=customer.logo_mimetype or 'image/png'  # default to PNG if mimetype is None
            )
    except Exception as e:
        print(f"Error serving logo: {str(e)}")
        return '', 404

@app.route('/api/customers/<int:id>/logo')
def get_customer_logo(id):
    customer = Customer.query.get_or_404(id)
    if customer.logo:
        return send_file(
            io.BytesIO(customer.logo),
            mimetype=customer.logo_mimetype
        )
    return '', 404

@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        try:
            # Debug: print ข้อมูลที่ได้รับจาก form
            print("Form data:", request.form)
            print("Files:", request.files)
            
            name = request.form.get('name')
            hq_contact_name = request.form.get('hq_contact_name')
            hq_contact_phone = request.form.get('hq_contact_phone')
            hq_contact_email = request.form.get('hq_contact_email')
            hq_address = request.form.get('hq_address')
            tax_number = request.form.get('tax_number')
            
            # รับไฟล์ logo
            logo_file = request.files.get('logo')

            # ตรวจสอบว่ามีข้อมูลที่จำเป็น
            if not name:
                flash('กรุณากรอกชื่อลูกค้า', 'error')
                return redirect(url_for('add_customer'))

            new_customer = Customer(
                name=name,
                hq_contact_name=hq_contact_name,
                hq_contact_phone=hq_contact_phone,
                hq_contact_email=hq_contact_email,
                hq_address=hq_address,
                tax_number=tax_number
            )

            # ถ้ามีการอัพโหลด logo
            if logo_file and logo_file.filename != '':
                # อ่านไฟล์เป็น binary
                logo_binary = logo_file.read()
                new_customer.logo = logo_binary
                new_customer.logo_filename = secure_filename(logo_file.filename)
                new_customer.logo_mimetype = logo_file.mimetype

            db.session.add(new_customer)
            db.session.commit()
            flash('เพิ่มข้อมูลลูกค้าสำเร็จ', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')
            print(f"Error: {str(e)}")
            return redirect(url_for('add_customer'))
            
    return render_template('add_customer.html')

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Debug prints
        print("Files:", request.files)
        print("Form data:", request.form)
        
        # Update text fields from form data
        customer.name = request.form.get('name', customer.name)
        customer.hq_contact_name = request.form.get('hq_contact_name', customer.hq_contact_name)
        customer.hq_contact_phone = request.form.get('hq_contact_phone', customer.hq_contact_phone)
        customer.hq_contact_email = request.form.get('hq_contact_email', customer.hq_contact_email)
        customer.hq_address = request.form.get('hq_address', customer.hq_address)
        customer.tax_number = request.form.get('tax_number', customer.tax_number)
        
        # Handle logo update if file is provided
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename != '':
                print(f"Processing new logo: {logo_file.filename}")
                
                # Read the file as binary data
                logo_data = logo_file.read()
                
                # Update logo and mimetype
                customer.logo = logo_data
                customer.logo_mimetype = logo_file.mimetype
                
                print(f"Updated logo size: {len(logo_data)} bytes")
                print(f"Updated mimetype: {logo_file.mimetype}")
        
        db.session.commit()
        print(f"Successfully updated customer {customer_id}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error updating customer: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/api/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    try:
        # ค้นหาลูกค้าจาก ID
        customer = Customer.query.get_or_404(id)
        
        active_branches_count = Branch.query.filter_by(customer_id=customer.id, isactive=1).count()
        if active_branches_count > 0:
            return jsonify({
                'success': False, 
                'message': f'ไม่สามารถลบลูกค้าได้เนื่องจากมีข้อมูลสาขาจำนวน {active_branches_count} สาขา รบกวนลบข้อมูลสาขาทั้งหมดก่อนที่จะลบลูกค้ารายนี้ครับ'
            }), 400
            
        # Soft delete โดยการ set active = 0
        customer.isactive = False
        db.session.commit()
        
        # Log การลบ
        print(f"Customer {id} deactivated successfully")
        
        return jsonify({
            'success': True,
            'message': 'ปิดการใช้งานลูกค้าเรียบร้อยแล้ว'
        })
        
    except Exception as e:
        db.session.rollback()
        # Log error
        print(f"Error deactivating customer {id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาดในการปิดการใช้งานลูกค้า: {str(e)}'
        }), 500
                
@app.route('/api/branches', methods=['POST'])
def add_branch():
    try:
        data = request.get_json()
        app.logger.info(f"Received data: {data}")
        
        # ตรวจสอบข้อมูลที่จำเป็น
        required_fields = {
            'name': 'ชื่อสาขา',
            'customer_id': 'รหัสลูกค้า',
            'branch_code': 'รหัสสาขา'
        }
        
        missing_fields = []
        for field, label in required_fields.items():
            if not data.get(field):
                missing_fields.append(label)
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'กรุณากรอก: {", ".join(missing_fields)}'
            }), 400

        # ตรวจสอบ customer_id
        customer = db.session.get(Customer, data['customer_id'])
        if not customer:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลลูกค้า'
            }), 404

        # ตรวจสอบ branch_code ซ้ำ
        existing_branch = Branch.query.filter_by(
            branch_code=data['branch_code'], 
            isactive=True
        ).first()
        
        if existing_branch:
            return jsonify({
                'success': False,
                'message': 'รหัสสาขานี้มีอยู่ในระบบแล้ว'
            }), 400

        # สร้าง Branch ใหม่
        new_branch = Branch(
            customer_id=data['customer_id'],
            name=data['name'],
            branch_code=data['branch_code'],
            contact_name=data.get('contact_name'),
            contact_phone=data.get('contact_phone'),
            address=data.get('address'),
            isactive=True
        )
        
        db.session.add(new_branch)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'เพิ่มสาขาเรียบร้อยแล้ว',
            'data': {
                'id': new_branch.id,
                'name': new_branch.name,
                'branch_code': new_branch.branch_code,
                'customer_id': new_branch.customer_id
            }
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding branch: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาดในการบันทึกข้อมูล'
        }), 500
                       
@app.route('/api/branches/<int:branch_id>', methods=['DELETE'])
def delete_branch(branch_id):
   try:
       branch = Branch.query.get_or_404(branch_id)
       # Soft delete โดยการ set isactive = False แทนการลบ
       branch.isactive = False
       db.session.commit()
       
       return jsonify({
           'success': True,
           'message': 'ปิดการใช้งานสาขาเรียบร้อยแล้ว'
       })
   except Exception as e:
       db.session.rollback()
       print(f"Error deactivating branch: {str(e)}")  # Debug log
       return jsonify({
           'success': False,
           'message': f'เกิดข้อผิดพลาด: {str(e)}'
       }), 500
 
@app.route('/api/branches/<int:branch_id>')
def get_branch_with_device(branch_id):
    try:
        branch = Branch.query.get(branch_id)
        if not branch:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลสาขา'
            }), 404
            
        # ดึงข้อมูล Device ล่าสุดของสาขา
        device = Device.query.filter_by(
            branch_id=branch_id,
            isactive=1
        ).order_by(Device.id.desc()).first()
        
        response_data = {
            'success': True,
            'id': branch.id,
            'name': branch.name,
            'branch_code': branch.branch_code,
            'contact_name': branch.contact_name,
            'contact_phone': branch.contact_phone,
            'address': branch.address
        }
        
        # เพิ่มข้อมูล Device ถ้ามี
        if device:
            response_data.update({
                'machine_type': device.machine_type,
                'teamviewer_id': device.teamviewer_id,
                'teamviewer_pwd': device.teamviewer_pwd,
                'anydesk_id': device.anydesk_id,
                'anydesk_pwd': device.anydesk_pwd,
                'notes': device.notes
            })
            
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
        
@app.route('/api/devices', methods=['POST'])
def add_device():
    try:
        data = request.get_json()
        
        # สร้าง Device ใหม่
        new_device = Device(
            branch_id=data['branch_id'],
            machine_type=data['machine_type'],
            teamviewer_id=data.get('teamviewer_id', ''),
            teamviewer_pwd=data.get('teamviewer_pwd', ''),
            anydesk_id=data.get('anydesk_id', ''),
            anydesk_pwd=data.get('anydesk_pwd', ''),
            notes=data.get('notes', ''),
            isactive=1
        )
        
        db.session.add(new_device)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'บันทึกข้อมูลรีโมทเรียบร้อยแล้ว'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/branches/<int:branch_id>/devices/<machine_type>', methods=['PUT'])
def update_device(branch_id, machine_type):
    try:
        data = request.get_json()
        
        device = db.session.query(Device).filter(
            Device.branch_id == branch_id,
            Device.machine_type == machine_type,
            Device.isactive == 1
        ).first()
        
        if device:
            # อัพเดทข้อมูล
            device.machine_type = data['machine_type']
            device.teamviewer_id = data['teamviewer_id']
            device.teamviewer_pwd = data['teamviewer_pwd']
            device.anydesk_id = data['anydesk_id']
            device.anydesk_pwd = data['anydesk_pwd']
            device.notes = data['notes']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'อัพเดทข้อมูลรีโมทเรียบร้อยแล้ว'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลเครื่อง'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
        
@app.route('/api/branches/<int:branch_id>/devices/<machine_type>')
def get_device_detail(branch_id, machine_type):
    try:
        device = db.session.query(Device).filter(
            Device.branch_id == branch_id,
            Device.machine_type == machine_type,
            Device.isactive == 1
        ).first()
        
        if device and device.isactive == 1:
            return jsonify({
                'success': True,
                'device': {
                    'teamviewer_id': device.teamviewer_id,
                    'teamviewer_pwd': device.teamviewer_pwd,
                    'anydesk_id': device.anydesk_id,
                    'anydesk_pwd': device.anydesk_pwd,
                    'notes': device.notes
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลเครื่อง'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
        
@app.route('/api/check-anydesk-status/<anydesk_id>')
def check_anydesk_status(anydesk_id):
    try:
        # ใช้ subprocess เรียก AnyDesk CLI command
        result = subprocess.run(['anydesk', '--status', anydesk_id], capture_output=True, text=True)
        is_online = 'online' in result.stdout.lower()
        
        return jsonify({
            'success': True,
            'is_online': is_online
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })
        
@app.route('/api/branches/<int:branch_id>/devices/<machine_type>', methods=['DELETE'])
def delete_device(branch_id, machine_type):
    try:
        device = db.session.query(Device).filter(
            Device.branch_id == branch_id,
            Device.machine_type == machine_type,
            Device.isactive == 1
        ).first()
        
        if device:
            # Soft delete - เปลี่ยน isactive เป็น 0
            device.isactive = 0
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'ลบข้อมูลเครื่องเรียบร้อยแล้ว'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลเครื่อง'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
        
@app.route('/customer/<int:customer_id>')
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    # customers = Customer.query.filter_by(isactive=1).all()
    return render_template('view_customer.html', customer=customer)

@app.route('/customers/<int:customer_id>/branches')
def view_branches(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    branches = Branch.query.filter_by(customer_id=customer_id).all()
    return render_template('view_branch.html', customer=customer, branches=branches)

@app.route('/branches')
def get_branches():
    branches = db.session.query(Branch).filter(Branch.isactive == 1).all()    # ดึงข้อมูลเครื่องของแต่ละสาขา
    for branch in branches:
        devices = db.session.query(Device).filter(
            Device.branch_id == branch.id,
            Device.isactive == 1
        ).all()
        branch.devices = devices
    return render_template('branches.html', branches=branches)

    
@app.route('/api/branches/<int:branch_id>', methods=['PUT'])
def edit_branch(branch_id):
    try:
        # เปลี่ยนจาก .query.get() เป็น db.session.get()
        branch = db.session.get(Branch, branch_id)
        if not branch:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลสาขา'
            }), 404

        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลที่ต้องการอัพเดท'
            }), 400

        branch.name = data.get('name', branch.name)
        branch.contact_name = data.get('contact_name', branch.contact_name)
        branch.contact_phone = data.get('contact_phone', branch.contact_phone)
        branch.address = data.get('address', branch.address)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'อัพเดทข้อมูลสาขาเรียบร้อยแล้ว'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500
        
@app.route('/api/branches/<int:customer_id>/export')
def export_branches(customer_id):
    try:
        # ดึงข้อมูลสาขาที่ active
        branches = Branch.query.filter_by(customer_id=customer_id, isactive=1).all()
        
        # สร้าง DataFrame
        data = []
        for branch in branches:
            data.append({
                'รหัสสาขา': branch.branch_code,
                'ชื่อสาขา': branch.name,
                'ชื่อผู้ติดต่อ': branch.contact_name,
                'เบอร์โทร': branch.contact_phone
            })
        
        df = pd.DataFrame(data)
        
        # สร้าง Excel file ใน memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Branches')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'branches_{customer_id}.xlsx'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/branches/<int:customer_id>/import', methods=['POST'])
def import_branches(customer_id):
    try:
        if 'file' not in request.files:
            print("No file in request")
            return jsonify({
                'success': False,
                'message': 'ไม่พบไฟล์ที่อัพโหลด'
            }), 400
            
        file = request.files['file']
        if file.filename == '':
            print("No filename")
            return jsonify({
                'success': False,
                'message': 'ไม่ได้เลือกไฟล์'
            }), 400
            
        # อ่านไฟล์ Excel และแสดงข้อมูลเพื่อ debug
        df = pd.read_excel(file)
        print("DataFrame contents:")
        print(df)
        print("DataFrame columns:", df.columns.tolist())
        
        # ตรวจสอบคอลัมน์ที่จำเป็น
        required_columns = ['รหัสสาขา', 'ชื่อสาขา']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Missing columns: {missing_columns}")
            return jsonify({
                'success': False,
                'message': f'คอลัมน์ที่จำเป็นไม่ครบ: {", ".join(missing_columns)}'
            }), 400
            
        # นำเข้าข้อมูลและแสดงแต่ละรายการ
        for _, row in df.iterrows():
            print("Processing row:", row.to_dict())
            branch = Branch(
                customer_id=customer_id,
                branch_code=str(row['รหัสสาขา']),  # แปลงเป็น string
                name=str(row['ชื่อสาขา']),  # แปลงเป็น string
                contact_name=str(row['ชื่อผู้ติดต่อ']) if pd.notna(row['ชื่อผู้ติดต่อ']) else '',
                contact_phone=str(row['เบอร์โทร']) if pd.notna(row['เบอร์โทร']) else '',
                isactive=1
            )
            print("Created branch object:", vars(branch))
            db.session.add(branch)
            
        db.session.commit()
        print("Commit successful")
        
        return jsonify({
            'success': True,
            'message': 'นำเข้าข้อมูลสำเร็จ'
        })
        
    except Exception as e:
        print("Error occurred:", str(e))
        print("Error type:", type(e))
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500                
                
@app.route('/api/branches/template')
def get_branch_template():
    try:
        # สร้าง DataFrame ว่างพร้อมคอลัมน์
        df = pd.DataFrame(columns=[
            'รหัสสาขา',
            'ชื่อสาขา',
            'ชื่อผู้ติดต่อ',
            'เบอร์โทร'
        ])
        
        # เพิ่มตัวอย่างข้อมูล 1 แถว
        df.loc[0] = [
            'B001',  # ตัวอย่างรหัสสาขา
            'สาขาตัวอย่าง',  # ตัวอย่างชื่อสาขา
            'ชื่อผู้ติดต่อ',  # ตัวอย่างชื่อผู้ติดต่อ
            '02-xxx-xxxx'  # ตัวอย่างเบอร์โทร
        ]
        
        # สร้าง Excel file ใน memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # เขียน DataFrame ลงใน Excel
            df.to_excel(writer, index=False, sheet_name='Template')
            
            # ปรับความกว้างคอลัมน์
            worksheet = writer.sheets['Template']
            worksheet.set_column('A:D', 20)  # ตั้งความกว้างคอลัมน์ A ถึง D เป็น 20
            
            # จัด format
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#4B5563',
                'border': 1
            })
            
            # ใส่ format ให้ header
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='branch_import_template.xlsx'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
        
@app.route('/summary/<int:customer_id>/<int:branch_id>')
def summary(customer_id, branch_id):
    customer = Customer.query.get_or_404(customer_id)
    branch = Branch.query.get_or_404(branch_id)
    
    # ดึงข้อมูล devices และจัดกลุ่มตาม machine_type
    devices = (Device.query
              .filter_by(branch_id=branch_id, isactive=True)
              .all())
    
    # จัดกลุ่มอุปกรณ์ตาม machine_type
    devices_by_type = {}
    for device in devices:
        if device.machine_type not in devices_by_type:
            devices_by_type[device.machine_type] = []
        devices_by_type[device.machine_type].append(device)
    
    return render_template('summary.html', 
                         customer=customer, 
                         branch=branch,
                         devices_by_type=devices_by_type)
if __name__ == '__main__':
    app.run(debug=True)