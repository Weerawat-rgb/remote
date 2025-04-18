// Add this JavaScript to enable real-time search
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('customerSearch');
    const customersContainer = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-2.gap-6');
    
    // ตรวจสอบว่ามี elements ที่จำเป็นหรือไม่
    if (!searchInput || !customersContainer) {
        console.error('Required elements for search not found');
        return;
    }
    
    const customerCards = Array.from(customersContainer.querySelectorAll('.bg-white.p-6.rounded-lg.shadow'));
    const noResultsMessage = document.createElement('p');
    noResultsMessage.className = 'text-gray-500 col-span-2';
    noResultsMessage.textContent = 'ไม่พบลูกค้าที่ค้นหา';
    
    // Store original cards for reset
    const originalCustomerCards = [...customerCards];
    
    // Disable form submission since we're handling search in real-time
    const searchForm = document.getElementById('customerSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
        });
    }
    
    // Add event listener for real-time search
    searchInput.addEventListener('input', function() {
        const searchQuery = this.value.toLowerCase().trim();
        
        // Clear the container
        customersContainer.innerHTML = '';
        
        if (searchQuery === '') {
            // If search is empty, restore all cards
            originalCustomerCards.forEach(card => {
                customersContainer.appendChild(card);
            });
            return;
        }
        
        // Filter cards based on search query
        const filteredCards = originalCustomerCards.filter(card => {
            const customerName = card.querySelector('h2').textContent.toLowerCase().trim();
            return customerName.includes(searchQuery);
        });
        
        // Display filtered results or no results message
        if (filteredCards.length > 0) {
            filteredCards.forEach(card => {
                customersContainer.appendChild(card);
            });
        } else {
            customersContainer.appendChild(noResultsMessage);
        }
    });
});