const socket = io();

export { socket };

// Ensure this script runs after the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {

    socket.on('connect', () => {
        localStorage.setItem('user_id', socket.id);
    })

    // Connect to the Socket.IO server
    socket.on('disconnect', () => {
        console.log('Socket disconnected, attempting to reconnect...');
        socket.connect();
    });

    socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
    });

    socket.on('connect_timeout', (timeout) => {
        console.warn('Connection timeout:', timeout);
    });

    socket.on('reconnect_attempt', () => {
        console.log('Attempting to reconnect...');
    });


});
