export const socket = (() => {
    // Check if we're in a browser environment
    if (typeof window === 'undefined') {
        console.error('Not in browser environment');
        return null;
    }

    // Create a socket connection
    const socketInstance = io();
    
    // Set up event listeners
    socketInstance.on('connect', () => {
        let userId = localStorage.getItem('user_id');
        if (!userId) {
            localStorage.setItem('user_id', socketInstance.id);
            userId = socketInstance.id;
        }
        
        // Get username from localStorage if available
        const username = localStorage.getItem('username');
        
        // Log for debugging
        console.log(`Sending user ID: ${userId}, username: ${username || 'none'} to server`);
        
        // Send both user ID and username to server
        socketInstance.emit("update_user_id", { 
            user_id: userId,
            username: username
        });
    });
    
    socketInstance.on('connect_error', (error) => {
        console.error('Socket connection error:', error);
    });

    return socketInstance;
})();
