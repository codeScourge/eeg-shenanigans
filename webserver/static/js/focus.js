document.addEventListener('DOMContentLoaded', function() {
    const bulb = document.querySelector('.bulb');
    const focusValue = document.getElementById('focus-value');
    
    function fetchData() {
        fetch('/data')
            .then(response => response.json())
            .then(data => {
                const focus = parseFloat(data.focus);
                updateBulb(focus);
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }
    
    function updateBulb(focus) {
        // Ensure focus is between 0 and 1
        const normalizedFocus = Math.max(0, Math.min(1, focus));
        
        // Update bulb brightness
        const brightness = normalizedFocus * 100;
        bulb.style.backgroundColor = `rgba(255, 255, 200, ${0.1 + normalizedFocus * 0.9})`;
        bulb.style.boxShadow = `0 0 ${normalizedFocus * 80}px rgba(255, 255, 200, ${normalizedFocus * 0.8})`;
        
        // Update filament
        const filament = document.querySelector('.filament');
        filament.style.borderColor = `rgba(255, 200, 100, ${0.3 + normalizedFocus * 0.7})`;
        
        // Update text
        focusValue.textContent = `Focus: ${Math.round(brightness)}%`;
    }
    
    // Initial fetch
    fetchData();
    
    // Fetch every 500ms (half a second)
    setInterval(fetchData, 500);
});
