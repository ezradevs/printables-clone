document.addEventListener('DOMContentLoaded', () => {
    // Dark mode toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', () => {
            document.body.classList.toggle('dark-mode');
            if (document.body.classList.contains('dark-mode')) {
                localStorage.setItem('darkMode', 'enabled');
            } else {
                localStorage.setItem('darkMode', 'disabled');
            }
        });

        if (localStorage.getItem('darkMode') === 'enabled') {
            document.body.classList.add('dark-mode');
            darkModeToggle.checked = true;
        }
    }

    // Favourite toggle
    document.querySelectorAll('.favourite-icon').forEach(icon => {
        icon.addEventListener('click', () => {
            const modelId = icon.dataset.modelId;
            fetch(`/favourite/${modelId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    icon.classList.toggle('favourited');
                } else {
                    alert(data.message);
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });

    // Add to collection
    const addToCollectionForm = document.getElementById('add-to-collection-form');
    if (addToCollectionForm) {
        addToCollectionForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const modelId = addToCollectionForm.dataset.modelId;
            const collectionId = addToCollectionForm.querySelector('select').value;
            const messageDiv = document.getElementById('collection-message');

            if (!collectionId) {
                messageDiv.textContent = 'Please select a collection.';
                messageDiv.className = 'alert alert-warning';
                return;
            }

            const formData = new FormData();
            formData.append('collection_id', collectionId);

            fetch(`/collection/add/${modelId}`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    messageDiv.textContent = data.message;
                    messageDiv.className = 'alert alert-success';
                } else {
                    messageDiv.textContent = data.message;
                    messageDiv.className = 'alert alert-danger';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                messageDiv.textContent = 'An error occurred.';
                messageDiv.className = 'alert alert-danger';
            });
        });
    }
});
