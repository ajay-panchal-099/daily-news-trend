// Schedule regular data refreshes
function scheduleRefreshes() {
    // Refresh all platforms except Google Trends every hour
    console.log('Scheduling refreshes...');
    setInterval(refreshAllPlatforms, 60*60*1000); // 60 minutes
    
    // Special handling for Google Trends (8 AM IST daily)
    const now = new Date();
    const istOffset = 5.5 * 60 * 60 * 1000; // IST is UTC+5:30
    const next8AM = new Date();
    
    // Set next refresh to 8 AM IST
    next8AM.setUTCHours(2, 30, 0, 0); // 8 AM IST = 2:30 UTC
    if (now.getTime() > next8AM.getTime()) {
        next8AM.setUTCDate(next8AM.getUTCDate() + 1);
    }
    
    const initialDelay = next8AM.getTime() - now.getTime();
    
    setTimeout(() => {
        refreshGoogleTrends();
        // Then set daily interval
        setInterval(refreshGoogleTrends, 24 * 60 * 60 * 1000);
    }, initialDelay);
}

function refreshAllPlatforms() {
    console.log('Refreshing all platforms...');
    fetch('/refresh-data')
        .then(response => response.json())
        .then(data => {
            console.log('All platforms refreshed:', data);
            location.reload(); // Reload page to show new data
        })
        .catch(error => {
            console.error('Refresh error:', error);
        });
}

function refreshGoogleTrends() {
    console.log('Refreshing Google Trends...');
    fetch('/refresh-google-trends')
        .then(response => response.json())
        .then(data => {
            console.log('Google Trends refreshed:', data);
            // Only reload if on Google Trends page
            if (window.location.pathname.includes('google')) {
                location.reload();
            }
        })
        .catch(error => {
            console.error('Google Trends refresh error:', error);
        });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', scheduleRefreshes);