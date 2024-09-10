// Replace this with the backend server URL
const serverUrl = "http://localhost:8000";

const socket = io(`${serverUrl}/ws`, {
    auth: {
        token: "your_jwt_token"  // Replace with actual JWT token
    }
});

const messageInput = document.getElementById('message-input');
const mediaInput = document.getElementById('media-input');
const messagesDiv = document.getElementById('messages');
const sendMessageButton = document.getElementById('send-message');
const onlineUsersList = document.getElementById('online-users-list');

// Fetch online users and update the list
function updateOnlineUsers(users) {
    onlineUsersList.innerHTML = '';
    users.forEach(user => {
        const li = document.createElement('li');
        li.textContent = user;
        onlineUsersList.appendChild(li);
    });
}

// Display message
function displayMessage(message) {
    const div = document.createElement('div');
    div.innerHTML = `<strong>${message.sender}:</strong> ${message.content}`;

    if (message.media_url) {
        const mediaElement = document.createElement('img');
        mediaElement.src = message.media_url;
        mediaElement.alt = "media";
        mediaElement.width = 200;
        div.appendChild(mediaElement);
    }

    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Listen for new messages
socket.on('receive_message', (message) => {
    displayMessage(message);
});

// Listen for online users
socket.on('online_users', (users) => {
    updateOnlineUsers(users);
});

// Upload media and get URL
async function uploadMedia(mediaFile) {
    const formData = new FormData();
    formData.append("file", mediaFile);

    const response = await fetch(`${serverUrl}/upload-media/`, {
        method: "POST",
        body: formData,
        headers: {
            Authorization: `Bearer ${your_jwt_token}`
        }
    });

    const data = await response.json();
    return data.file_url;
}

// Send message
async function sendMessage() {
    const content = messageInput.value;
    let media_url = null;

    if (mediaInput.files.length > 0) {
        const mediaFile = mediaInput.files[0];
        media_url = await uploadMedia(mediaFile);
    }

    const messageData = {
        sender: "your_email",  // Replace with the current user's email
        content: content,
        media_url: media_url,
        private: false,  // Adjust for private/group
        group: "default-group",  // Adjust for group chats
    };

    socket.emit('send_message', messageData);

    // Clear inputs
    messageInput.value = '';
    mediaInput.value = '';
}

// Send message on button click
sendMessageButton.addEventListener('click', () => {
    sendMessage();
});
