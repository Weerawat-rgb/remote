/**
 * branch-core.js
 * ฟังก์ชันหลักสำหรับการจัดการสาขา
 */

// ======== BRANCH OPERATIONS ========

/**
 * เปิด modal แก้ไขข้อมูลสาขา
 */
async function openEditBranchModal(branchId) {
    try {
        // หา row ของสาขาที่ต้องการแก้ไข
        const tr = document.querySelector(`tr[data-branch-id="${branchId}"]`);
        if (!tr) throw new Error('ไม่พบข้อมูลสาขา');

        // ดึงข้อมูลจาก cells แทนการใช้ data attributes
        const name = tr.querySelector('td[data-name]')?.textContent.trim();
        const contactPhone = tr.querySelector('td[data-contact-phone]')?.textContent.trim();
        const branchCode = tr.querySelector('td[data-branch-code]')?.textContent.trim();
        const notes = tr.querySelector('td[data-notes]')?.textContent.trim();

        // ตรวจสอบและกำหนดค่าให้กับ form fields
        const elements = {
            'edit_branch_id': branchId,
            'edit_branch_name': name || '',
            'edit_contact_phone': contactPhone || '',
            'edit_branch_code': branchCode || '',
            'edit_notes': notes || ''
        };

        // กำหนดค่าให้แต่ละ field
        for (const [id, value] of Object.entries(elements)) {
            const element = document.getElementById(id);
            if (element) {
                element.value = value;
            }
        }

        // แสดง modal
        const modal = document.getElementById('editBranchModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }

    } catch (error) {
        console.error('Error:', error);
        alert('เกิดข้อผิดพลาดในการดึงข้อมูล: ' + error.message);
    }
}

/**
 * ปิด modal แก้ไขข้อมูลสาขา
 */
function closeEditBranchModal() {
    const modal = document.getElementById('editBranchModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
}

/**
 * บันทึกการแก้ไขข้อมูลสาขา
 */
async function updateBranch(event) {
    event.preventDefault();
    console.log('Updating branch...'); // Debug log

    const branchId = document.getElementById('edit_branch_id').value;
    const formData = {
        branch_code: document.getElementById('edit_branch_code').value,
        name: document.getElementById('edit_branch_name').value,
        contact_phone: document.getElementById('edit_contact_phone').value,
        notes: document.getElementById('edit_notes').value,
        isactive: true
    };

    console.log('Form data:', formData); // Debug log

    try {
        const response = await fetch(`/api/branches/${branchId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        console.log('Response status:', response.status); // Debug log

        const result = await response.json();
        console.log('Response data:', result); // Debug log

        if (result.success) {
            closeEditBranchModal();
            location.reload();
        } else {
            alert(result.message || 'เกิดข้อผิดพลาด กรุณาลองใหม่');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('เกิดข้อผิดพลาด กรุณาลองใหม่');
    }
}

/**
 * เปิด modal เพิ่มสาขาใหม่
 */
function openAddBranchModal() {
    const modal = document.getElementById('addBranchModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

/**
 * ปิด modal เพิ่มสาขา
 */
function closeAddBranchModal() {
    const modal = document.getElementById('addBranchModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    // เคลียร์ form
    document.getElementById('addBranchForm').reset();
}

/**
 * เพิ่มสาขาใหม่
 */
async function addBranch() {
    try {
        const formFields = {
            'branch_name': 'name',
            'contact_phone': 'contact_phone',
            'customer_id': 'customer_id',
            'branch_code': 'branch_code',
            'branch_notes': 'notes'
        };

        const formData = {};
        for (const [elementId, fieldName] of Object.entries(formFields)) {
            const element = document.getElementById(elementId);
            if (!element) {
                console.error(`ไม่พบ element: ${elementId}`);
                alert(`เกิดข้อผิดพลาดระบบ: ไม่พบฟิลด์ ${fieldName}`);
                return;
            }
            formData[fieldName] = element.value.trim();
        }

        const response = await fetch('/api/branches/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            alert('เพิ่มสาขาเรียบร้อยแล้ว');
            closeAddBranchModal();
            window.location.reload();
        } else {
            throw new Error(data.message || 'ไม่สามารถบันทึกข้อมูลได้');
        }
    } catch (error) {
        console.error('Error:', error);
        alert(`เกิดข้อผิดพลาด: ${error.message}`);
    }
}

/**
 * ลบสาขา
 */
function deleteBranch(branchId) {
    if (confirm('คุณแน่ใจที่จะลบสาขานี้หรือไม่?')) {
        console.log('Deleting branch:', branchId); // Debug log

        fetch(`/api/branches/${branchId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
            .then(response => response.json())
            .then(data => {
                console.log('Response:', data); // Debug log
                if (data.success) {
                    alert('ลบสาขาเรียบร้อยแล้ว');
                    location.reload();
                } else {
                    alert('เกิดข้อผิดพลาด: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('เกิดข้อผิดพลาดในการลบสาขา');
            });
    }
}

/**
 * ส่งออกข้อมูลสาขาและอุปกรณ์
 */
function exportBranches() {
    const customerId = document.getElementById('customer_id')?.value || document.querySelector('input[name="customer_id"]')?.value;
    window.location.href = `/api/branches/devices/export/${customerId}/export`;
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // เพิ่ม event listener สำหรับฟอร์มเพิ่มสาขา
    const addBranchForm = document.getElementById('addBranchForm');
    if (addBranchForm) {
        addBranchForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            try {
                const formData = new FormData(event.target);
                const data = {};
                formData.forEach((value, key) => {
                    data[key] = value;
                });
    
                const response = await fetch('/api/branches/add', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
    
                const result = await response.json();
    
                if (result.success) {
                    closeAddBranchModal();
                    alert('บันทึกข้อมูลสำเร็จ');
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                } else {
                    throw new Error(result.message || 'ไม่สามารถบันทึกข้อมูลได้');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('เกิดข้อผิดพลาดในการเพิ่มสาขา: ' + error.message);
            }
        });
    }
});