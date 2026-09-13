<?php
// send_mail.php - JSON/AJAX friendly PHP mail handler with honeypot, rate-limit, reCAPTCHA optional, auto-reply.
//
// FIXED: the original version set the "From" header to the VISITOR's own
// email address. Since your server (rome.vineyard.haus) has no authority
// to send mail on behalf of some_random_person@gmail.com or wherever,
// this fails SPF/DKIM checks at almost every major mail provider - which
// is very likely why messages weren't being delivered reliably. The fix:
// always send FROM your own domain, and put the visitor's address in
// Reply-To instead (so hitting "reply" still goes to them correctly).
//
// NOTE ON RELIABILITY: PHP's built-in mail() function is still not the
// most reliable way to send email from shared hosting, even with this
// fix - it depends heavily on how your host has mail configured. If you
// still have delivery problems after this fix, two solid upgrade paths:
//   1. Switch to SMTP-authenticated sending via PHPMailer, using the
//      SMTP mailbox credentials your host already gave you
//      (mail.rome.vineyard.haus). See the commented block near the
//      bottom of this file for where that would go.
//   2. Skip PHP entirely and use a free hosted form backend like
//      Formspree (formspree.io) or Web3Forms (web3forms.com) - you'd
//      just point contact.js at their endpoint instead of this file.
//      No server code, no deliverability headaches, generous free tiers.

// ==== CONFIG ====
$TO = "zeus@rome.vineyard.haus";
$FROM_ADDRESS = "zeus@rome.vineyard.haus"; // must be a real mailbox on YOUR domain
$FROM_NAME = "Rome Contact Form";
$SUBJECT_PREFIX = "[Rome Contact] ";
$AUTO_REPLY_SUBJECT = "Thanks for contacting Rome: The Eternal City";
$AUTO_REPLY_BODY = "Thanks for reaching out to the Rome dev team. We've received your message and will reply shortly.\n\n— The Immortal Staff";
$MAX_MESSAGE_LEN = 6000;
$MAX_NAME_LEN = 100;

// reCAPTCHA config (optional). If you enable reCAPTCHA, set RECAPTCHA_SECRET in your server env or paste below.
$RECAPTCHA_SECRET = getenv('RECAPTCHA_SECRET') ?: ''; // keep empty to disable recaptcha checks

// rate-limiting config
$RATE_LIMIT_SECONDS = 15;  // allow one submission per IP every N seconds
$RATE_LIMIT_DIR = sys_get_temp_dir() . '/rome_contact_rate'; // folder for small lock files

// helper: send JSON and exit
function json_response($ok, $msg = '', $code = 200) {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['success' => $ok, 'error' => $ok ? '' : $msg]);
    exit;
}

// get raw input and decode JSON (AJAX)
$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data)) {
    // fallback to normal form POST
    $data = $_POST;
}

// Honeypot: 'website' should be empty
if (!empty($data['website'])) {
    json_response(false, 'Spam detected', 400);
}

// Basic fields
$name = isset($data['name']) ? trim($data['name']) : '';
$email = isset($data['email']) ? trim($data['email']) : '';
$message = isset($data['message']) ? trim($data['message']) : '';
$recaptcha_token = isset($data['recaptcha_token']) ? $data['recaptcha_token'] : '';

// Basic server-side validation
if ($name === '' || $email === '' || $message === '') {
    json_response(false, 'Missing name, email, or message', 400);
}
if (strlen($name) > $MAX_NAME_LEN || strlen($message) > $MAX_MESSAGE_LEN) {
    json_response(false, 'Message or name too long', 400);
}
// prevent header injection
if (preg_match("/[\r\n]/", $name) || preg_match("/[\r\n]/", $email)) {
    json_response(false, 'Invalid input', 400);
}
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    json_response(false, 'Invalid email address', 400);
}

// Rate limiting by IP (simple)
$ip = $_SERVER['REMOTE_ADDR'] ?: 'unknown';
if (!is_dir($RATE_LIMIT_DIR)) {
    @mkdir($RATE_LIMIT_DIR, 0700, true);
}
$ratefile = $RATE_LIMIT_DIR . '/' . preg_replace('/[^a-z0-9_.-]/i', '_', $ip) . '.txt';
if (file_exists($ratefile)) {
    $last = intval(file_get_contents($ratefile));
    if (time() - $last < $RATE_LIMIT_SECONDS) {
        json_response(false, 'You are sending messages too frequently. Please wait a moment.', 429);
    }
}
@file_put_contents($ratefile, strval(time()));

// Optional: verify reCAPTCHA if configured
if (!empty($RECAPTCHA_SECRET)) {
    if (empty($recaptcha_token)) {
        json_response(false, 'Captcha verification required', 400);
    }
    $verify = file_get_contents("https://www.google.com/recaptcha/api/siteverify?secret=" . urlencode($RECAPTCHA_SECRET) . "&response=" . urlencode($recaptcha_token));
    $v = json_decode($verify, true);
    if (!$v || empty($v['success']) || (!empty($v['score']) && $v['score'] < 0.3)) {
        json_response(false, 'Captcha verification failed', 400);
    }
}

// Build email body (plain text)
$subject = $SUBJECT_PREFIX . 'Message from ' . $name;
$body = "You have received a new message from the Rome website contact form.\n\n";
$body .= "Name: " . $name . "\n";
$body .= "Email: " . $email . "\n";
$body .= "IP: " . $ip . "\n\n";
$body .= "Message:\n" . $message . "\n\n";

// FIXED: From is now always YOUR OWN domain address, never the visitor's.
// The visitor's real email goes in Reply-To, so clicking "reply" in your
// inbox still goes to them correctly - but the message is actually SENT
// as your own domain, which is what SPF/DKIM checks expect.
$headers = "From: \"{$FROM_NAME}\" <{$FROM_ADDRESS}>\r\n";
$headers .= "Reply-To: \"{$name}\" <{$email}>\r\n";
$headers .= "MIME-Version: 1.0\r\n";
$headers .= "Content-Type: text/plain; charset=UTF-8\r\n";

// Attempt to send server mail
$sent = @mail($TO, $subject, $body, $headers);

if (!$sent) {
    // Try simple fallback: log the failed mail (server syslog / file) then return error
    error_log("send_mail.php: mail() failed for contact form from $email ($ip)");
    json_response(false, 'Failed to send message. Please try again later.', 500);
}

// Auto-reply to sender (acknowledgement) - this one was already correct,
// since it sends FROM your own address TO the visitor.
$autoreply_headers = "From: \"Rome: The Immortal Staff\" <{$FROM_ADDRESS}>\r\n";
$autoreply_headers .= "Content-Type: text/plain; charset=UTF-8\r\n";
$autoreply_body = $AUTO_REPLY_BODY . "\n\n";
$autoreply_body .= "Original message we received:\n\n" . wordwrap($message, 72);
@mail($email, $AUTO_REPLY_SUBJECT, $autoreply_body, $autoreply_headers);

// Success!
json_response(true, '', 200);

// ============================================================
// OPTIONAL UPGRADE: SMTP-authenticated sending via PHPMailer
// ============================================================
// If plain mail() still isn't reliable enough after the From-header fix
// above, PHPMailer + your host's SMTP credentials is the standard
// stronger option. Rough shape (not wired in - you'd need to download
// PHPMailer's src/ folder from https://github.com/PHPMailer/PHPMailer
// and upload PHPMailer.php, SMTP.php, and Exception.php alongside this
// file, then replace the mail() call above with something like:
//
//   require 'PHPMailer.php'; require 'SMTP.php'; require 'Exception.php';
//   use PHPMailer\PHPMailer\PHPMailer;
//   $mail = new PHPMailer(true);
//   $mail->isSMTP();
//   $mail->Host = 'mail.rome.vineyard.haus';
//   $mail->SMTPAuth = true;
//   $mail->Username = 'your-mailbox-username-here';   // fill in yourself
//   $mail->Password = 'your-mailbox-password-here';   // fill in yourself, never share this
//   $mail->SMTPSecure = 'tls';
//   $mail->Port = 587;
//   $mail->setFrom($FROM_ADDRESS, $FROM_NAME);
//   $mail->addAddress($TO);
//   $mail->addReplyTo($email, $name);
//   $mail->Subject = $subject;
//   $mail->Body = $body;
//   $mail->send();
//
// Deliberately left commented out - fill in your own credentials
// directly on the server, never paste real mailbox passwords into a
// file you share elsewhere.
?>
