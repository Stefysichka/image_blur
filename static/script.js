document.getElementById('uploadForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // Stop the form from submitting normally

    const formData = new FormData(this);  // Collect the form data

    const response = await fetch(this.action, { method: 'POST', body: formData });
    const data = await response.json();

    if (data.success) {
        document.getElementById('processedImage').src = `/static/processed_images/${data.task_id}`;
    }
});
