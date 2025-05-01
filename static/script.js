document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    const chatForm = document.getElementById('chatForm');
    const uploadStatus = document.getElementById('uploadStatus');
    const chatMessages = document.getElementById('chatMessages');
    const candidatesList = document.getElementById('candidatesList');

    // Load candidates on page load
    loadCandidates();

    // Handle resume upload
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('resumeFile');
        const file = fileInput.files[0];

        if (!file) {
            showUploadStatus('Please select a file', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            showUploadStatus('Uploading...', '');
            const response = await fetch('/upload-resume', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }

            const resume = await response.json();
            showUploadStatus('Resume uploaded successfully!', 'success');
            fileInput.value = '';
            loadCandidates();
        } catch (error) {
            showUploadStatus(error.message, 'error');
        }
    });

    // Handle chat messages
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        addMessageToChat('user', message);
        messageInput.value = '';
        
        try {
            // Show loading state
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message assistant-message loading';
            loadingDiv.textContent = 'Thinking...';
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });
            
            // Remove loading message
            loadingDiv.remove();
            
            const data = await response.json();
            
            if (response.ok) {
                // Add assistant's response to chat
                addMessageToChat('assistant', data.response);
                
                // If there are candidate rankings, display them
                if (data.rankings && data.rankings.length > 0) {
                    const rankingsHtml = data.rankings.map(rank => `
                        <div class="candidate-ranking">
                            <h3>${rank.name}</h3>
                            <p><strong>Match Score:</strong> ${rank.match_percentage}%</p>
                            <p><strong>Reasoning:</strong> ${rank.reasoning}</p>
                            <p><strong>Relevant Skills:</strong> ${rank.relevant_skills.join(', ')}</p>
                        </div>
                    `).join('');
                    
                    addMessageToChat('assistant', `<div class="rankings-container">${rankingsHtml}</div>`);
                }
            } else {
                // Display error message
                addMessageToChat('assistant', `Error: ${data.detail || 'Failed to process your request. Please try again.'}`);
            }
        } catch (error) {
            console.error('Error:', error);
            addMessageToChat('assistant', 'Sorry, there was an error processing your request. Please try again.');
        }
    });

    // Load candidates
    async function loadCandidates() {
        try {
            const response = await fetch('/candidates');
            if (!response.ok) {
                throw new Error('Failed to load candidates');
            }

            const candidates = await response.json();
            displayCandidates(candidates);
        } catch (error) {
            console.error('Error loading candidates:', error);
        }
    }

    // Display candidates
    function displayCandidates(candidates) {
        candidatesList.innerHTML = '';
        candidates.forEach((candidate, index) => {
            // Format years of experience
            const years = Math.floor(candidate.years_of_experience);
            const months = Math.round((candidate.years_of_experience - years) * 12);
            const experienceText = `${years} years ${months} months`;

            // Format education details
            const educationDetails = candidate.education.map(edu => {
                const startDate = edu.start_date ? new Date(edu.start_date).toLocaleDateString() : 'N/A';
                const endDate = edu.end_date ? new Date(edu.end_date).toLocaleDateString() : 'Present';
                const gpaText = edu.gpa ? ` (GPA: ${edu.gpa})` : '';
                return `
                    <div class="education-item">
                        <strong>${edu.degree} in ${edu.field_of_study}</strong>
                        <p>${edu.institution}</p>
                        <p>${startDate} - ${endDate}${gpaText}</p>
                    </div>
                `;
            }).join('');

            // Create summary from work experience
            const summary = candidate.work_experience.length > 0 
                ? candidate.work_experience[0].description 
                : 'No work experience available';

            const card = document.createElement('div');
            card.className = 'candidate-card';
            card.innerHTML = `
                <div class="card-header">
                    <span class="candidate-number">#${index + 1}</span>
                    <h3>${candidate.first_name} ${candidate.last_name}</h3>
                </div>
                <div class="card-body">
                    <div class="card-section">
                        <h4>Current Position</h4>
                        <p>${candidate.current_position || 'Not specified'}</p>
                    </div>
                    <div class="card-section">
                        <h4>Experience</h4>
                        <p>${experienceText}</p>
                    </div>
                    <div class="card-section">
                        <h4>Contact</h4>
                        <p><i class="fas fa-envelope"></i> ${candidate.email}</p>
                        <p><i class="fas fa-phone"></i> ${candidate.phone}</p>
                    </div>
                    <div class="card-section">
                        <h4>Summary</h4>
                        <p class="summary-text">${summary}</p>
                    </div>
                    <div class="card-section">
                        <h4>Education</h4>
                        ${educationDetails}
                    </div>
                    <div class="card-section">
                        <h4>Skills</h4>
                        <div class="skills-list">
                            ${candidate.skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
                        </div>
                    </div>
                </div>
            `;
            candidatesList.appendChild(card);
        });
    }

    // Show upload status
    function showUploadStatus(message, type) {
        uploadStatus.textContent = message;
        uploadStatus.className = type ? type : '';
    }

    // Add message to chat
    function addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        // Handle HTML content for rankings
        if (content.includes('<div class="rankings-container">')) {
            messageDiv.innerHTML = content;
        } else {
            messageDiv.textContent = content;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}); 