import os
import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.competitor import Competitor
from app.models.events import CompetitorEvent
from app.models.prediction import CompetitorPrediction
from app.models.recommendations import Recommendation
from app.models.user import User
from app.workers.celery_app import celery_app

logger = logging.getLogger("report-generator")

# Import reportlab conditionally
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

@celery_app.task(name="app.workers.tasks.report_generator.generate_weekly_report")
def generate_weekly_report(company_id: int):
    """
    Weekly automated task compiling events, anomalies, recommendations, and predictions
    from the last 7 days. Generates styled PDF (or HTML fallback) and dispatches it.
    """
    logger.info(f"Generating weekly report for company_id={company_id}")
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            logger.error(f"Company id={company_id} not found for report generation.")
            return None
            
        owner = db.query(User).filter(User.id == company.user_id).first()
        recipient_email = company.notification_email if company.notification_email else (owner.email if owner else "admin@marketstrategist.local")
        
        # Fetch data from the last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        competitors = db.query(Competitor).filter(Competitor.company_id == company_id).all()
        competitor_ids = [c.id for c in competitors]
        
        events = []
        predictions = []
        recommendations = []
        
        if competitor_ids:
            # Fetch events with competitor eager loaded if possible
            events = db.query(CompetitorEvent).filter(
                CompetitorEvent.competitor_id.in_(competitor_ids),
                CompetitorEvent.created_at >= week_ago
            ).order_by(CompetitorEvent.created_at.desc()).all()
            
            # Fetch current predictions
            predictions = db.query(CompetitorPrediction).filter(
                CompetitorPrediction.competitor_id.in_(competitor_ids)
            ).all()
            
            # Fetch recommendations
            recommendations = db.query(Recommendation).filter(
                Recommendation.company_id == company_id,
                Recommendation.created_at >= week_ago
            ).order_by(Recommendation.created_at.desc()).all()
            
        # Ensure target storage folders exist
        report_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "reports"))
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        is_pdf = False
        
        if REPORTLAB_AVAILABLE:
            filename = f"weekly_report_{company_id}_{timestamp}.pdf"
            filepath = os.path.join(report_dir, filename)
            try:
                doc = SimpleDocTemplate(
                    filepath,
                    pagesize=letter,
                    rightMargin=40,
                    leftMargin=40,
                    topMargin=40,
                    bottomMargin=40
                )
                styles = getSampleStyleSheet()
                
                # Report styles
                title_style = ParagraphStyle(
                    'ReportTitle',
                    parent=styles['Heading1'],
                    fontSize=22,
                    leading=26,
                    textColor=colors.HexColor('#0f172a'),
                    spaceAfter=8
                )
                subtitle_style = ParagraphStyle(
                    'ReportSubtitle',
                    parent=styles['Normal'],
                    fontSize=11,
                    leading=13,
                    textColor=colors.HexColor('#64748b'),
                    spaceAfter=20
                )
                heading_style = ParagraphStyle(
                    'SectionHeading',
                    parent=styles['Heading2'],
                    fontSize=14,
                    leading=18,
                    textColor=colors.HexColor('#1e3a8a'),
                    spaceBefore=16,
                    spaceAfter=8,
                    keepWithNext=True
                )
                body_style = ParagraphStyle(
                    'BodyText',
                    parent=styles['Normal'],
                    fontSize=9.5,
                    leading=13.5,
                    textColor=colors.HexColor('#334155'),
                    spaceAfter=5
                )
                meta_style = ParagraphStyle(
                    'MetaText',
                    parent=styles['Normal'],
                    fontSize=8,
                    leading=10,
                    textColor=colors.HexColor('#94a3b8'),
                    spaceAfter=8
                )
                
                story = []
                
                # Title Block
                story.append(Paragraph("MarketStrategist Weekly Intelligence Digest", title_style))
                story.append(Paragraph(
                    f"Company Context: <b>{company.name}</b> | Period: {week_ago.strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}",
                    subtitle_style
                ))
                story.append(Spacer(1, 10))
                
                # Section 1: Executive Summary
                story.append(Paragraph("1. Executive Summary", heading_style))
                summary_text = (
                    f"This intelligence digest synthesizes tactical updates, competitor events, anomalies, "
                    f"and automated directives for {company.name} compiled in the last 7 days. "
                    f"We monitored a fleet of {len(competitors)} competitors, detecting {len(events)} strategic updates/anomalies, "
                    f"maintaining {len(predictions)} active threat predictions, and compiling {len(recommendations)} "
                    f"action recommendations."
                )
                story.append(Paragraph(summary_text, body_style))
                story.append(Spacer(1, 10))
                
                # Section 2: Recent Strategic Events & Anomalies
                story.append(Paragraph("2. Strategic Events & Anomalies", heading_style))
                if not events:
                    story.append(Paragraph("No significant competitor events or activity spikes detected in this period.", body_style))
                else:
                    for idx, ev in enumerate(events, 1):
                        ev_comp_name = ev.competitor.name if ev.competitor else "Unknown Competitor"
                        story.append(Paragraph(f"<b>{idx}. {ev_comp_name}: {ev.title}</b>", body_style))
                        story.append(Paragraph(
                            f"Type: {ev.event_type.upper()} | Severity: {ev.severity.upper()} | Confidence: {ev.confidence_score:.2f}",
                            meta_style
                        ))
                        story.append(Paragraph(f"{ev.description}", body_style))
                        story.append(Spacer(1, 4))
                story.append(Spacer(1, 10))
                
                # Section 3: Competitor Next-Move Predictions
                story.append(Paragraph("3. Competitor Next-Action Forecast Matrix", heading_style))
                if not predictions:
                    story.append(Paragraph("No strategic forecasts have been generated for your competitor portfolio.", body_style))
                else:
                    for idx, pred in enumerate(predictions, 1):
                        pred_comp_name = pred.competitor.name if pred.competitor else "Unknown Competitor"
                        story.append(Paragraph(
                            f"<b>{idx}. {pred_comp_name} Forecast: {pred.predicted_action}</b>",
                            body_style
                        ))
                        story.append(Paragraph(f"Confidence Score: {pred.confidence_score*100:.0f}%", meta_style))
                        story.append(Paragraph(f"Rationale: {pred.description}", body_style))
                        story.append(Spacer(1, 4))
                story.append(Spacer(1, 10))
                
                # Section 4: Recommended Strategic Actions
                story.append(Paragraph("4. Recommended Tactical Response Actions", heading_style))
                if not recommendations:
                    story.append(Paragraph("No response directives generated in the past 7 days.", body_style))
                else:
                    for idx, rec in enumerate(recommendations, 1):
                        story.append(Paragraph(f"<b>{idx}. Directive: {rec.title}</b>", body_style))
                        story.append(Paragraph(
                            f"Priority: {rec.priority.upper()} | Classification: {rec.recommendation_type.upper()}",
                            meta_style
                        ))
                        story.append(Paragraph(f"{rec.description}", body_style))
                        story.append(Spacer(1, 4))
                
                doc.build(story)
                logger.info(f"Weekly PDF generated successfully at {filepath}")
                is_pdf = True
            except Exception as pdf_err:
                logger.error(f"Error compiling ReportLab PDF: {pdf_err}. Falling back to HTML.")
                is_pdf = False
                
        # Generate HTML (as fallback or primary if reportlab failed)
        if not is_pdf:
            filename = f"weekly_report_{company_id}_{timestamp}.html"
            filepath = os.path.join(report_dir, filename)
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #f8fafc; color: #0f172a; padding: 25px; margin: 0;">
                    <div style="max-width: 750px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 30px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
                        <h1 style="color: #1e3a8a; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; margin-top: 0; font-size: 24px;">MarketStrategist Weekly Intelligence Digest</h1>
                        <p style="color: #64748b; font-size: 13px; margin-bottom: 25px;"><strong>Company:</strong> {company.name} | <strong>Period:</strong> {week_ago.strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}</p>
                        
                        <h2 style="color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-top: 25px; font-size: 16px;">1. Executive Summary</h2>
                        <p style="line-height: 1.5; color: #334155; font-size: 14px;">
                            This intelligence digest synthesizes tactical updates, competitor events, anomalies, 
                            and automated directives for {company.name} compiled in the last 7 days. 
                            We monitored a fleet of {len(competitors)} competitors, detecting {len(events)} strategic updates/anomalies, 
                            maintaining {len(predictions)} active threat predictions, and compiling {len(recommendations)} 
                            action recommendations.
                        </p>
                        
                        <h2 style="color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-top: 25px; font-size: 16px;">2. Strategic Events & Anomalies</h2>
            """
            if not events:
                html_content += "<p style='color: #64748b; font-style: italic; font-size: 13px;'>No significant competitor events or activity spikes detected in this period.</p>"
            else:
                for idx, ev in enumerate(events, 1):
                    ev_comp_name = ev.competitor.name if ev.competitor else "Unknown Competitor"
                    html_content += f"""
                    <div style="margin-bottom: 15px; padding: 12px; background-color: #f8fafc; border-left: 3px solid #3b82f6; border-radius: 4px;">
                        <h4 style="margin: 0 0 4px 0; color: #0f172a; font-size: 14px;">{idx}. {ev_comp_name}: {ev.title}</h4>
                        <p style="margin: 0 0 8px 0; font-size: 11px; color: #64748b;">Type: {ev.event_type.upper()} | Severity: {ev.severity.upper()} | Confidence: {ev.confidence_score:.2f}</p>
                        <p style="margin: 0; line-height: 1.4; color: #334155; font-size: 13px;">{ev.description}</p>
                    </div>
                    """
            
            html_content += "<h2 style='color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-top: 25px; font-size: 16px;'>3. Competitor Next-Action Forecast Matrix</h2>"
            if not predictions:
                html_content += "<p style='color: #64748b; font-style: italic; font-size: 13px;'>No strategic forecasts have been generated for your competitor portfolio.</p>"
            else:
                for idx, pred in enumerate(predictions, 1):
                    pred_comp_name = pred.competitor.name if pred.competitor else "Unknown Competitor"
                    html_content += f"""
                    <div style="margin-bottom: 15px; padding: 12px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px;">
                        <h4 style="margin: 0 0 4px 0; color: #0f172a; font-size: 14px;">{idx}. {pred_comp_name} Forecast: <span style="color: #2563eb;">{pred.predicted_action}</span></h4>
                        <p style="margin: 0 0 8px 0; font-size: 11px; color: #64748b;">Confidence Score: {pred.confidence_score*100:.0f}%</p>
                        <p style="margin: 0; line-height: 1.4; color: #334155; font-size: 13px;"><strong>Rationale:</strong> {pred.description}</p>
                    </div>
                    """
            
            html_content += "<h2 style='color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-top: 25px; font-size: 16px;'>4. Recommended Tactical Response Actions</h2>"
            if not recommendations:
                html_content += "<p style='color: #64748b; font-style: italic; font-size: 13px;'>No response directives generated in the past 7 days.</p>"
            else:
                for idx, rec in enumerate(recommendations, 1):
                    html_content += f"""
                    <div style="margin-bottom: 15px; padding: 12px; background-color: #f0fdf4; border-left: 3px solid #16a34a; border-radius: 4px;">
                        <h4 style="margin: 0 0 4px 0; color: #14532d; font-size: 14px;">{idx}. Directive: {rec.title}</h4>
                        <p style="margin: 0 0 8px 0; font-size: 11px; color: #15803d;">Priority: {rec.priority.upper()} | Focus: {rec.recommendation_type.upper()}</p>
                        <p style="margin: 0; line-height: 1.4; color: #166534; font-size: 13px;">{rec.description}</p>
                    </div>
                    """
            
            html_content += """
                    </div>
                </body>
            </html>
            """
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Fallback HTML report written successfully to {filepath}")
            
        # Dispatch email or log locally
        subject = f"[MarketStrategist] Weekly Intelligence Digest: {company.name}"
        email_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #334155; padding: 20px;">
                <h2>Weekly Executive Intelligence Digest</h2>
                <p>Hello,</p>
                <p>Please find attached your weekly competitor intelligence digest for <strong>{company.name}</strong>, compiled on {datetime.now().strftime('%Y-%m-%d')}.</p>
                <p>This report compiles:
                    <ul>
                        <li>Recent competitor strategic events and statistical anomalies</li>
                        <li>Predictive action forecasting matrix</li>
                        <li>Tailored response recommendations</li>
                    </ul>
                </p>
                <br/>
                <p>Best regards,<br/>The MarketStrategist Team</p>
            </body>
        </html>
        """
        
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT")
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if smtp_server and smtp_port and smtp_user and smtp_password:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = recipient_email
            msg.attach(MIMEText(email_body, "html"))
            
            part = MIMEBase("application", "octet-stream")
            with open(filepath, "rb") as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(filepath)}"
            )
            msg.attach(part)
            
            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, recipient_email, msg.as_string())
            logger.info(f"Successfully emailed weekly report to {recipient_email} via SMTP.")
        else:
            # Fallback mock file log
            email_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "emails"))
            os.makedirs(email_dir, exist_ok=True)
            mock_email_path = os.path.join(email_dir, f"weekly_report_email_{company_id}_{timestamp}.html")
            
            mock_email_body = f"""
            <h3>[MOCK EMAIL DISPATCH TO: {recipient_email}]</h3>
            <p><strong>Subject:</strong> {subject}</p>
            <p><strong>Attachment Link:</strong> <a href="file:///{filepath.replace(os.sep, '/')}">{os.path.basename(filepath)}</a></p>
            <hr/>
            {email_body}
            """
            with open(mock_email_path, "w", encoding="utf-8") as f:
                f.write(mock_email_body)
            logger.info(f"[Mock Notification] Saved weekly report email dispatch locally: {mock_email_path}")
            
        return filepath
        
    except Exception as e:
        logger.error(f"Failed to execute generate_weekly_report task: {e}")
        raise e
    finally:
        db.close()
