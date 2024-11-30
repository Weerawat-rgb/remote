import io
from flask import Flask, jsonify, make_response, render_template, request, redirect, send_file, url_for, flash
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import or_
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = '5e3d17fba71924d29490882d7bfb694f23c1a2ae720c2878'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://sa:admin123@nart:1433/RemoteAccessDB?driver=ODBC+Driver+17+for+SQL+Server&charset=utf8'
app.config['JSON_AS_ASCII'] = False

# เพิ่มการตั้งค่านี้
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


db = SQLAlchemy(app)
migrate = Migrate(app, db) 

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

class Branch(db.Model):
    __tablename__ = 'Branches'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    branch_code = db.Column(db.String(100))
    address = db.Column(db.String(200))
    contact_name = db.Column(db.String(100))
    teamviewer_id = db.Column(db.String(20))
    teamviewer_pwd = db.Column(db.String(20))
    anydesk_id = db.Column(db.String(20))
    anydesk_pwd = db.Column(db.String(20))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))
    devices = db.relationship('Device', backref='branch', lazy=True)
    isactive = db.Column(db.Boolean, nullable=True, default=True)

class Device(db.Model):
    __tablename__ = 'Devices'
    
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('Branches.id'), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)
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
        customers = Customer.query.all()
        # ทดสอบ print ค่า
        for customer in customers:
            print(f"Customer name: {customer.hq_contact_name}")
        return render_template('index.html', customers=customers)
    except Exception as e:
        print(f"Error: {str(e)}")
        return str(e)
    
@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    results = Customer.query.filter(
        or_(
            Customer.name.ilike(f'%{query}%'),
            Customer.hq_contact_name.ilike(f'%{query}%'),
            Customer.hq_contact_email.ilike(f'%{query}%'),
            Customer.hq_contact_phone.ilike(f'%{query}%'),
            Customer.hq_address.ilike(f'%{query}%')
        )
    ).limit(5).all()
    
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'hq_contact_name': c.hq_contact_name,
        'hq_contact_phone': c.hq_contact_phone
    } for c in results])
    
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
        
            # เช็คจำนวนสาขา
        if len(customer.branches) > 0:
            return jsonify({
                'success': False, 
                'message': f'ไม่สามารถลบลูกค้าได้เนื่องจากมีข้อมูลสาขาจำนวน {len(customer.branches)} สาขา รบกวนลบข้อมูลสาขาทั้งหมดก่อนที่จะลบลูกค้ารายนี้ครับ'
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
        data = request.get_json(force=True)  # เพิ่ม force=True
        new_branch = Branch(
            customer_id=data['customer_id'],
            name=data['name'],
            contact_name=data['contact_name'],
            contact_phone=data['contact_phone']
        )
        
        db.session.add(new_branch)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'เพิ่มสาขาเรียบร้อยแล้ว'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
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
        
@app.route('/branch/<int:branch_id>/device/add', methods=['GET', 'POST'])
def add_device(branch_id):
    if request.method == 'POST':
        device = Device(
            branch_id=branch_id,
            device_type=request.form['device_type'],
            teamviewer_id=request.form['teamviewer_id'],
            teamviewer_password=request.form['teamviewer_password'],
            anydesk_id=request.form['anydesk_id'],
            anydesk_password=request.form['anydesk_password'],
            notes=request.form['notes']
        )
        db.session.add(device)
        db.session.commit()
        flash('Device added successfully')
        return redirect(url_for('view_branch', branch_id=branch_id))
    return render_template('add_device.html', branch_id=branch_id)

@app.route('/customer/<int:customer_id>')
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template('view_customer.html', customer=customer)

@app.route('/customers/<int:customer_id>/branches')
def view_branches(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    branches = Branch.query.filter_by(customer_id=customer_id).all()
    return render_template('view_branch.html', customer=customer, branches=branches)

@app.route('/api/branches/<int:branch_id>', methods=['GET'])
def get_branch(branch_id):
    branch = Branch.query.get_or_404(branch_id)
    return jsonify({
        'id': branch.id,
        'name': branch.name,
        'contact_name': branch.contact_name,
        'contact_phone': branch.contact_phone,
        'address': branch.address
    })
    
@app.route('/api/branches/<int:branch_id>', methods=['PUT'])
def edit_branch(branch_id):
    try:
        branch = Branch.query.get_or_404(branch_id)
        data = request.json

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


if __name__ == '__main__':
    app.run(debug=True)