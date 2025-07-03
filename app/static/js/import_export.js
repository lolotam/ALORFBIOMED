document.addEventListener('DOMContentLoaded', () => {
    const importForm = document.getElementById('importForm');
    const exportButtons = document.querySelectorAll('.export-button');
    const importResult = document.getElementById('importResult');
    const importProgress = document.getElementById('importProgress');
    const file = document.getElementById('file');
    const sampleData = {
        ppm: [
            'Department,Name,MODEL,SERIAL,MANUFACTURER,LOG_Number,Installation_Date,Warranty_End,PPM_Q_I_date,PPM_Q_I_engineer,PPM_Q_II_date,PPM_Q_II_engineer,PPM_Q_III_date,PPM_Q_III_engineer,PPM_Q_IV_date,PPM_Q_IV_engineer,Status',
            '4A,ECG MACHINE,SE1200EXPRESS,460016-M19902,EDAN,2452,01/05/2025,03/05/2025,28/03/2025,NIXON,28/06/2025,JAYAPRAKASH,28/09/2025,NIXON,28/12/2025,JAYAPRAKASH,Maintained'
        ].join('\n'),
        ocm: [
            'Department,Name,Model,Serial,Manufacturer,Log_Number,Installation_Date,Warranty_End,Service_Date,Engineer,Next_Maintenance,Status',
            'Radiology,X-Ray Machine,Discovery XR656,XR901234,GE Healthcare,OCM-2023-001,05/11/2024,05/11/2025,05/04/2025,Jennifer Lee,05/11/2025,Upcoming'
        ].join('\n')
    };

    const downloadTemplate = (dataType) => {
        const blob = new Blob([sampleData[dataType]], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${dataType}_template.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    };

    document.querySelectorAll('.download-template').forEach(button => {
        button.addEventListener('click', (e) => {
            const dataType = e.target.dataset.type;
            downloadTemplate(dataType);
        });
    });

    if (importForm) {
        importForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const formData = new FormData(importForm);

            if (!file.files.length) {
                importResult.innerHTML = '<div class="alert alert-danger">Please select a file.</div>';
                return;
            }

            try {
                importProgress.innerHTML = '<div class="alert alert-info">Importing... Please wait.</div>';
                const response = await fetch('/api/import/auto', {
                    method: 'POST',
                    body: formData,
                });

                const data = await response.json();
                if (response.ok) {
                    let resultHtml = `<div class="alert alert-success">${data.message}</div>`;
                    resultHtml += `<p><strong>File Type:</strong> ${data.type.toUpperCase()}</p>`;
                    
                    // Add encoding information if available
                    if (data.encoding_used) {
                        resultHtml += `<p><strong>File Encoding:</strong> ${data.encoding_used}</p>`;
                    }
                    if (data.file_name) {
                        resultHtml += `<p><strong>File Name:</strong> ${data.file_name}</p>`;
                    }
                    
                    resultHtml += `<p><strong>Total Rows:</strong> ${data.stats.total_rows}</p>`;
                    resultHtml += `<p><strong>Imported:</strong> ${data.stats.imported}</p>`;
                    resultHtml += `<p><strong>Updated:</strong> ${data.stats.updated || 0}</p>`;
                    resultHtml += `<p><strong>Skipped:</strong> ${data.stats.skipped}</p>`;
                    resultHtml += `<p><strong>Errors:</strong> ${data.stats.errors}</p>`;
                    
                    if (data.stats.skipped_details?.length > 0) {
                        resultHtml += `<h5>Skipped Details:</h5><ul>`;
                        data.stats.skipped_details.forEach(detail => {
                            resultHtml += `<li>${detail}</li>`;
                        });
                        resultHtml += `</ul>`;
                    }
                    
                    if (data.stats.error_details?.length > 0) {
                        resultHtml += `<h5>Error Details:</h5><ul>`;
                        data.stats.error_details.forEach(detail => {
                            resultHtml += `<li>${detail}</li>`;
                        });
                        resultHtml += `</ul>`;
                    }

                    importResult.innerHTML = resultHtml;
                } else {
                    // Enhanced error handling for encoding issues
                    let errorHtml = `<div class="alert alert-danger">`;
                    errorHtml += `<strong>Import Failed:</strong> ${data.error || 'Unknown error'}`;
                    
                    if (data.details) {
                        errorHtml += `<br><small>${data.details}</small>`;
                    }
                    
                    if (data.suggestions && data.suggestions.length > 0) {
                        errorHtml += `<hr><strong>Suggestions:</strong><ul>`;
                        data.suggestions.forEach(suggestion => {
                            errorHtml += `<li>${suggestion}</li>`;
                        });
                        errorHtml += `</ul>`;
                    }
                    
                    if (data.file_name) {
                        errorHtml += `<hr><small><strong>File:</strong> ${data.file_name}</small>`;
                    }
                    
                    errorHtml += `</div>`;
                    importResult.innerHTML = errorHtml;
                }
            } catch (error) {
                console.error('Error during import:', error);
                importResult.innerHTML = '<div class="alert alert-danger">An unexpected error occurred during import.</div>';
            } finally {
                importProgress.innerHTML = '';
            }
        });
    }

    exportButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const dataType = button.getAttribute('data-type');
            try {
                const response = await fetch(`/api/export/${dataType}`);
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = `${dataType}_export_${new Date().toISOString().split('T')[0]}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    a.remove();
                } else {
                    const error = await response.json();
                    alert(`Export failed: ${error.message || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Error during export:', error);
                alert('An error occurred during export');
            }
        });
    });
});
