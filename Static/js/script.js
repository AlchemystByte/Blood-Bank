document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('.donor-form');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Validate phone number: must be exactly 10 digits
            const phoneField = form.querySelector('input[name="phone"]');
            if (phoneField && phoneField.value.trim() !== '') {
                const phoneRegex = /^\d{10}$/;
                if (!phoneRegex.test(phoneField.value.trim())) {
                    alert('Phone number must be exactly 10 digits.');
                    e.preventDefault();
                    phoneField.focus();
                    return;
                }
            }

            // Validate email: must be a valid email format
            const emailField = form.querySelector('input[name="email"]');
            if (emailField && emailField.value.trim() !== '') {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(emailField.value.trim())) {
                    alert('Please enter a valid email address.');
                    e.preventDefault();
                    emailField.focus();
                    return;
                }
            }

            // Validate age: must be between 18 and 65
            const ageField = form.querySelector('input[name="age"]');
            if (ageField && ageField.value.trim() !== '') {
                const ageValue = parseInt(ageField.value.trim(), 10);
                if (isNaN(ageValue) || ageValue < 18 || ageValue > 65) {
                    alert('Age must be a number between 18 and 65.');
                    e.preventDefault();
                    ageField.focus();
                    return;
                }
            }

            // Check required fields: ensure they are not empty
            const requiredFields = form.querySelectorAll('input[required], select[required]');
            for (let field of requiredFields) {
                if (field.value.trim() === '') {
                    alert('Please fill in all required fields.');
                    e.preventDefault();
                    field.focus();
                    return;
                }
            }
        });
    });
});