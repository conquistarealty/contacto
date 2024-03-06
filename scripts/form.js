// Function to generate HTML content
function generateHtmlContent(formData) {
    let htmlContent = `<!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact Form Response</title>
    <style>
    body {
        font-family: Arial, sans-serif;
        background-color: #f0f0f0;
        padding: 20px;
    }
    .container {
        max-width: 600px;
        margin: 0 auto;
        background-color: #fff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    }
    label {
        font-weight: bold;
    }
    </style>
    </head>
    <body>
    <div class="container">
    <h2>Contact Form Response</h2>`;

    // Add form data to the HTML content
    for (const key in formData) {
        htmlContent += `<label>${key}:</label>`;
        // If the value is an array (multiple selections), format it as a list
        if (Array.isArray(formData[key])) {
            htmlContent += `<ul>`;
            formData[key].forEach(value => {
                htmlContent += `<li>${value}</li>`;
            });
            htmlContent += `</ul>`;
        } else {
            htmlContent += `<p>${formData[key]}</p>`;
        }
    }

    // Add closing HTML tags
    htmlContent += `</div>
    </body>
    </html>`;

    return htmlContent;
}

// Function to handle errors
function handleConfigError(error) {
  // Display the error message
  const errorMessage = document.createElement('p');
  errorMessage.textContent = 'Error loading configuration: ' + error.message;
  document.body.appendChild(errorMessage);

  // Hide other elements
  const container = document.querySelector('.container');
  container.style.display = 'none';
}

// Function to update email placeholders
function updateEmailPlaceholders(email) {
    const emailPlaceholders = document.querySelectorAll('.email-placeholder');
    emailPlaceholders.forEach(placeholder => {
        placeholder.textContent = email;
    });
}

// Function to copy email to clipboard
function copyEmailToClipboard(email) {
    const tempInput = document.createElement('input');
    tempInput.value = email;
    document.body.appendChild(tempInput);
    tempInput.select();
    document.execCommand('copy');
    document.body.removeChild(tempInput);
    alert('Email copied to clipboard: ' + email);
}

// Function to dynamically deselect the default option
 function createUpdateDefaultOption(selectElement) {
     function updateDefaultOption() {
         const defaultOption = selectElement.querySelector('option[value=""][disabled][selected]');
         if (defaultOption) {
             defaultOption.selected = false;
             console.log("Default option removed.");
             // Remove the event listener after it's been triggered once
             selectElement.removeEventListener('change', updateDefaultOption);
         }
     }
     // Return the closure
     return updateDefaultOption;
 }

 // Function to print information about the select element
 function printSelectInfo(selectElement) {
     const label = selectElement.getAttribute('data-label') || 'No label';
     const selectedCount = Array.from(selectElement.selectedOptions).length;
     console.log('Select element:', label);
     console.log('Number of selected options:', selectedCount);
 }

// Set form action (mailto) from config.json
fetch('config.json')
.then(response => response.json())
.then(data => {
    // Alert user if email key not found
    if (!data.email) {
        throw new Error('Email address not found in config.json');
    }

    // Alert user if title not found
    if (!data.title) {
      throw new Error('Title not found in config.json');
    }

    // Set document title
    document.title = data.title;

    // Check if subject is provided and not empty
    if (!data.subject || data.subject.trim() === '') {
        throw new Error('Subject is required in config.json');
    }

    const form = document.getElementById('contact-form');
    const email = data.email;
    const subject = encodeURIComponent(data.subject); // Encrypt subject
    form.setAttribute('action', 'mailto:' + email + '?subject=' + subject);

    // Set form backend URL if available and not null
    const formBackendUrl = data.form_backend_url;
    if (formBackendUrl !== undefined && formBackendUrl !== null) {
       form.setAttribute('action', formBackendUrl);
       form.setAttribute('enctype', 'application/x-www-form-urlencoded');
    }

    // Update email placeholder in instructions
    updateEmailPlaceholders(email);

    // Add click event listener to copy email to clipboard
    const emailPlaceholders = document.querySelectorAll('.email-placeholder');
    emailPlaceholders.forEach(placeholder => {
        placeholder.addEventListener('click', () => {
            copyEmailToClipboard(email);
        });
    });
})
.catch(error => {
    handleConfigError(error);
});

// Fetching and populating form fields from config.json
fetch('config.json')
.then(response => {
    // Alert user if config.json unreachable
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    return response.json();
})
.then(data => {
    // Get form element by id
    const form = document.getElementById('contact-form');

    // Iterate over questions in config.json
    data.questions.forEach(question => {
        // Create labels for each question
        const label = document.createElement('label');
        label.textContent = question.label + ':';
        label.style.color = '#ddd'; // Light text color
        form.appendChild(label);
        form.appendChild(document.createElement('br'));

        let input;
        // Create input elements for each question
        if (question.type === 'textarea') {
            input = document.createElement('textarea');
            input.setAttribute('rows', '4');
        } else if (question.type === 'selectbox') {
            input = document.createElement('select');
            // Create options for select box
            question.options.forEach(option => {
                const optionElem = document.createElement('option');
                optionElem.textContent = option.label;
                optionElem.setAttribute('value', option.value);
                if (option.selected) {
                    optionElem.setAttribute('selected', 'selected');
                }
                if (option.disabled) {
                    optionElem.setAttribute('disabled', 'disabled');
                }
                input.appendChild(optionElem);
            });

            // Attach event listener to dynamically deselect default option when any other option is selected
            const updateDefaultOption = createUpdateDefaultOption(input);
            input.addEventListener('change', updateDefaultOption);

            // Attach event listener to print the number of selected options
            input.addEventListener('change', () => {
                printSelectInfo(input);
            });
        } else {
            input = document.createElement('input');
            input.setAttribute('type', question.type);
        }

        // Set the attributes common attributes for form processing
        input.setAttribute('name', question.name);
        input.setAttribute('data-label', question.label); // Store label
        if (question.required) {
            input.setAttribute('required', '');
        }

        // Add custom attributes
        if (question.custom) {
            Object.entries(question.custom).forEach(([key, value]) => {
                input.setAttribute(key, value);
            });
        }

        // Add to form
        form.appendChild(input);
        form.appendChild(document.createElement('br'));
    });

    // Setup form submission button
    const send_button = document.createElement('button');
    send_button.setAttribute('type', 'submit');
    send_button.textContent = 'Send';
    form.appendChild(send_button);

    // Setup form download button
    const download_html_button = document.createElement('button');
    download_html_button.setAttribute('type', 'button');
    download_html_button.textContent = 'Download Form';

    // Add event to listen for click
    download_html_button.addEventListener('click', () => {
        const formData = {};
        const inputs = form.querySelectorAll('input, textarea, select');
        let valid = true;

        inputs.forEach(input => {
            let fieldValue = input.value;

            if (input.tagName === 'SELECT' && input.hasAttribute('multiple')) {
                const selectedOptions = Array.from(input.selectedOptions);

                // Convert array to string
                fieldValue = selectedOptions.map(option => option.value).join(', ');
            }

            if (input.hasAttribute('required') && (!fieldValue || !fieldValue.trim())) {
                valid = false;
                input.style.borderColor = 'red'; // Highlight required fields in red
            } else {
                input.style.borderColor = '#555'; // Reset border color
            }

            // Store form data
            formData[input.getAttribute('data-label')] = fieldValue;
        });

        if (valid) {
            // Generate HTML content
            const htmlContent = generateHtmlContent(formData);

            // Create a Blob containing the HTML content
            const blob = new Blob([htmlContent], { type: 'text/html' });

            // Create a download link
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'contact_form_response.html';

            // Append the link to the body and click it programmatically
            document.body.appendChild(link);
            link.click();

            // Remove the link from the body
            document.body.removeChild(link);
        } else {
            alert('Please fill out all required fields.');
        }
    });
    form.appendChild(download_html_button);
})
.catch(error => {
    handleConfigError(error);
});
