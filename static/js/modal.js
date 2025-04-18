// Modal functions for customer management

// Close modals
function closeEditModal() {
    document.getElementById('editCustomerModal').classList.add('hidden');
    document.getElementById('editCustomerModal').classList.remove('flex');
}

function closeModal() {
    document.getElementById('modal').classList.add('hidden');
    document.getElementById('modal-backdrop').classList.add('hidden');
    document.body.style.overflow = 'auto';
}

// Open modals
function openAddCustomerModal() {
    document.getElementById('modal').classList.remove('hidden');
    document.getElementById('modal-backdrop').classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function openEditModal(customerId) {
    console.log('Opening edit modal for customer ID:', customerId);
    
    // แสดง loading indicator (ถ้ามี)
    const modal = document.getElementById('editCustomerModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    
    // ดึงข้อมูลลูกค้า
    fetch(`/api/customers/${customerId}`)
        .then(response => response.json())
        .then(customer => {
            console.log('Customer data:', customer);
            
            // กำหนดค่าพื้นฐาน
            document.getElementById('customerId').value = customer.id;
            document.getElementById('customerName').value = customer.name || '';
            
            // กำหนดค่า notes
            const notesField = document.getElementById('notes');
            if (notesField) {
                notesField.value = customer.notes || '';
            }
            
            // กำหนดค่า website_url (สำคัญ!)
            const websiteUrlField = document.getElementById('website_url');
            if (websiteUrlField) {
                console.log('Setting website_url to:', customer.website_url);
                websiteUrlField.value = customer.website_url || '';
                // ตรวจสอบค่าหลังจากกำหนด
                setTimeout(() => {
                    console.log('website_url after set:', websiteUrlField.value);
                }, 100);
            }
            
            // แสดงโลโก้
            const logoImg = document.getElementById('currentLogo');
            if (logoImg) {
                if (customer.has_logo) {
                    logoImg.src = `/api/customers/${customerId}/logo?t=${new Date().getTime()}`;
                    logoImg.style.display = 'block';
                } else {
                    logoImg.src = '';
                    logoImg.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('Error loading customer data:', error);
            alert('เกิดข้อผิดพลาดในการโหลดข้อมูลลูกค้า');
        });
}

// Delete customer functions
function confirmDelete() {
    document.getElementById('deleteConfirmDialog').classList.remove('hidden');
}

function cancelDelete() {
    document.getElementById('deleteConfirmDialog').classList.add('hidden');
}

function deactivateCustomer() {
    const customerId = document.getElementById('customerId').value;

    fetch(`/api/customers/${customerId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json().then(data => ({
            ok: response.ok,
            status: response.status,
            data: data
        })))
        .then(({ ok, status, data }) => {
            if (!ok) {
                throw new Error(data.message || `Server returned ${status}`);
            }

            // ถ้าสำเร็จ
            document.getElementById('deleteConfirmDialog').classList.add('hidden');
            closeEditModal();
            location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function () {
    // Close modal when pressing ESC key
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            closeModal();
            closeEditModal();
        }
    });

    // Logo preview for add form
    const logoInput = document.getElementById('logo');
    if (logoInput) {
        logoInput.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                // Check file size (2MB limit)
                if (file.size > 2 * 1024 * 1024) {
                    alert('ขนาดไฟล์ต้องไม่เกิน 2MB');
                    this.value = '';
                    return;
                }

                const preview = document.getElementById('preview');
                const logoPreview = document.getElementById('logoPreview');
                const reader = new FileReader();

                reader.onload = function (e) {
                    logoPreview.src = e.target.result;
                    preview.classList.remove('hidden');
                };

                reader.readAsDataURL(file);
            }
        });
    }

    // Logo preview for edit form
    const editLogoInput = document.getElementById('logoInput');
    if (editLogoInput) {
        editLogoInput.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                if (file.size > 2 * 1024 * 1024) { // 2MB limit
                    alert('ขนาดไฟล์ต้องไม่เกิน 2MB');
                    this.value = '';
                    return;
                }

                const reader = new FileReader();
                reader.onload = function (e) {
                    document.getElementById('currentLogo').src = e.target.result;
                    document.getElementById('currentLogo').style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    document.getElementById('editCustomerForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const formData = new FormData(this);

        // แสดงข้อมูลทั้งหมดที่จะส่ง
        console.log('Form data to submit:');
        for (let [key, value] of formData.entries()) {
            console.log(`${key}: ${value}`);
        }

        const customerId = formData.get('customer_id');
        if (!customerId) {
            alert('ไม่พบรหัสลูกค้า');
            return;
        }

        // ส่งข้อมูลไปยัง API
        fetch(`/api/customers/${customerId}`, {
            method: 'PUT',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('บันทึกข้อมูลสำเร็จ');
                    closeEditModal();
                    window.location.reload();
                } else {
                    alert(data.message || 'เกิดข้อผิดพลาดในการบันทึกข้อมูล');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('เกิดข้อผิดพลาดในการบันทึกข้อมูล');
            });
    });

    // Add customer form submission
    const addForm = document.querySelector('form[action*="add_customer"]');
    if (addForm) {
        addForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);

            try {
                const response = await fetch(addForm.action, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    alert(data.message || 'เพิ่มข้อมูลลูกค้าสำเร็จ');
                    closeModal();
                    window.location.reload();
                } else {
                    alert('เกิดข้อผิดพลาด: ' + (data.message || 'ไม่สามารถเพิ่มข้อมูลลูกค้าได้'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('เกิดข้อผิดพลาดในการส่งข้อมูล');
            }
        });
    }
});