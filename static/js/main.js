// Refresh interval in milliseconds (1 hour = 3600000 ms)
const REFRESH_INTERVAL = 3600000;
const GOOGLE_TRENDS_HOUR = 8; // 8 AM IST

// Function to refresh all platform data
async function refreshAllData() {
    try {
        const response = await fetch('/refresh-data');
        const data = await response.json();
        
        if (data.status === 'success') {
            console.log('Data refreshed successfully at:', new Date().toLocaleString());
            window.location.reload();
        } else {
            throw new Error(data.message || 'Unknown error');
        }
    } catch (error) {
        console.error('Error refreshing data:', error);
    }
}

// Function to refresh Google Trends data
async function refreshGoogleTrends() {
    try {
        const response = await fetch('/refresh-google-trends');
        const data = await response.json();
        
        if (data.status === 'success') {
            console.log('Google trends refreshed successfully at:', new Date().toLocaleString());
            window.location.reload();
        } else {
            throw new Error(data.message || 'Unknown error');
        }
    } catch (error) {
        console.error('Error refreshing Google trends:', error);
    }
}

// Schedule Google Trends refresh at 8 AM IST
function scheduleGoogleTrendsRefresh() {
    const now = new Date();
    const ist = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
    
    const targetTime = new Date(ist);
    targetTime.setHours(GOOGLE_TRENDS_HOUR, 0, 0, 0);
    
    if (ist >= targetTime) {
        targetTime.setDate(targetTime.getDate() + 1);
    }
    
    const delay = targetTime - ist;
    console.log(`Next Google Trends refresh scheduled for: ${targetTime.toLocaleString()}`);
    
    setTimeout(() => {
        refreshGoogleTrends();
        scheduleGoogleTrendsRefresh(); // Schedule next day's refresh
    }, delay);
}

// Initialize refreshes
function initializeRefreshes() {
    const lastUpdated = document.querySelector('.last-updated');
    if (lastUpdated) {
        const updateTimeText = lastUpdated.textContent.replace('Last updated: ', '');
        const updateTime = new Date(updateTimeText);
        const now = new Date();
        
        if (isNaN(updateTime.getTime())) {
            console.warn('Invalid last update time, refreshing data...');
            refreshAllData();
        } else if ((now - updateTime) > REFRESH_INTERVAL) {
            console.log('Data is stale, refreshing...');
            refreshAllData();
        }
    }
    
    // Set up periodic refresh for all platforms
    setInterval(refreshAllData, REFRESH_INTERVAL);
    
    // Start Google Trends scheduling
    scheduleGoogleTrendsRefresh();
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', initializeRefreshes);