const video = document.getElementById('video');
const progressBar = document.getElementById('progress-bar');
const cogLoadDisplay = document.getElementById('cog-load');
const playbackRateDisplay = document.getElementById('playback-rate');

let currentLoad = 0;
let lastLoad = 0;
let stepsSinceUIUpdate = 0;

// Function to fetch data
function fetchData() {
    fetch('/data')
        .then(response => response.json())
        .then(data => {
            console.log(data);
            lastLoad = currentLoad;
            // Ensure cogload is a number
            currentLoad = parseFloat(data.cogload) || 0;
            stepsSinceUIUpdate = 0;
        })
        .catch(error => {
            console.error('Error fetching data:', error);
        });
}

// Function to update UI with smooth transitions
function updateUI() {

    const stepsPerTransition = 2000 / 100 // since so many UI ubdates for each fetch
    const difference = currentLoad - lastLoad
    const stepSize = difference / stepsPerTransition
    const displayedLoad = lastLoad + (stepSize  * stepsSinceUIUpdate)
    // console.log("displayedLoad ", displayedLoad)

    // 0-1 to 1-2
    const playbackRate = displayedLoad + 1
    // console.log("playbackRate ", playbackRate)
    video.playbackRate = playbackRate;
    
    progressBar.style.width = `${currentLoad * 100}%`;
    cogLoadDisplay.textContent = currentLoad.toFixed(2);
    playbackRateDisplay.textContent = playbackRate.toFixed(2);
}

// Start fetching data when video starts playing
video.addEventListener('play', () => {
    // Set initial data fetch and UI update
    fetchData();
    updateUI();
    
    // Set up intervals for data fetching and UI updates
    setInterval(fetchData, 2000);  // Fetch data every 2 seconds
    setInterval(updateUI, 100);    // Update UI more frequently for smooth transitions
}); 