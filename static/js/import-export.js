/**
 * import-export.js
 * ฟังก์ชันจัดการการนำเข้า/ส่งออกข้อมูล
 */

/**
 * เรียกใช้งานปุ่มเลือกไฟล์
 */
function triggerFileInput() {
    document.getElementById('fileInput').click();
}

/**
 * นำเข้าข้อมูลจากไฟล์ Excel
 */
async function importBranches(event) {
    const customerId = document.getElementById('customer_id')?.value 
                      || document.querySelector('input[name="customer_id"]')?.value;
    const fileInput = document.getElementById('fileInput');

    try {
        if (!fileInput.files || fileInput.files.length === 0) {
            showToast('กรุณาเลือกไฟล์', 'error');
            return;
        }

        // แสดง loading toast
        showToast('กำลังนำเข้าข้อมูล...', 'info');

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        const response = await fetch(`/api/branches/devices/import/${customerId}`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            if (result.errors) {
                showToast('พบข้อผิดพลาด', 'error');
                alert('พบข้อผิดพลาด:\n\n' + result.errors.join('\n'));
            } else {
                showToast(result.message || 'เกิดข้อผิดพลาดในการนำเข้าข้อมูล', 'error');
            }
            return;
        }

        // แสดง success toast
        showToast(result.message, 'success');

        // รีเฟรชหน้าเว็บหลังจาก toast แสดงเสร็จ
        setTimeout(() => window.location.reload(), 3500);

    } catch (error) {
        console.error('Import failed:', error);
        showToast('เกิดข้อผิดพลาดในการนำเข้าข้อมูล', 'error');
    } finally {
        fileInput.value = '';
    }
}

/**
 * ดาวน์โหลด template สำหรับนำเข้าข้อมูล
 */
async function downloadTemplate() {
    try {
        const response = await fetch('/api/branches/devices/template');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // รับ blob จาก response
        const blob = await response.blob();

        // สร้าง URL สำหรับ blob
        const url = window.URL.createObjectURL(blob);

        // สร้าง element a เพื่อดาวน์โหลด
        const a = document.createElement('a');
        a.href = url;
        a.download = 'device_import_template.xlsx';
        document.body.appendChild(a);
        a.click();

        // cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

    } catch (error) {
        console.error('Download failed:', error);
        alert('เกิดข้อผิดพลาดในการดาวน์โหลด Template');
    }
}

/**
 * ส่งออกข้อมูลสาขาและอุปกรณ์
 */
function exportBranches() {
    const customerId = document.getElementById('customer_id')?.value 
                      || document.querySelector('input[name="customer_id"]')?.value;
    
    if (!customerId) {
        alert('ไม่พบรหัสลูกค้า');
        return;
    }
    
    window.location.href = `/api/branches/devices/export/${customerId}/export`;
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // เพิ่ม event listener สำหรับ file input
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', importBranches);
    }
});