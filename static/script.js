/* For room.html */

// TODO: Fetch the list of existing chat messages.
// POST to the API when the user posts a new message.
// Automatically poll for new messages on a regular interval.
// Allow changing the name of a room
document.addEventListener('DOMContentLoaded', function() {
  clearmsg(); 
  updateRoomName(); 
  postMessage(); 
  startMessagePolling();
});

function clearmsg() {
  const messagesContainer = document.querySelector('.messages');
  messagesContainer.innerHTML = ''; 
}

function getMessages() {
  fetch(`/api/rooms/${WATCH_PARTY_ROOM_ID}/messages`, {
      headers: {
          'X-API-Key': WATCH_PARTY_API_KEY
      }
  })
  .then(response => response.json())
  .then(messages => {
      const messagesContainer = document.querySelector('.messages');
      messagesContainer.innerHTML = '';
      messages.forEach(message => {
        const messageElement = document.createElement('message');
        const authorElement = document.createElement('author');
        const contentElement = document.createElement('content');
        authorElement.textContent = message.user_name;
        contentElement.textContent = message.body;
        messageElement.appendChild(authorElement);
        messageElement.appendChild(contentElement);
        messagesContainer.appendChild(messageElement);
      });
  })
  .catch(error => console.error('Error:', error));
}

function postMessage() {
  document.getElementById('comment_form').addEventListener('submit', function(event) {
      event.preventDefault();
      const commentText = document.getElementById('comment_text').value.trim();
      if (!commentText) {
          alert('Please enter a message.');
          return;
      }

      fetch(`/api/rooms/${WATCH_PARTY_ROOM_ID}/messages`, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'X-API-Key': WATCH_PARTY_API_KEY,
          },
          body: JSON.stringify({ body: commentText })
      })
      .then(response => response.json())
      .then(data => {
          alert('Message posted successfully!');
          document.getElementById('comment_text').value = '';
          getMessages();
      })
      .catch(error => {
          console.error('Error:', error);
          alert('Failed to post message.');
      });
  });
}

function updateRoomName() {
  const editLink = document.getElementById('editLink');
  const saveLink = document.getElementById('saveLink');
  const roomNameDisplay = document.querySelector('.roomData .display');
  const roomNameEdit = document.querySelector('.roomData .edit');
  const roomNameInput = roomNameEdit.querySelector('input');

  editLink.addEventListener('click', function(event) {
      event.preventDefault();
      roomNameDisplay.classList.add('hide');
      roomNameEdit.classList.remove('hide');
      roomNameInput.focus();
  });

  saveLink.addEventListener('click', function(event) {
      event.preventDefault();
      const newName = roomNameInput.value.trim();
      if (!newName) {
          alert('Room name cannot be empty!');
          return;
      }

      fetch(`/api/rooms/${WATCH_PARTY_ROOM_ID}/name`, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'X-API-Key': WATCH_PARTY_API_KEY,
          },
          body: JSON.stringify({ name: newName }),
      })
      .then(response => {
          if (response.ok) {
              return response.json();
          }
          throw new Error('Network response was not ok.');
      })
      .then(data => {
          alert('Room name updated successfully!');
          document.querySelector('.roomData .display .roomName').textContent = newName;
          roomNameEdit.classList.add('hide');
          roomNameDisplay.classList.remove('hide');
      })
      .catch(error => console.error('Error:', error));
  });
}

function startMessagePolling() {
  getMessages();
  setInterval(getMessages, 100);
}


/* For profile.html */

// TODO: Allow updating the username and password
document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('updateUsername').addEventListener('click', function() {
    const newName = document.getElementById('username').value;
    fetch('/api/user/name', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': WATCH_PARTY_API_KEY,
      },
      body: JSON.stringify({ name: newName })
    })
    .then(response => response.json())
    .then(data => {
      if(data.message) {
        alert("Username updated successfully!");
      } else {
        alert("Failed to update username: " + data.error);
      }
    })
    .catch(error => console.error('Error:', error));
  });

  document.getElementById('updatePassword').addEventListener('click', function() {
    const newPassword = document.getElementById('password').value;
    fetch('/api/user/password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': WATCH_PARTY_API_KEY,
      },
      body: JSON.stringify({ password: newPassword })
    })
    .then(response => response.json())
    .then(data => {
      if(data.message) {
        alert("Password updated successfully!");
      } else {
        alert("Failed to update password: " + data.error);
      }
    })
    .catch(error => console.error('Error:', error));
  });
});