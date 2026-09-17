from flask import current_app
from threading import Thread

def _apply_db_smtp():
    """Load SMTP settings from SiteSetting into app config if present."""
    try:
        from app.models import SiteSetting
        mapping = {
            'MAIL_SERVER': 'MAIL_SERVER',
            'MAIL_PORT': 'MAIL_PORT',
            'MAIL_USE_TLS': 'MAIL_USE_TLS',
            'MAIL_USERNAME': 'MAIL_USERNAME',
            'MAIL_PASSWORD': 'MAIL_PASSWORD',
            'MAIL_DEFAULT_SENDER': 'MAIL_DEFAULT_SENDER',
        }
        for key, cfg in mapping.items():
            row = SiteSetting.query.filter_by(key=key).first()
            if row and row.value is not None and row.value != '':
                if key == 'MAIL_PORT':
                    try:
                        current_app.config[cfg] = int(row.value)
                    except ValueError:
                        pass
                elif key == 'MAIL_USE_TLS':
                    current_app.config[cfg] = row.value in ('1', 'true', 'True', 'yes', 'on')
                else:
                    current_app.config[cfg] = row.value
    except Exception:
        pass

def send_async_email(app, msg):
    with app.app_context():
        try:
            from app import mail
            mail.send(msg)
        except Exception as e:
            try:
                current_app.logger.error(f"Mail send failed: {e}")
            except Exception:
                pass

def send_email(subject, recipients, body_html, body_text=None):
    from flask_mail import Message
    from app import mail
    _apply_db_smtp()
    if not current_app.config.get('MAIL_USERNAME'):
        try:
            current_app.logger.warning("MAIL_USERNAME not set – email not sent")
        except Exception:
            pass
        return False
    try:
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            html=body_html,
            body=body_text or body_html,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
        )
        app = current_app._get_current_object()
        Thread(target=send_async_email, args=(app, msg)).start()
        return True
    except Exception as e:
        try:
            current_app.logger.error(f"Email error: {e}")
        except Exception:
            pass
        return False

def send_welcome_subscriber(email):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;">
      <h2 style="color:#063B70;">Thank you for subscribing!</h2>
      <p>You have successfully subscribed to updates from <strong>Morang Model College &amp; School</strong>, Urlabari, Morang.</p>
      <p>You will receive notices, news and important announcements at this email address.</p>
      <p style="color:#5A6F85;font-size:14px;">Morang Model College &amp; School<br>+977-21-542730<br>morangmodel2037@gmail.com</p>
    </div>
    """
    return send_email(
        subject="Welcome – Morang Model College & School Newsletter",
        recipients=email,
        body_html=html
    )


def notify_subscribers_notice(notice_title, notice_slug, notice_content_preview=''):
    """Email all active newsletter subscribers when a notice is published/updated."""
    try:
        from app.models import NewsletterSubscriber
        subs = NewsletterSubscriber.query.filter_by(is_active=True).all()
        if not subs:
            return 0
        preview = (notice_content_preview or '')[:200]
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;">
          <h2 style="color:#063B70;">New Notice – Morang Model College &amp; School</h2>
          <h3 style="color:#17324D;">{notice_title}</h3>
          <p style="color:#5A6F85;">{preview}{'...' if len(notice_content_preview or '') > 200 else ''}</p>
          <p><a href="https://morangmodel.com/notices/{notice_slug}" style="display:inline-block;padding:12px 20px;background:#F7C928;color:#052B50;text-decoration:none;border-radius:8px;font-weight:600;">View Notice on Website</a></p>
          <p style="color:#5A6F85;font-size:13px;margin-top:24px;">You received this because you subscribed to updates from Morang Model College &amp; School, Urlabari.</p>
        </div>
        """
        sent = 0
        for s in subs:
            if send_email(f"Notice: {notice_title} – Morang Model", s.email, html):
                sent += 1
        return sent
    except Exception as e:
        try:
            from flask import current_app
            current_app.logger.error(f"notify subscribers: {e}")
        except Exception:
            pass
        return 0
