/**
 * Delete Confirmation Modal
 * 
 * Provides a stylish modal popup for confirming delete actions
 * instead of navigating to a separate confirmation page.
 */

// Function to get cookie by name (for CSRF token)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    // Create the modal HTML and append it to the body
    const modalHTML = `
    <div class="modal fade" id="deleteConfirmationModal" tabindex="-1" aria-labelledby="deleteConfirmationModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content border-0" style="border-radius: 14px; overflow: hidden;">
                <div class="modal-header" style="background: #ffebee; border-bottom: 1px solid #ffcdd2;">
                    <h5 class="modal-title fw-bold" id="deleteConfirmationModalLabel" style="color: #d32f2f;">
                        <i class="fas fa-trash-alt me-2" style="color: #f44336;"></i>
                        <span id="deleteModalTitle">Confirm Deletion</span>
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body p-4">
                    <div class="alert alert-warning d-flex align-items-center" role="alert" style="border-radius: 10px; border-left: 4px solid #f44336;">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-exclamation-triangle me-3" style="font-size: 1.5rem; color: #f44336;"></i>
                            <div>
                                <strong>Warning:</strong> This action cannot be undone. 
                                <span id="deleteWarningText">All data will be permanently deleted.</span>
                            </div>
                        </div>
                    </div>
                    
                    <div id="deleteItemDetails" class="p-3 bg-light rounded mt-3">
                        <!-- Item details will be inserted here -->
                    </div>
                </div>
                <div class="modal-footer bg-white p-3 border-top">
                    <button type="button" class="btn" data-bs-dismiss="modal" 
                            style="border-radius: 8px; background-color: #6c757d; color: white; box-shadow: 0 2px 6px rgba(108, 117, 125, 0.4); transition: all 0.2s ease;">
                        <i class="fas fa-times me-2"></i> Cancel
                    </button>
                    <button type="button" id="confirmDeleteBtn" class="btn" 
                            style="border-radius: 8px; background-color: #d32f2f; color: white; box-shadow: 0 2px 6px rgba(211, 47, 47, 0.4); transition: all 0.2s ease;">
                        <i class="fas fa-trash-alt me-2"></i> Delete
                    </button>
                </div>
            </div>
        </div>
    </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Initialize the modal
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'));
    
    // Add click event listeners to all delete buttons with the data-delete-url attribute
    document.querySelectorAll('[data-delete-url]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const deleteUrl = this.getAttribute('data-delete-url');
            const itemType = this.getAttribute('data-item-type') || 'Item';
            const itemId = this.getAttribute('data-item-id') || '';
            const itemDetails = this.getAttribute('data-item-details') || '';
            
            // Set the modal title and warning text
            document.getElementById('deleteModalTitle').textContent = `Delete ${itemType} ${itemId}`;
            document.getElementById('deleteWarningText').textContent = 
                `All ${itemType.toLowerCase()} data will be permanently deleted.`;
            
            // Set the item details if provided
            if (itemDetails) {
                document.getElementById('deleteItemDetails').innerHTML = itemDetails;
                document.getElementById('deleteItemDetails').style.display = 'block';
            } else {
                document.getElementById('deleteItemDetails').style.display = 'none';
            }
            
            // Set up the confirm delete button to submit the form
            document.getElementById('confirmDeleteBtn').onclick = function() {
                // Create a form element
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = deleteUrl;
                
                // Add CSRF token
                // First try to get the token from a form input
                let csrfToken;
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                
                // Try to get the token from a form input
                const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrfElement) {
                    csrfToken = csrfElement.value;
                } else {
                    // If not found, try to get it from the cookie
                    csrfToken = getCookie('csrftoken');
                }
                
                csrfInput.value = csrfToken;
                form.appendChild(csrfInput);
                
                // Append the form to the body and submit it
                document.body.appendChild(form);
                form.submit();
            };
            
            // Show the modal
            deleteModal.show();
        });
    });
});
