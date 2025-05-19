document.addEventListener('DOMContentLoaded', function () {
    // Attach event listener to all progress inputs (i.e., for task completion)
    const progressInputs = document.querySelectorAll('.progress-input');
    progressInputs.forEach(input => {
        input.addEventListener('input', function () {
            // Get the associated schedule ID from the input's data attribute
            const scheduleId = input.getAttribute('data-schedule-id');
            const progressValue = input.value;

            // Send an AJAX request to update progress on the server
            updateProgress(scheduleId, progressValue);
        });
    });
});

// Function to update progress using a POST request
function updateProgress(scheduleId, progressValue) {
    const formData = new FormData();
    formData.append('progress', progressValue);

    fetch(`/schedules/update-progress/${scheduleId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // After successful response, update the UI to reflect the new progress
        const progressBar = document.querySelector(`#progress-bar-${scheduleId}`);
        const progressText = document.querySelector(`#progress-text-${scheduleId}`);

        // Update the progress bar width and text
        if (progressBar && progressText) {
            progressBar.style.width = `${progressValue}%`;
            progressText.textContent = `${progressValue}%`;
        }
    })
    .catch(error => {
        console.error('Error updating progress:', error);
    });
}
