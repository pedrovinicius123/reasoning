document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-btn');
    const essayContainer = document.getElementById('essay-container');
    const graphId = document.getElementById("graph-id").textContent

    generateBtn.addEventListener('click', async () => {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        console.log(typeof marked)

        try {
            const response = await fetch(`/agents/writer/${graphId}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            if (data.essay) {
                essayContainer.innerHTML = marked.parse(data.essay);
            } else {
                alert('No essay content received from the server.');
            }
        } catch (error) {
            console.error('Error generating essay:', error);
            alert('An error occurred while generating the essay.');
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Continue Writing';
        }
    });
});