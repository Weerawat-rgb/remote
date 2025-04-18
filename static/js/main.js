/**
 * main.js
 * ไฟล์หลักสำหรับเชื่อมต่อกับทุกไฟล์ JavaScript และเริ่มต้นการทำงาน
 */

// ทำงานเมื่อโหลดหน้าเสร็จ
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
    
    // เพิ่ม event listener สำหรับ file input นำเข้าข้อมูล
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', importBranches);
    }
});