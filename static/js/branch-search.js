/**
 * branch-search.js
 * ฟังก์ชันค้นหาสาขาแบบเรียลไทม์
 */

document.addEventListener('DOMContentLoaded', function() {
    initBranchSearch();
});

/**
 * เริ่มต้นการทำงานของฟังก์ชันค้นหาสาขา
 */
function initBranchSearch() {
    // ค้นหาช่อง input ที่มีอยู่แล้ว
    const searchInput = document.getElementById('branchSearch');
    
    if (searchInput) {
        // เพิ่ม Event Listener สำหรับการค้นหา
        searchInput.addEventListener('input', searchBranches);
        console.log('Branch search initialized on existing search field');
    } else {
        console.warn('Search input field not found, real-time search not available');
    }
}

/**
 * ฟังก์ชันค้นหาสาขาแบบเรียลไทม์
 */
function searchBranches() {
    const searchQuery = document.getElementById('branchSearch').value.toLowerCase().trim();
    const rows = document.querySelectorAll('tbody tr');
    
    let foundCount = 0;
    
    rows.forEach(row => {
        // ข้ามแถวที่เป็น message ข้อความเมื่อไม่พบข้อมูล
        if (row.id === 'noResultsMessage') return;
        
        // ค้นหาจากรหัสสาขา ชื่อสาขา เบอร์โทร และหมายเหตุ
        const branchCode = row.querySelector('td[data-branch-code]')?.textContent.toLowerCase() || '';
        const branchName = row.querySelector('td[data-name]')?.textContent.toLowerCase() || '';
        const contactPhone = row.querySelector('td[data-contact-phone]')?.textContent.toLowerCase() || '';
        const notes = row.querySelector('td[data-notes]')?.textContent.toLowerCase() || '';
        
        const isMatch = 
            branchCode.includes(searchQuery) || 
            branchName.includes(searchQuery) || 
            contactPhone.includes(searchQuery) || 
            notes.includes(searchQuery);
        
        if (isMatch) {
            row.style.display = '';
            foundCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // แสดงข้อความเมื่อไม่พบผลลัพธ์
    let noResultsMsg = document.getElementById('noResultsMessage');
    
    if (foundCount === 0 && searchQuery !== '') {
        if (!noResultsMsg) {
            noResultsMsg = document.createElement('tr');
            noResultsMsg.id = 'noResultsMessage';
            noResultsMsg.innerHTML = `
                <td colspan="7" class="px-4 py-8 text-center text-gray-500">
                    <div class="flex flex-col items-center">
                        <svg class="w-12 h-12 mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p class="text-lg font-medium">ไม่พบสาขาที่ค้นหา</p>
                        <p class="text-sm">ลองใช้คำค้นหาอื่น หรือตรวจสอบการสะกดอีกครั้ง</p>
                    </div>
                </td>
            `;
            document.querySelector('tbody').appendChild(noResultsMsg);
        }
    } else if (noResultsMsg) {
        noResultsMsg.remove();
    }
}

/**
 * ฟังก์ชันล้างการค้นหา
 */
function clearBranchSearch() {
    const searchInput = document.getElementById('branchSearch');
    if (searchInput) {
        searchInput.value = '';
        searchBranches();
    }
}

// ส่งออกฟังก์ชันสำหรับใช้งานนอกไฟล์
window.branchSearch = {
    init: initBranchSearch,
    search: searchBranches,
    clear: clearBranchSearch
};