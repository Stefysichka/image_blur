document.getElementById('uploadForm').addEventListener('submit', async function(event) {
    event.preventDefault(); 

    const formData = new FormData(this); 

    const response = await fetch(this.action, { method: 'POST', body: formData });
    const data = await response.json();

    if (data.success) {
        document.getElementById('processedImage').src = `/static/processed_images/${data.task_id}`;
    }
});
