// BSOD Error Analyzer JavaScript
// Handles UI, API calls, and file uploads for the student project

// API base URL
const API_BASE = '';  // Empty string for relative URL to current host
// Alternative: const API_BASE = window.location.origin;  // For absolute URL to current host

// Wait for DOM to load
// Modularize code and add comments for clarity

document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM Content Loaded'); // Debug line

  // DOM elements
  const tabs = document.querySelectorAll('.tab');
  const fileDropArea = document.getElementById('file-drop-area');
  const fileInput = document.getElementById('dump-file');
  const fileNameDisplay = document.getElementById('file-name');
  const resultSection = document.getElementById('result-section');
  const loadingIndicator = document.getElementById('loading');
  const resultsContent = document.getElementById('results-content');
  const dumpForm = document.getElementById('dump-form');
  const codeForm = document.getElementById('code-form');
  const scanSystemBtn = document.getElementById('scan-system-btn');

  // Debug check if elements are found
  console.log('Elements found:', {
    dumpForm: !!dumpForm,
    codeForm: !!codeForm,
    scanSystemBtn: !!scanSystemBtn,
    resultSection: !!resultSection,
    loadingIndicator: !!loadingIndicator,
    resultsContent: !!resultsContent
  });

  // Tab switching logic
  tabs.forEach(tab =>
    tab.addEventListener('click', () => {
      console.log('Tab clicked:', tab.dataset.tab); // Debug line
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      document.getElementById(tab.dataset.tab + '-tab').classList.add('active');
    })
  );

  // File upload UI events
  fileDropArea.addEventListener('click', () => {
    console.log('File drop area clicked'); // Debug line
    fileInput.click();
  });
  
  fileInput.addEventListener('change', updateFileName);
  setupDragAndDrop();

  // Form submissions
  if (dumpForm) {
    dumpForm.addEventListener('submit', (e) => {
      console.log('Dump form submitted'); // Debug line
      handleDumpSubmit(e);
    });
  }

  if (codeForm) {
    codeForm.addEventListener('submit', (e) => {
      console.log('Code form submitted'); // Debug line
      handleCodeSubmit(e);
    });
  }

  if (scanSystemBtn) {
    scanSystemBtn.addEventListener('click', (e) => {
      console.log('Scan system button clicked'); // Debug line
      handleSystemScan(e);
    });
  }

  // Update file name display
  function updateFileName() {
    fileNameDisplay.textContent = fileInput.files[0]
      ? `Selected file: ${fileInput.files[0].name}`
      : '';
  }
  function displayEventViewerResults(data) {
    console.log('Displaying Event Viewer results:', data);
    
    if (!data || data.success === false) {
      showError(data?.error || 'An error occurred');
      return;
    }
    
    // If there's a warning, show it but continue processing
    let warningHtml = '';
    if (data.warning) {
      console.log('Warning from scan:', data.warning);
      warningHtml = `<div class="warning-message">
                      <p><strong>Warning:</strong> ${data.warning}</p>
                    </div>`;
    }
    
    // If no crashes were found or crashes is empty, show a message
    if (!data.crashes || data.crashes.length === 0) {
      resultsContent.innerHTML = `
        <div class="info-message">
          <h3>No BSOD Events Found</h3>
          <p>${data.message || 'No blue screen errors were found in your system\'s Event Viewer.'}</p>
          ${warningHtml}
          <div class="scan-help">
            <h4>Why might this happen?</h4>
            <ul>
              <li>Your system hasn't experienced any recent blue screens</li>
              <li>Windows may have cleared the Event Viewer logs</li>
              <li>The crash events might be stored in a different location</li>
            </ul>
          </div>
        </div>`;
      return;
    }
    
    // Build HTML to display each crash
    let html = `<div class="scan-results">
                  <h3>Found ${data.crashes.length} BSOD Events</h3>
                  ${warningHtml}
                  <div class="crash-history">`;
    
    // Loop through crashes and format each one
    data.crashes.forEach(crash => {
      html += formatCrashEvent(crash);
    });
    
    html += '</div></div>';
    resultsContent.innerHTML = html;
  }

// Helper function to format a single crash event
function formatCrashEvent(crash) {
    console.log('Formatting crash event:', crash); // Debug log
    
    let html = `<div class="crash-item">
                  <h4>${crash.error_code || 'Unknown Error'}</h4>
                  <div class="crash-details">
                    <p><strong>Date:</strong> ${crash.date || 'Unknown'}</p>
                    <p><strong>Source:</strong> ${crash.event_source || crash.source || 'Event Viewer'}</p>
                    <p><strong>Event ID:</strong> ${crash.event_id || 'Unknown'}</p>
                    <p><strong>Description:</strong> ${crash.description || 'No details available'}</p>`;
    
    // Add dump file location if available
    if (crash.dump_file) {
        html += `<p><strong>Dump File:</strong> ${crash.dump_file}</p>`;
    }
    
    // Add parameters if available
    if (crash.parameters && crash.parameters.length > 0) {
        html += `<p><strong>Parameters:</strong> ${crash.parameters.join(', ')}</p>`;
    }
    
    // Add event message if available (limit length and add expand/collapse)
    if (crash.event_message) {
        const shortMessage = crash.event_message.length > 150 ? 
            crash.event_message.substring(0, 150) + '...' : 
            crash.event_message;
            
        html += `<div class="event-message">
                   <p><strong>Event Details:</strong> 
                      <span class="short-message">${shortMessage}</span>
                      ${crash.event_message.length > 150 ? 
                        `<span class="expand-message" onclick="this.parentNode.querySelector('.short-message').style.display='none';this.parentNode.querySelector('.full-message').style.display='inline';this.style.display='none';">[Show More]</span>
                         <span class="full-message" style="display:none">${crash.event_message} <span class="collapse-message" onclick="this.parentNode.style.display='none';this.parentNode.parentNode.querySelector('.short-message').style.display='inline';this.parentNode.parentNode.querySelector('.expand-message').style.display='inline';">[Show Less]</span></span>` 
                        : ''}
                   </p>
                 </div>`;
    }
    
    html += `</div>`; // Close crash-details div
    
    // Add common causes if available
    if (crash.common_causes && crash.common_causes.length > 0) {
        html += `<div class="crash-causes">
                   <h5>Possible Causes:</h5>
                   <ul>`;
        crash.common_causes.forEach(cause => {
            html += `<li>${cause}</li>`;
        });
        html += `</ul></div>`;
    }
    
    html += '</div>'; // Close crash-item div
    return html;
}

  // Drag-and-drop handlers
  function setupDragAndDrop() {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => 
      fileDropArea.addEventListener(event, e => {
        e.preventDefault();
        e.stopPropagation();
      })
    );
    ['dragenter', 'dragover'].forEach(event =>
      fileDropArea.addEventListener(event, () => 
        fileDropArea.style.borderColor = '#0078d7'
      )
    );
    ['dragleave', 'drop'].forEach(event =>
      fileDropArea.addEventListener(event, () => 
        fileDropArea.style.borderColor = '#ccc'
      )
    );
    fileDropArea.addEventListener('drop', e => {
      const files = e.dataTransfer.files;
      if (files.length) {
        fileInput.files = files;
        updateFileName();
      }
    });
  }

  // Handle dump file form submit
  async function handleDumpSubmit(e) {
    e.preventDefault();
    if (!fileInput.files.length) {
      return alert('Please select a dump file to analyze.');
    }
    showLoading();
    try {
      const formData = new FormData();
      formData.append('dumpFile', fileInput.files[0]);
      const response = await fetch(`${API_BASE}/api/analyze-dump`, { 
        method: 'POST',
        body: formData
      });
      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      const results = await response.json();
      console.log('Dump analysis results:', results); // Debug
      displayResults(results);
    } catch (error) {
      console.error('Error in handleDumpSubmit:', error); // Debug
      showError(`Error analyzing dump file: ${error.message}`);
    } finally {
      hideLoading();
    }
  }

  // Handle error code form submit
  async function handleCodeSubmit(e) {
    e.preventDefault();
    const codeInput = document.getElementById('error-code');
    const errorCode = codeInput.value.trim();
    if (!errorCode) {
      return alert('Please enter a BSOD error code or message.');
    }
    showLoading();
    try {
      console.log('Sending error code:', errorCode); // Debug
      const response = await fetch(`${API_BASE}/api/analyze-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ errorCode })
      });
      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      const results = await response.json();
      console.log('Error code analysis results:', results); // Debug
      displayResults(results);
    } catch (error) {
      console.error('Error in handleCodeSubmit:', error); // Debug
      showError(`Error analyzing error code: ${error.message}`);
    } finally {
      hideLoading();
    }
  }

  // Scan system for BSOD history
  async function handleSystemScan(e) {
    e.preventDefault();
    showLoading();
    try {
      console.log('Starting system scan...'); // Debug
      const response = await fetch(`${API_BASE}/api/scan-system`, {
        method: 'GET'
      });
      console.log('Scan response status:', response.status); // Debug
      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      const results = await response.json();
      console.log('System scan results:', results); // Debug
      displayResults(results);
    } catch (error) {
      console.error('Error in handleSystemScan:', error); // Debug
      showError(`Error scanning system: ${error.message}`);
    } finally {
      hideLoading();
    }
  }

  // UI helpers
  function showLoading() {
    console.log('Showing loading indicator'); // Debug
    loadingIndicator.style.display = 'block';
    resultsContent.innerHTML = '';
    // Make sure the results section is visible
    resultSection.style.display = 'block';
  }
  
  function hideLoading() {
    console.log('Hiding loading indicator'); // Debug
    loadingIndicator.style.display = 'none';
  }
  
  function showError(message) {
    console.log('Showing error:', message); // Debug
    resultsContent.innerHTML = `<div class="error">${message}</div>`;
    // Make sure the results section is visible
    resultSection.style.display = 'block';
  }
  
  // Display results in the UI with comprehensive handling of all response types
  function displayResults(data) {
    console.log('displayResults called with data:', data); // Debug
    
    // Check if results section exists
    if (!resultsContent) {
      console.error('Results content element not found!');
      return;
    }
    
    // Make sure the results section is visible
    resultSection.style.display = 'block';
    
    // Handle empty data
    if (!data) {
      showError('No data received from server.');
      return;
    }
    
    // Handle error responses
    if (data.success === false) {
      showError(data.error || 'An error occurred.');
      return;
    }
    
    // Handle different response formats
    
    // If data has crashes field, it's from scan-system
    if (data.crashes !== undefined) {
      console.log('Processing scan-system response'); // Debug
      displayEventViewerResults(data);
      return;
    }
    
    // If data has code property, it's a BSOD error object
    if (data.code) {
      console.log('Processing direct error object response'); // Debug
      resultsContent.innerHTML = formatResult(data);
      return;
    }
    
    // If data has result property, use that
    if (data.result) {
      console.log('Processing result property response'); // Debug
      resultsContent.innerHTML = formatResult(data.result);
      return;
    }
    
    // If data is an array, map and join results
    if (Array.isArray(data) && data.length > 0) {
      console.log('Processing array response'); // Debug
      resultsContent.innerHTML = data.map(formatResult).join('');
      return;
    }
    
    // Default fallback if no other condition matches
    console.log('No recognized format, showing generic message'); // Debug
    resultsContent.innerHTML = '<div>No relevant BSOD information found.</div>';
  }
  
  // Format a single result object for display
  function formatResult(result) {
    console.log('Formatting result:', result); // Debug
    
    let html = '<div class="result-card">';
    
    // Display the error code and name
    if (result.code) {
      let nameDisplay = result.name || '';
      html += `<h3>${result.code}${result.hexCode ? ` (${result.hexCode})` : ''}${nameDisplay ? ` - ${nameDisplay}` : ''}</h3>`;
    }
    
    // Display description
    if (result.description) {
      html += `<p>${result.description}</p>`;
    }
    
    // Display common causes - check different property names
    let causes = result.causes || result.commonCauses || [];
    if (causes && causes.length > 0) {
      html += `<h4>Possible Causes:</h4><ul>`;
      causes.forEach(cause => {
        if (typeof cause === 'string') {
          html += `<li>${cause}</li>`;
        } else if (cause.title) {
          html += `<li><strong>${cause.title}</strong>: ${cause.description || ''}</li>`;
        }
      });
      html += `</ul>`;
    }
    
    // Display solutions - check different property names
    let solutions = result.solutions || [];
    if (solutions && solutions.length > 0) {
      html += `<h4>Suggested Solutions:</h4><ul>`;
      solutions.forEach(solution => {
        if (typeof solution === 'string') {
          html += `<li>${solution}</li>`;
        } else if (solution.title) {
          html += `<li><strong>${solution.title}</strong>: ${solution.description || ''}</li>`;
          if (solution.steps) {
            html += '<ol style="margin-left: 20px">';
            solution.steps.forEach(step => {
              html += `<li>${step}</li>`;
            });
            html += '</ol>';
          }
        }
      });
      html += `</ul>`;
    }
    
    // Add any technical details if available - with improved formatting
    if (result.technicalDetails) {
      html += `<div class="technical-details">
                <pre>${result.technicalDetails}</pre>
              </div>`;
    }
    
    html += '</div>';
    return html;
  }
});