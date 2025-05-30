document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const startBtn = document.getElementById('startBtn');
    const restartBtn = document.getElementById('restartBtn');
    const instructions = document.getElementById('instructions');
    const focusTask = document.getElementById('focusTask');
    const unfocusTask = document.getElementById('unfocusTask');
    const results = document.getElementById('results');
    const statusText = document.getElementById('statusText');
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
    
    // Event listeners
    startBtn.addEventListener('click', startCalibration);
    restartBtn.addEventListener('click', resetCalibration);
    
    // Functions
    function startCalibration() {
        // Send request to start EEG data collection
        fetch('/start_focus_callibration', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            
            // Start the actual calibration process
            isCalibrating = true;
            instructions.classList.add('hidden');
            focusTask.classList.remove('hidden');
            
            // Start focus phase after 3 seconds countdown
            statusText.textContent = 'Starting in 3...';
            setTimeout(() => {
                statusText.textContent = 'Starting in 2...';
                setTimeout(() => {
                    statusText.textContent = 'Starting in 1...';
                    setTimeout(() => {
                        startFocusPhase();
                    }, 1000);
                }, 1000);
            }, 1000);
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('Failed to start calibration. Please try again.');
        });
    }
    
    function startFocusPhase() {
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
                startUnfocusPhase();
            }
        }, 1000);
    }
    
    function startUnfocusPhase() {
        // Hide focus task and show unfocus task
        focusTask.classList.add('hidden');
        unfocusTask.classList.remove('hidden');
        
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
        // Send request to stop EEG data collection
        fetch('/start_focus_callibration', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ action: 'stop' }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            
            // Show results
            unfocusTask.classList.add('hidden');
            results.classList.remove('hidden');
            isCalibrating = false;
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('Failed to complete calibration. Please try again.');
        });
    }
    
    function resetCalibration() {
        results.classList.add('hidden');
        instructions.classList.remove('hidden');
        
        // Reset progress bars
        progress.style.width = '0%';
        unfocusProgress.style.width = '0%';
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
            fetch('/start_focus_callibration', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action: 'cancel' }),
                keepalive: true
            });
            
            // Show confirmation dialog
            e.preventDefault();
            e.returnValue = '';
            return '';
        }
    });
});