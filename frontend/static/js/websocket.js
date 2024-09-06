export { socket };

let socket;

if (!socket) {
    socket = io();
}

document.addEventListener('DOMContentLoaded', () => {

    socket.on('connect', () => {
        let userId = localStorage.getItem('user_id');
        if (!userId) {
            localStorage.setItem('user_id', socket.id);
        }
        socket.emit("update_user_id", { user_id: userId });
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
