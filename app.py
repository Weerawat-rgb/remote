# Standard library imports
from flask_cors import CORS
from waitress import serve
import logging
import io
import os
# import subprocess
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from devices_warranty import customer_search
# Third-party imports
import pandas as pd
from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_, text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename


# สร้าง logs directory ถ้ายังไม่มี
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# กำหนด log file path
log_file = os.path.join(log_dir, 'app.log')
stdout_log = os.path.join(log_dir, 'stdout.log')

# ตั้งค่า logging
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# แก้ไขการจัดการ stdout
try:
    if sys.stdout is None or not hasattr(sys.stdout, 'encoding'):
        sys.stdout = open(stdout_log, 'a', encoding='utf-8')
    elif sys.stdout.encoding != 'utf-8':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
except Exception as e:
    logging.error(f"Error configuring stdout: {str(e)}")
    sys.stdout = open(stdout_log, 'a', encoding='utf-8')

# สร้าง Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = '5e3d17fba71924d29490882d7bfb694f23c1a2ae720c2878'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://info:info123@infosever.thaiddns.com,1451/RemoteAccessDB?driver=ODBC+Driver+17+for+SQL+Server&charset=utf8'
app.config['JSON_AS_ASCII'] = False

logging.getLogger('werkzeug').setLevel(logging.INFO)

CORS(app)
app.register_blueprint(customer_search)


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
    notes = db.Column(db.Text)
    website_url = db.Column(db.String(255))
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
    contact_phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
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
        
class SpareType(db.Model):
    __tablename__ = 'spare_types'
    type_id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(20), nullable=False)
    spare_parts = db.relationship('SparePart', backref='type', lazy=True)
    
class SpareModel(db.Model):
    __tablename__ = 'spare_model'
    model_id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    spare_parts = db.relationship('SparePart', backref='model', lazy=True)

class SparePart(db.Model):
    __tablename__ = 'spare_parts'
    id = db.Column(db.Integer, primary_key=True)
    spare_type_id = db.Column(db.Integer, db.ForeignKey('spare_types.type_id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('spare_model.model_id'), nullable=False)  # เพิ่ม FK
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    notes = db.Column(db.Text)
    isactive = db.Column(db.Boolean, nullable=True, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


@app.route('/')
def index():
    try:
        # Query active customers and sort by name
        customers = Customer.query.filter_by(isactive=1).order_by(Customer.name).all()
        return render_template('index.html', customers=customers)
    except Exception as e:
        print(f"Error: {str(e)}")
        return str(e)

@app.route('/devices_warranty')
def devices_warranty():
    return render_template('devices_warranty.html')
    
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
        'notes': customer.notes,  
        'website_url': customer.website_url,  
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
            # tax_number = request.form.get('tax_number')
            notes = request.form.get('notes')
            website_url = request.form.get('website_url')
            
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
                # tax_number=tax_number,
                notes=notes,
                website_url=website_url
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
            return jsonify({'status': 'success', 'message': 'บันทึกข้อมูลสำเร็จ'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 400
            
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
        customer.notes = request.form.get('notes', customer.notes)
        customer.website_url = request.form.get('website_url', customer.website_url)
        
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
                
@app.route('/api/branches/add', methods=['POST'])
def add_branch():
    try:
        # Debug: print request data
        print("Received request data:", request.get_json())
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลที่ส่งมา'
            }), 400

        # Validate required fields
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุชื่อสาขา'
            }), 400

        if not data.get('customer_id'):
            return jsonify({
                'success': False,
                'message': 'ไม่พบรหัสลูกค้า'
            }), 400

        # Create new branch
        new_branch = Branch(
            customer_id=data['customer_id'],
            name=data['name'],
            branch_code=data.get('branch_code', ''),
            contact_phone=data.get('contact_phone', ''),
            notes=data.get('notes', ''),
            isactive=True
        )
        
        # Debug: print new branch data
        print("Creating new branch:", {
            'customer_id': new_branch.customer_id,
            'name': new_branch.name,
            'branch_code': new_branch.branch_code,
            'contact_phone': new_branch.contact_phone,
            'notes': new_branch.notes
        })
        
        db.session.add(new_branch)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'เพิ่มสาขาเรียบร้อยแล้ว'
        })
        
    except Exception as e:
        print("Error occurred:", str(e))  # Debug log
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 400
                                       
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

@app.route('/api/branches/remote/<int:branch_id>', methods=['GET'])
def get_branch(branch_id):
    try:
        branch = Branch.query.get_or_404(branch_id)
        
        # เตรียมข้อมูลอุปกรณ์
        devices_data = []
        for device in branch.devices:
            if device.isactive:  # ดึงเฉพาะอุปกรณ์ที่ยังใช้งานอยู่
                devices_data.append({
                    'id': device.id,
                    'machine_type': device.machine_type,
                    'teamviewer_id': device.teamviewer_id,
                    'teamviewer_pwd': device.teamviewer_pwd,
                    'anydesk_id': device.anydesk_id,
                    'anydesk_pwd': device.anydesk_pwd,
                    'notes': device.notes
                })
        
        return jsonify({
            'success': True,
            'id': branch.id,
            'name': branch.name,
            'branch_code': branch.branch_code,
            'devices': devices_data
        })
        
    except Exception as e:
        print('Error:', str(e))  # Debug log
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
@app.route('/api/branches/<int:branch_id>', methods=['PUT'])
def update_branch(branch_id):
    try:
        data = request.get_json()
        # print("Received data:", data)  # Debug log
        
        branch = Branch.query.get_or_404(branch_id)
        # print("Found branch:", branch.id, branch.name)  # Debug log
        
        if 'branch_code' in data:
            branch.branch_code = data['branch_code']
        if 'name' in data and data['name']:  
            branch.name = data['name']
        if 'contact_phone' in data:
            branch.contact_phone = data['contact_phone']
        if 'notes' in data:
            branch.notes = data['notes']
        
        # print("Updated branch data:", {  # Debug log
        #     'id': branch.id,
        #     'name': branch.name,
        #     'branch_code': branch.branch_code,
        #     'contact_phone': branch.contact_phone
        # })
        
        db.session.commit()
        # print("Database committed successfully")  # Debug log
        
        return jsonify({
            'success': True,
            'message': 'อัพเดทข้อมูลสำเร็จ'
        })
        
    except Exception as e:
        print("Error occurred:", str(e))  # Debug log
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500

@app.route('/api/branches/devices/template', methods=['GET'])
def get_device_template():
    try:
        # สร้าง DataFrame ว่างพร้อมคอลัมน์
        df = pd.DataFrame(columns=[
            'รหัสสาขา',
            'ชื่อสาขา', 
            'ประเภทเครื่อง',
            'TeamViewer ID',
            'TeamViewer Password',
            'AnyDesk ID',
            'AnyDesk Password',
            'หมายเหตุ'
        ])
        
        # เพิ่มตัวอย่างข้อมูล 1 แถว
        df.loc[0] = [
            'B001',  # รหัสสาขา
            'สาขาตัวอย่าง',  # ชื่อสาขา
            'Cashier, Manager, Take Order, Server, Kioks, KDS',  # ประเภทเครื่อง
            '123456789',  # TeamViewer ID
            'password123',  # TeamViewer Password
            '987654321',  # AnyDesk ID
            'password321',  # AnyDesk Password
            'ตัวอย่างหมายเหตุ'  # หมายเหตุ
        ]
        
        # สร้าง Excel file ใน memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # เขียน DataFrame ลงใน Excel
            df.to_excel(writer, index=False, sheet_name='Template')
            
            # ปรับความกว้างคอลัมน์
            worksheet = writer.sheets['Template']
            worksheet.set_column('A:H', 20)
            
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
            download_name='device_import_template.xlsx'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/branches/devices/export/<int:customer_id>/export')
def export_branch_devices(customer_id):
    try:
        # Query devices data with customer_id filter
        query = """
            SELECT 
                b.branch_code as 'รหัสสาขา',
                b.name as 'ชื่อสาขา',
                d.machine_type as 'ประเภทเครื่อง',
                d.teamviewer_id as 'TeamViewer ID',
                d.teamviewer_pwd as 'TeamViewer Password',
                d.anydesk_id as 'AnyDesk ID',
                d.anydesk_pwd as 'AnyDesk Password',
                d.notes as 'หมายเหตุ'
            FROM branches b
            INNER JOIN Devices d ON d.branch_id = b.id
            WHERE b.isactive = 1 
            AND d.isactive = 1
            AND b.customer_id = :customer_id
            ORDER BY b.name
        """
        
        # สร้าง DataFrame จาก query result
        from sqlalchemy import text
        df = pd.read_sql(text(query), db.engine, params={'customer_id': customer_id})
        
        # ถ้าไม่มีข้อมูล ให้สร้าง empty DataFrame with columns
        if len(df) == 0:
            df = pd.DataFrame(columns=[
                'รหัสสาขา', 'ชื่อสาขา', 'ประเภทเครื่อง', 
                'TeamViewer ID', 'TeamViewer Password',
                'AnyDesk ID', 'AnyDesk Password', 'หมายเหตุ'
            ])
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write DataFrame to Excel
            df.to_excel(writer, index=False, sheet_name='Devices')
            
            # Adjust column widths
            worksheet = writer.sheets['Devices']
            worksheet.set_column('A:B', 20)  # Branch code and name
            worksheet.set_column('C:C', 15)  # Machine type
            worksheet.set_column('D:G', 25)  # TeamViewer and AnyDesk info
            worksheet.set_column('H:H', 30)  # Notes
            
            # Format headers
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#4B5563',
                'border': 1
            })
            
            # Apply header format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'customer_{customer_id}_devices.xlsx'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
        
@app.route('/api/branches/devices/import/<int:customer_id>', methods=['POST'])
def import_branch_devices(customer_id):
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'ไม่พบไฟล์ที่อัพโหลด'
            }), 400

        file = request.files['file']
        if not file.filename.endswith('.xlsx'):
            return jsonify({
                'success': False,
                'message': 'กรุณาอัพโหลดไฟล์ Excel (.xlsx) เท่านั้น'
            }), 400

        # ตรวจสอบว่า customer_id มีอยู่จริง
        customer = db.session.query(Customer).filter_by(
            id=customer_id,
            isactive=True
        ).first()
        
        if not customer:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลลูกค้า'
            }), 404

        # อ่านไฟล์ Excel
        df = pd.read_excel(file)
        
        # ตรวจสอบ columns ที่จำเป็น
        required_columns = [
            'รหัสสาขา',
            'ชื่อสาขา', 
            'ประเภทเครื่อง',
            'TeamViewer ID',
            'TeamViewer Password',
            'AnyDesk ID',
            'AnyDesk Password',
            'หมายเหตุ'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'success': False,
                'message': f'ไม่พบคอลัมน์ที่จำเป็น: {", ".join(missing_columns)}'
            }), 400

        # ตรวจสอบความถูกต้องของข้อมูล
        errors = []
        for idx, row in df.iterrows():
            row_num = idx + 2  # +2 เพราะ Excel เริ่มที่ 1 และมี header 1 แถว
            
            # ตรวจสอบรหัสสาขา
            if pd.isna(row['รหัสสาขา']) or str(row['รหัสสาขา']).strip() == '':
                errors.append(f'แถวที่ {row_num}: รหัสสาขาไม่สามารถเป็นค่าว่างได้')
                continue

            # ตรวจสอบชื่อสาขา
            if pd.isna(row['ชื่อสาขา']) or str(row['ชื่อสาขา']).strip() == '':
                errors.append(f'แถวที่ {row_num}: ชื่อสาขาไม่สามารถเป็นค่าว่างได้')
                continue

        if errors:
            return jsonify({
                'success': False,
                'message': 'พบข้อผิดพลาดในไฟล์',
                'errors': errors
            }), 400

        # อัพเดตข้อมูลในฐานข้อมูล
        success_count = 0
        new_branch_count = 0
        
        for _, row in df.iterrows():
            # ค้นหาสาขา
            branch = db.session.query(Branch).filter_by(
                branch_code=str(row['รหัสสาขา']).strip(),
                customer_id=customer_id,
                isactive=True
            ).first()
            
            # ถ้าไม่พบสาขา ให้สร้างใหม่
            if not branch:
                branch = Branch(
                    customer_id=customer_id,
                    branch_code=str(row['รหัสสาขา']).strip(),
                    name=str(row['ชื่อสาขา']).strip(),
                    isactive=True
                )
                db.session.add(branch)
                db.session.flush()  # เพื่อให้ได้ branch.id
                new_branch_count += 1
            
            # สร้าง Device ใหม่ทุกครั้ง
            device = Device(
                branch_id=branch.id,
                isactive=True
            )
            db.session.add(device)

            # อัพเดตข้อมูล Device โดยตัดช่องว่างออกจาก ID อัตโนมัติ
            device.machine_type = str(row['ประเภทเครื่อง']).strip() if pd.notna(row['ประเภทเครื่อง']) else None
            
            # ตัดช่องว่างออกจาก TeamViewer ID
            if pd.notna(row['TeamViewer ID']):
                device.teamviewer_id = str(row['TeamViewer ID']).replace(' ', '')
            else:
                device.teamviewer_id = None
                
            device.teamviewer_pwd = str(row['TeamViewer Password']).strip() if pd.notna(row['TeamViewer Password']) else None
            
            # ตัดช่องว่างออกจาก AnyDesk ID
            if pd.notna(row['AnyDesk ID']):
                device.anydesk_id = str(row['AnyDesk ID']).replace(' ', '')
            else:
                device.anydesk_id = None
                
            device.anydesk_pwd = str(row['AnyDesk Password']).strip() if pd.notna(row['AnyDesk Password']) else None
            device.notes = str(row['หมายเหตุ']).strip() if pd.notna(row['หมายเหตุ']) else None
            
            success_count += 1
        # Commit การเปลี่ยนแปลงทั้งหมด
        db.session.commit()

        message = f'นำเข้าข้อมูลสำเร็จ {success_count} รายการ'
        if new_branch_count > 0:
            message += f' (สร้างสาขาใหม่ {new_branch_count} สาขา)'

        return jsonify({
            'success': True,
            'message': message
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500                        
                                
@app.route('/summary/<int:customer_id>/<int:branch_id>')
def summary(customer_id, branch_id):
    try:
        customer = Customer.query.get_or_404(customer_id)
        branch = Branch.query.get_or_404(branch_id)
        
        # นับจำนวนอุปกรณ์ที่ active
        active_devices_count = Device.query.filter_by(
            branch_id=branch_id, 
            isactive=True
        ).count()
        
        # ดึงข้อมูล devices และจัดกลุ่มตาม machine_type
        devices = (Device.query
                  .filter_by(branch_id=branch_id, isactive=True)
                  .all())
        
        devices_by_type = {}
        for device in devices:
            if device.machine_type not in devices_by_type:
                devices_by_type[device.machine_type] = []
            devices_by_type[device.machine_type].append(device)
        
        return render_template('summary.html', 
                             customer=customer, 
                             branch=branch,
                             devices_by_type=devices_by_type,
                             active_devices_count=active_devices_count)
                             
    except Exception as e:
        print(f"Error in summary route: {str(e)}")
        return render_template('error.html', 
                             error_message="เกิดข้อผิดพลาดในการโหลดข้อมูล",
                             details=str(e)), 500

@app.route('/manage/spare')
def manage_spare():
    try:
        spares = db.session.query(
            SparePart,
            SpareType,
            SpareModel
        ).join(
            SpareType
        ).join(
            SpareModel
        ).filter(
            SparePart.isactive == 1  
        ).all()

        spare_types = SpareType.query.all()
        models = SpareModel.query.order_by(SpareModel.model_name).all()
        
        return render_template('spare/manage.html', 
                             spares=spares,
                             spare_types=spare_types,
                             models=models)
    except Exception as e:
        print(f"Error in manage_spare: {str(e)}")
        db.session.rollback()
        flash('เกิดข้อผิดพลาดในการดึงข้อมูล: ' + str(e), 'error')
        return redirect(url_for('index'))
            
@app.route('/manage/spare/add', methods=['POST'])
def add_spare():
    try:
        data = request.get_json()
        
        # เช็ค serial number ซ้ำเฉพาะที่ยัง active
        existing_spare = SparePart.query.filter(
            SparePart.serial_number == data['serial_number'],
            SparePart.isactive == 1
        ).first()
        
        if existing_spare:
            return jsonify({
                'status': 'error',
                'message': f'Serial number {data["serial_number"]} มีอยู่ในระบบแล้ว กรุณาตรวจสอบอีกครั้ง'
            }), 400

        # ถ้าไม่ซ้ำค่อยบันทึก
        spare = SparePart(
            spare_type_id=data['spare_type'],
            model_id=data['model_id'],
            serial_number=data['serial_number'],
            notes=data.get('notes', ''),
            isactive=1
        )
        
        db.session.add(spare)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'บันทึกข้อมูลสำเร็จ'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500
                            
@app.route('/manage/spare/edit/<int:id>', methods=['GET', 'POST'])
def edit_spare(id):
    spare = SparePart.query.get_or_404(id)
    if request.method == 'POST':
        try:
            spare.spare_type_id = request.form['spare_type']
            spare.model = request.form['model']
            spare.serial_number = request.form['serial_number']
            spare.notes = request.form['notes']
            db.session.commit()
            flash('Spare part updated successfully', 'success')
            return redirect(url_for('manage_spare'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            db.session.rollback()

    spare_types = SpareType.query.all()
    return render_template('spare/edit.html', spare=spare, spare_types=spare_types)

@app.route('/manage/spare/delete/<int:id>')
def delete_spare(id):
    spare = SparePart.query.get_or_404(id)
    try:
        spare.isactive = 0  # Soft delete
        db.session.commit()
        flash('ลบข้อมูลสำเร็จ', 'success')
    except Exception as e:
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
        db.session.rollback()
    return redirect(url_for('manage_spare'))

@app.route('/spare/repair')
def manage_repair():
    return render_template('spare/repair.html')

@app.route('/api/repair-stats')
def get_repair_stats():
    try:
        query = text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status_value = 'อยู่ระหว่างซ่อมแซม' AND isfinalize = 0 THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status_value = 'ส่งคืนเรียบร้อย' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status_value IN ('ไม่สามารถซ่อมได้', 'ไม่อนุมัติซ่อม') THEN 1 ELSE 0 END) as cancelled
            FROM repair_requests r
            LEFT JOIN (
                SELECT repair_id, status_value
                FROM status_history
                WHERE id IN (
                    SELECT MAX(id)
                    FROM status_history
                    WHERE status_type = 'repair'
                    GROUP BY repair_id
                )
            ) latest_status ON r.id = latest_status.repair_id
        """)
        
        result = db.session.execute(query).first()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': result.total or 0,
                'in_progress': result.in_progress or 0,
                'completed': result.completed or 0,
                'cancelled': result.cancelled or 0
            }
        })
    except Exception as e:
        print(f"Error getting repair stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/repair-search')
def search_repairs():
    try:
        search_type = request.args.get('type', '')
        query = request.args.get('query', '')

        sql_query = text("""
            SELECT DISTINCT
                r.model_name,
                r.serial_number,
                r.supplier_code,
                r.symptoms,
                r.receive_date,
                r.supplier_send_date,
                r.isfinalize,
                latest_status.status_value as current_status,
                d.FirstName,
                d.InsertDate
            FROM repair_requests r
            LEFT JOIN (
                SELECT repair_id, status_value
                FROM status_history
                WHERE id IN (
                    SELECT MAX(id)
                    FROM status_history
                    WHERE status_type = 'repair'
                    GROUP BY repair_id
                )
            ) latest_status ON r.id = latest_status.repair_id
            LEFT JOIN devices d ON r.model_name = d.itemcode
            WHERE 
                CASE 
                    WHEN :search_type = 'serial' THEN r.serial_number LIKE :search_query
                    WHEN :search_type = 'model' THEN r.model_name LIKE :search_query
                    WHEN :search_type = 'user' THEN d.FirstName LIKE :search_query
                    ELSE 1=1
                END
            ORDER BY r.created_at DESC
        """)
        
        search_param = f"%{query}%" if query else "%"
        results = db.session.execute(sql_query, {
            'search_type': search_type,
            'search_query': search_param
        }).fetchall()
        
        return jsonify({
            'success': True,
            'data': [{
                'model_name': row.model_name,
                'serial_number': row.serial_number,
                'supplier_code': row.supplier_code,
                'symptoms': row.symptoms,
                'receive_date': row.receive_date.isoformat() if row.receive_date else None,
                'supplier_send_date': row.supplier_send_date.isoformat() if row.supplier_send_date else None,
                'isfinalize': row.isfinalize,
                'current_status': row.current_status,
                'user_name': row.FirstName,
                'purchase_date': row.InsertDate.isoformat() if row.InsertDate else None
            } for row in results]
        })
    except Exception as e:
        print(f"Error searching repairs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

            
if __name__ == '__main__':
    print('\n=================================')
    print('Server is running at: http://127.0.0.1:5000')
    print('=================================\n')
    app.run(host='127.0.0.1', port=5000, debug=True)
    
