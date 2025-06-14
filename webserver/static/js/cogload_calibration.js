document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const TOTAL_VIDEOS = 3;
    const VIDEO_DURATION = 30; // seconds
    const COUNTDOWN_DURATION = 3; // seconds
    const FEEDBACK_COUNTDOWN = 2; // seconds
    
    // Elements
    const startScreen = document.getElementById('start-screen');
    const countdownScreen = document.getElementById('countdown-screen');
    const videoScreen = document.getElementById('video-screen');
    const feedbackScreen = document.getElementById('feedback-screen');
    const resultsScreen = document.getElementById('results-screen');
    const startButton = document.getElementById('start-button');
    const videoPlayer = document.getElementById('video-player');
    const countdownText = document.getElementById('countdown-text');
    const resultsData = document.getElementById('results-data');
    
    // Buttons
    const stayButton = document.getElementById('stay-button');
    const fasterButton = document.getElementById('faster-button');
    const slowerButton = document.getElementById('slower-button');
    const explainButton = document.getElementById('explain-button');
    
    // State
    let currentVideoIndex = 0;
    let results = [];
    
    // Event listeners
    startButton.addEventListener('click', startCalibration);
    stayButton.addEventListener('click', () => recordFeedback('stay'));
    fasterButton.addEventListener('click', () => recordFeedback('faster'));
    slowerButton.addEventListener('click', () => recordFeedback('slower'));
    explainButton.addEventListener('click', () => recordFeedback('explain'));
    
    // Start calibration process
    function startCalibration() {
        startScreen.classList.add('hidden');
        currentVideoIndex = 0;
        results = [];
        startCountdown();
    }
    
    // Countdown before video
    function startCountdown() {
        countdownScreen.classList.remove('hidden');
        videoScreen.classList.add('hidden');
        feedbackScreen.classList.add('hidden');
        
        let countdown = COUNTDOWN_DURATION;
        countdownText.textContent = `Starting in ${countdown}...`;
        
        const countdownInterval = setInterval(() => {
            countdown--;
            countdownText.textContent = `Starting in ${countdown}...`;
            
            if (countdown <= 0) {
                clearInterval(countdownInterval);
                playVideo();
            }
        }, 1000);
    }
    
    // Play current video
    function playVideo() {
        countdownScreen.classList.add('hidden');
        videoScreen.classList.remove('hidden');
        
        // Set video source
        videoPlayer.src = `/static/videos/clip_${currentVideoIndex}.mp4`;
        videoPlayer.controls = false;
        
        // Record start time
        const startTime = Math.floor(Date.now() / 1000); // Unix timestamp in seconds
        
        // Play video
        videoPlayer.play();
        
        // Set timeout for video end
        setTimeout(() => {
            videoPlayer.pause();
            showFeedbackScreen(startTime);
        }, VIDEO_DURATION * 1000);
    }
    
    // Show feedback screen after video
    function showFeedbackScreen(startTime) {
        videoScreen.classList.add('hidden');
        feedbackScreen.classList.remove('hidden');
        
        // Store start time for current video
        results[currentVideoIndex] = {
            start_time: startTime,
            answer: null
        };
    }
    
    // Record user feedback
    function recordFeedback(answer) {
        // Store answer
        results[currentVideoIndex].answer = answer;
        
        // Move to next video or finish
        currentVideoIndex++;
        
        if (currentVideoIndex < TOTAL_VIDEOS) {
            feedbackScreen.classList.add('hidden');
            
            // Wait before next video
            setTimeout(() => {
                startCountdown();
            }, FEEDBACK_COUNTDOWN * 1000);
        } else {
            finishCalibration();
        }
    }
    
    // Finish calibration and show results
    function finishCalibration() {
        feedbackScreen.classList.add('hidden');
        resultsScreen.classList.remove('hidden');
        
        // Display results
        resultsData.textContent = JSON.stringify(results, null, 2);
        
        // Send results to server
        sendResultsToServer(results);
    }
    
    // Send results to server
    function sendResultsToServer(data) {
        fetch('/cogload_calibration', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Success:', data);
        })
        .catch(error => {
            console.error('Error sending data:', error);
        });
    }
});
