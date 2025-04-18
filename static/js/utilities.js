/**
 * utilities.js
 * ฟังก์ชันสนับสนุนและ utilites ต่างๆ
 */

/**
 * คัดลอกข้อความไปยังคลิปบอร์ด
 * @param {string} text - ข้อความที่ต้องการคัดลอก
 */
function copyToClipboard(text) {
    if (text && text !== '-') {
        // วิธีที่ 1: ใช้ Clipboard API (modern browsers)
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('คัดลอกข้อมูลแล้ว', 'success');
            }).catch(err => {
                console.error('Failed to copy: ', err);
                showToast('ไม่สามารถคัดลอกข้อมูลได้', 'error');
            });
        }
        // วิธีที่ 2: วิธีดั้งเดิมใช้ textarea
        else {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.left = '-999999px';
            textarea.style.top = '-999999px';
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();

            try {
                document.execCommand('copy');
                textarea.remove();
                showToast('คัดลอกข้อมูลแล้ว', 'success');
            } catch (err) {
                console.error('Failed to copy: ', err);
                textarea.remove();
                showToast('ไม่สามารถคัดลอกข้อมูลได้', 'error');
            }
        }
    }
}

/**
 * แสดง Toast Notification แบบพื้นฐาน
 * @param {string} message - ข้อความที่ต้องการแสดง
 * @param {string} type - ประเภทข้อความ ('success', 'error', 'info')
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg text-white text-sm font-medium shadow-lg transform transition-all duration-300 ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        'bg-blue-500'
    }`;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => document.body.removeChild(toast), 300);
    }, 2000);
}

/**
 * แสดง Toast Notification แบบมี Container (สำหรับหลาย toast พร้อมกัน)
 * @param {string} message - ข้อความที่ต้องการแสดง
 * @param {string} type - ประเภทข้อความ ('success', 'error', 'info')
 */
function showContainerToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return showToast(message, type);

    const toast = document.createElement('div');
    toast.className = `rounded-md px-6 py-4 text-sm font-medium text-white shadow-lg transform transition-all duration-300 ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        type === 'info' ? 'bg-blue-500' : 'bg-gray-500'
    }`;

    // สร้าง flex container สำหรับ icon และ message
    const content = document.createElement('div');
    content.className = 'flex items-center';

    // เพิ่ม loading spinner ถ้าเป็น info toast
    if (type === 'info') {
        const spinner = document.createElement('div');
        spinner.className = 'animate-spin mr-2 h-4 w-4 text-white';
        spinner.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
    `;
        content.appendChild(spinner);
    }

    const text = document.createElement('span');
    text.textContent = message;
    content.appendChild(text);

    toast.appendChild(content);
    container.appendChild(toast);

    // Animation
    setTimeout(() => toast.style.opacity = '0', 3000);
    setTimeout(() => container.removeChild(toast), 3500);
}

/**
 * แสดง Toast Notification แบบ SweetAlert2 (ถ้ามี)
 * @param {string} icon - ไอคอนที่ต้องการแสดง
 * @param {string} text - ข้อความที่ต้องการแสดง
 */
function showSweetAlert2Toast(icon, text) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            toast: true,
            icon: icon,
            title: text,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
    } else {
        showToast(text, icon === 'success' ? 'success' : icon === 'error' ? 'error' : 'info');
    }
}