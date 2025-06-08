document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const startBtn = document.getElementById('startBtn');
    const restartBtn = document.getElementById('restartBtn');
    const instructions = document.getElementById('instructions');
    const focusTask = document.getElementById('focusTask');
    const unfocusTask = document.getElementById('unfocusTask');
    const results = document.getElementById('results');
    const statusText = document.getElementById('statusText');
    const unfocusStatusText = document.getElementById('unfocusStatusText');
    const targetCircle = document.getElementById('targetCircle');
    const progress = document.getElementById('progress');
    const timer = document.getElementById('timer');
    const unfocusProgress = document.getElementById('unfocusProgress');
    const unfocusTimer = document.getElementById('unfocusTimer');
    
    // Configuration
    const focusDuration = 40; // seconds
    const unfocusDuration = 40; // seconds
    const circleMovementInterval = 2000; // milliseconds
    
    // Variables
    let focusTimeRemaining = focusDuration;
    let unfocusTimeRemaining = unfocusDuration;
    let focusTimerId;
    let unfocusTimerId;
    let circleMovementId;
    let isCalibrating = false;
    let calibrationStartTime; // Timestamp when actual calibration starts
    let focusStartTime; // Timestamp when focus phase starts
    let unfocusStartTime; // Timestamp when unfocus phase starts
    
    // Event listeners
    startBtn.addEventListener('click', startCalibration);
    restartBtn.addEventListener('click', resetCalibration);
    
    // Functions
    function startCalibration() {
        // Start the actual calibration process
        isCalibrating = true;
        
        // Hide everything and show only focus task
        hideAllSections();
        focusTask.classList.remove('hidden');
        
        // Start focus phase after 3 seconds countdown
        statusText.textContent = 'Starting in 3...';
        setTimeout(() => {
            statusText.textContent = 'Starting in 2...';
            setTimeout(() => {
                statusText.textContent = 'Starting in 1...';
                setTimeout(() => {
                    // Record timestamp when calibration actually starts
                    calibrationStartTime = Date.now() / 1000; // Convert to seconds for Unix timestamp
                    startFocusPhase();
                }, 1000);
            }, 1000);
        }, 1000);
    }
    
    function startFocusPhase() {
        // Record timestamp when focus phase starts
        focusStartTime = Date.now() / 1000;
        
        statusText.textContent = 'Focus on the moving circle!';
        focusTimeRemaining = focusDuration;
        updateFocusTimer();
        
        // Start moving the circle
        moveCircle();
        circleMovementId = setInterval(moveCircle, circleMovementInterval);
        
        // Start the timer
        focusTimerId = setInterval(() => {
            focusTimeRemaining--;
            updateFocusTimer();
            
            // Update progress bar
            const progressPercent = ((focusDuration - focusTimeRemaining) / focusDuration) * 100;
            progress.style.width = progressPercent + '%';
            
            if (focusTimeRemaining <= 0) {
                clearInterval(focusTimerId);
                clearInterval(circleMovementId);
                transitionToUnfocusPhase();
            }
        }, 1000);
    }
    
    function transitionToUnfocusPhase() {
        // Hide everything and show only unfocus task
        hideAllSections();
        unfocusTask.classList.remove('hidden');
        
        // Start unfocus phase after 3 seconds countdown
        unfocusStatusText.textContent = 'Next phase starting in 3...';
        setTimeout(() => {
            unfocusStatusText.textContent = 'Next phase starting in 2...';
            setTimeout(() => {
                unfocusStatusText.textContent = 'Next phase starting in 1...';
                setTimeout(() => {
                    startUnfocusPhase();
                }, 1000);
            }, 1000);
        }, 1000);
    }
    
    function startUnfocusPhase() {
        // Record timestamp when unfocus phase starts
        unfocusStartTime = Date.now() / 1000;
        
        unfocusStatusText.textContent = 'Relax your mind...';
        unfocusTimeRemaining = unfocusDuration;
        updateUnfocusTimer();
        
        // Start the timer
        unfocusTimerId = setInterval(() => {
            unfocusTimeRemaining--;
            updateUnfocusTimer();
            
            // Update progress bar
            const progressPercent = ((unfocusDuration - unfocusTimeRemaining) / unfocusDuration) * 100;
            unfocusProgress.style.width = progressPercent + '%';
            
            if (unfocusTimeRemaining <= 0) {
                clearInterval(unfocusTimerId);
                completeCalibration();
            }
        }, 1000);
    }
    
    function completeCalibration() {
        // Record timestamp when calibration ends
        const calibrationEndTime = Date.now() / 1000;
        
        // Send timestamps to backend
        fetch('/focus_calibration', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                calibration_start: calibrationStartTime,
                focus_start: focusStartTime,
                focus_end: unfocusStartTime,
                unfocus_start: unfocusStartTime,
                unfocus_end: calibrationEndTime
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Calibration data sent successfully:', data);
            
            // Show results
            hideAllSections();
            results.classList.remove('hidden');
            isCalibrating = false;
        })
        .catch((error) => {
            console.error('Error sending calibration data:', error);
            alert('Failed to complete calibration. Please try again.');
        });
    }
    
    function resetCalibration() {
        hideAllSections();
        instructions.classList.remove('hidden');
        
        // Reset progress bars
        progress.style.width = '0%';
        unfocusProgress.style.width = '0%';
    }
    
    // Helper function to hide all sections
    function hideAllSections() {
        instructions.classList.add('hidden');
        focusTask.classList.add('hidden');
        unfocusTask.classList.add('hidden');
        results.classList.add('hidden');
    }
    
    function moveCircle() {
        const container = document.getElementById('circleContainer');
        const containerWidth = container.offsetWidth;
        const containerHeight = container.offsetHeight;
        const circleWidth = targetCircle.offsetWidth;
        const circleHeight = targetCircle.offsetHeight;
        
        // Calculate new position (with padding to keep circle fully visible)
        const padding = 30;
        const maxX = containerWidth - circleWidth - padding;
        const maxY = containerHeight - circleHeight - padding;
        const newX = Math.floor(Math.random() * maxX) + padding;
        const newY = Math.floor(Math.random() * maxY) + padding;
        
        // Apply new position
        targetCircle.style.left = newX + 'px';
        targetCircle.style.top = newY + 'px';
    }
    
    function updateFocusTimer() {
        const minutes = Math.floor(focusTimeRemaining / 60).toString().padStart(2, '0');
        const seconds = (focusTimeRemaining % 60).toString().padStart(2, '0');
        timer.textContent = `${minutes}:${seconds}`;
    }
    
    function updateUnfocusTimer() {
        const minutes = Math.floor(unfocusTimeRemaining / 60).toString().padStart(2, '0');
        const seconds = (unfocusTimeRemaining % 60).toString().padStart(2, '0');
        unfocusTimer.textContent = `${minutes}:${seconds}`;
    }
    
    // Handle page unload to stop calibration if in progress
    window.addEventListener('beforeunload', function(e) {
        if (isCalibrating) {
            // Show confirmation dialog
            e.preventDefault();
            e.returnValue = '';
            return '';
        }
    });
});
