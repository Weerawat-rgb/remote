/**
 * device-operations.js
 * ฟังก์ชันจัดการอุปกรณ์และการรีโมท
 */

// ======== REMOTE/DEVICE OPERATIONS ========

/**
 * เปิด modal ข้อมูลรีโมท
 */
function openRemoteModal(branchId) {
    console.log('Opening remote modal for branch:', branchId);
    document.getElementById('remote_branch_id').value = branchId;

    // เคลียร์ค่าทุกฟิลด์ให้ว่าง
    const machineTypeSelect = document.getElementById('remote_machine_type');
    machineTypeSelect.value = machineTypeSelect.options[0].value;
    document.getElementById('remote_teamviewer_id').value = '';
    document.getElementById('remote_teamviewer_pwd').value = '';
    document.getElementById('remote_anydesk_id').value = '';
    document.getElementById('remote_anydesk_pwd').value = '';
    document.getElementById('remote_notes').value = '';

    // เปลี่ยนค่า flag เป็นเพิ่มใหม่
    document.getElementById('is_editing').value = 'false';

    // แสดง Modal
    const modal = document.getElementById('remoteModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

/**
 * ปิด modal ข้อมูลรีโมท
 */
function closeRemoteModal() {
    const modal = document.getElementById('remoteModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

/**
 * บันทึกข้อมูลรีโมท (device)
 */
function saveRemote() {
    const branchId = document.getElementById('remote_branch_id').value;
    const isEditing = document.getElementById('is_editing').value === 'true';
    const editMachineType = document.getElementById('edit_machine_type').value;

    const data = {
        branch_id: parseInt(branchId),
        machine_type: document.getElementById('remote_machine_type').value,
        teamviewer_id: document.getElementById('remote_teamviewer_id').value,
        teamviewer_pwd: document.getElementById('remote_teamviewer_pwd').value,
        anydesk_id: document.getElementById('remote_anydesk_id').value,
        anydesk_pwd: document.getElementById('remote_anydesk_pwd').value,
        notes: document.getElementById('remote_notes').value
    };

    // เลือกใช้ POST สำหรับเพิ่มใหม่ หรือ PUT สำหรับแก้ไข
    const url = isEditing ?
        `/api/branches/${branchId}/devices/${editMachineType}` :
        '/api/devices';

    const method = isEditing ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                closeRemoteModal();
                location.reload();
            } else {
                alert(data.message || 'เกิดข้อผิดพลาดในการบันทึกข้อมูล');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('เกิดข้อผิดพลาดในการบันทึกข้อมูล');
        });
}

/**
 * แสดงรายละเอียดอุปกรณ์
 */
function showDeviceDetail(branchId, machineType) {
    fetch(`/api/branches/${branchId}/devices/${machineType}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.device) {
                let detailContent = `
            <div class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
                <div class="bg-white rounded-xl max-w-2xl w-full mx-4 shadow-2xl">
                    <!-- Header -->
                    <div class="flex justify-between items-center p-6 border-b bg-gradient-to-r from-indigo-600 to-indigo-500 rounded-t-xl">
                        <h3 class="text-xl font-semibold text-white">รายละเอียดเครื่อง ${machineType}</h3>
                        <button onclick="this.closest('div.fixed').remove()" 
                                class="text-white/70 hover:text-white transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    <!-- Content -->
                    <div class="p-6 space-y-6">
                        <!-- Teamviewer Section -->
                        <div class="bg-gray-50 rounded-lg p-4">
                            <h4 class="text-lg font-semibold text-indigo-600 mb-4">Teamviewer</h4>
                            <div class="space-y-3">
                                <div class="flex items-center justify-between bg-white rounded-lg p-3 shadow-sm">
                                    <p class="text-gray-700">
                                        <span class="text-gray-500 font-medium">ID:</span> 
                                        <span class="ml-2">${data.device.teamviewer_id || '-'}</span>
                                    </p>
                                    <button onclick="copyToClipboard('${data.device.teamviewer_id}')" 
                                            class="text-indigo-600 hover:text-indigo-800 p-1 rounded hover:bg-indigo-50 transition-colors">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                                    d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                                        </svg>
                                    </button>
                                </div>
                                
                                <div class="flex items-center justify-between bg-white rounded-lg p-3 shadow-sm">
                                    <p class="text-gray-700">
                                        <span class="text-gray-500 font-medium">Password:</span>
                                        <span class="ml-2">${data.device.teamviewer_pwd || '-'}</span>
                                    </p>
                                    <button onclick="copyToClipboard('${data.device.teamviewer_pwd}')"
                                            class="text-indigo-600 hover:text-indigo-800 p-1 rounded hover:bg-indigo-50 transition-colors">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                                    d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- Anydesk Section -->
                        <div class="bg-gray-50 rounded-lg p-4">
                            <h4 class="text-lg font-semibold text-indigo-600 mb-4">Anydesk</h4>
                            <div class="space-y-3">
                                <div class="flex items-center justify-between bg-white rounded-lg p-3 shadow-sm">
                                    <p class="text-gray-700">
                                        <span class="text-gray-500 font-medium">ID:</span>
                                        <span class="ml-2">${data.device.anydesk_id || '-'}</span>
                                    </p>
                                    <button onclick="copyToClipboard('${data.device.anydesk_id}')"
                                            class="text-indigo-600 hover:text-indigo-800 p-1 rounded hover:bg-indigo-50 transition-colors">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                                    d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                                        </svg>
                                    </button>
                                </div>
                                
                                <div class="flex items-center justify-between bg-white rounded-lg p-3 shadow-sm">
                                    <p class="text-gray-700">
                                        <span class="text-gray-500 font-medium">Password:</span>
                                        <span class="ml-2">${data.device.anydesk_pwd || '-'}</span>
                                    </p>
                                    <button onclick="copyToClipboard('${data.device.anydesk_pwd}')"
                                            class="text-indigo-600 hover:text-indigo-800 p-1 rounded hover:bg-indigo-50 transition-colors">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                                    d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div class="bg-gray-50 rounded-lg p-4">
                            <p class="text-gray-700">
                                <span class="text-gray-500 font-medium">Remark:</span>
                                <span class="ml-2">${data.device.notes || '-'}</span>
                            </p>
                        </div>

                        <!-- Action Buttons -->
                        <div class="mt-8 pt-4 border-t flex justify-end space-x-3">
                            <button onclick="this.closest('div.fixed').remove(); editDevice('${branchId}', '${machineType}')"
                                    class="flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors">
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                                แก้ไข
                            </button>
                            
                            <button onclick="if(confirm('คุณต้องการลบข้อมูลเครื่องนี้ใช่หรือไม่?')) deleteDevice('${branchId}', '${machineType}')"
                                    class="flex items-center px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors">
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                                ลบ
                            </button>
                        </div>
                    </div>
                </div>
                </div>
               `;
                document.body.insertAdjacentHTML('beforeend', detailContent);
            } else {
                alert(data.message || 'ไม่พบข้อมูลเครื่อง');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('เกิดข้อผิดพลาดในการโหลดข้อมูล');
        });
}

/**
 * แก้ไขข้อมูลอุปกรณ์
 */
function editDevice(branchId, machineType) {
    fetch(`/api/branches/${branchId}/devices/${machineType}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // เติมข้อมูลในฟอร์มแก้ไข
                document.getElementById('remote_branch_id').value = branchId;
                document.getElementById('remote_machine_type').value = machineType;
                document.getElementById('remote_teamviewer_id').value = data.device.teamviewer_id || '';
                document.getElementById('remote_teamviewer_pwd').value = data.device.teamviewer_pwd || '';
                document.getElementById('remote_anydesk_id').value = data.device.anydesk_id || '';
                document.getElementById('remote_anydesk_pwd').value = data.device.anydesk_pwd || '';
                document.getElementById('remote_notes').value = data.device.notes || '';

                // เพิ่ม flag เพื่อบอกว่ากำลังแก้ไข
                document.getElementById('is_editing').value = 'true';
                document.getElementById('edit_machine_type').value = machineType;

                // เปิด Modal แก้ไข
                const remoteModal = document.getElementById('remoteModal');
                remoteModal.classList.remove('hidden');
                remoteModal.classList.add('flex');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('เกิดข้อผิดพลาดในการโหลดข้อมูล');
        });
}

/**
 * ลบอุปกรณ์
 */
function deleteDevice(branchId, machineType) {
    fetch(`/api/branches/${branchId}/devices/${machineType}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('ลบข้อมูลเครื่องเรียบร้อยแล้ว');
                location.reload();
            } else {
                alert(data.message || 'เกิดข้อผิดพลาดในการลบข้อมูล');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('เกิดข้อผิดพลาดในการลบข้อมูล');
        });
}