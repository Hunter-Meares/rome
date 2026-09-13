// contact.js - AJAX submit + UI handling + honeypot + reCAPTCHA hooks

document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('contact-form');
  const banner = document.getElementById('contact-banner');
  const spinner = document.getElementById('contact-spinner');
  const submitBtn = document.getElementById('contact-submit');

  function showBanner(msg, type = 'success') {
    banner.textContent = msg;
    banner.className = ''; // reset
    banner.style.display = 'block';
    banner.classList.add(type);
    // Auto-hide after a while for success
    if (type === 'success') {
      setTimeout(() => banner.style.display = 'none', 6000);
    }
  }

  function clearBanner() {
    banner.style.display = 'none';
    banner.textContent = '';
    banner.className = '';
  }

  async function getRecaptchaToken() {
    // Placeholder: if you enable reCAPTCHA v3 or invisible, implement here.
    // Example for v3: grecaptcha.execute('SITE_KEY', {action: 'contact'}).then(token => { ... })
    // For now we return null.
    return null;
  }

  form.addEventListener('submit', async function (ev) {
    ev.preventDefault();
    clearBanner();

    // Honeypot check (hidden input named 'website')
    const honeypot = form.querySelector('input[name="website"]');
    if (honeypot && honeypot.value.trim().length > 0) {
      showBanner('Submission blocked (spam detected).', 'error');
      return;
    }

    // Basic client-side validation
    const name = (form.name.value || '').trim();
    const email = (form.email.value || '').trim();
    const message = (form.message.value || '').trim();
    if (!name || !email || !message) {
      showBanner('Please fill all required fields.', 'error');
      return;
    }
    const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    if (!emailRegex.test(email)) {
      showBanner('Please enter a valid email address.', 'error');
      return;
    }

    // disable UI
    submitBtn.disabled = true;
    spinner.style.display = 'inline-block';

    // optional: get recaptcha token
    const recaptchaToken = await getRecaptchaToken();

    // send payload
    try {
      const payload = { name, email, message };
      if (recaptchaToken) payload.recaptcha_token = recaptchaToken;

      const res = await fetch('send_mail.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const json = await res.json();
      if (res.ok && json && json.success) {
        showBanner('Message sent — thank you! We will respond as soon as possible.', 'success');
        form.reset();
      } else {
        showBanner(json && json.error ? json.error : 'Failed to send message. Try again later.', 'error');
      }
    } catch (err) {
      console.error(err);
      showBanner('Network or server error. Please try again later.', 'error');
    } finally {
      submitBtn.disabled = false;
      spinner.style.display = 'none';
    }
  });
});
