import numpy as np
import pandas as pd
from app.models import OPDQueue, SilentIssue
from app import db
from datetime import datetime, timedelta

class SilentIssueDetector:
    def analyze_recent_data(self):
        # 1. Fetch recent records
        records = OPDQueue.query.order_by(OPDQueue.timestamp.desc()).limit(50).all()
        if len(records) < 10:
            return
            
        data = [r.to_dict() for r in records]
        df = pd.DataFrame(data)
        
        latest = df.iloc[0]
        
        # --- Type 1: Sudden Crowd Surge (Z-Score) ---
        mean_patients = df['patients_waiting'].mean()
        std_patients = df['patients_waiting'].std()
        
        if std_patients > 0:
            z_score = (latest['patients_waiting'] - mean_patients) / std_patients
            if z_score > 2.5: 
                self._create_alert(
                    "Sudden Crowd Surge", 
                    "High", 
                    f"Patient count {latest['patients_waiting']} is significantly higher than usual ({mean_patients:.1f})."
                )

        # --- Type 2: Efficiency Drop ---
        # High patients but active doctors < 2
        if latest['active_doctors'] < 2 and latest['patients_waiting'] > 15:
             self._create_alert(
                    "Severe Staff Shortage", 
                    "High", 
                    f"Critical: {latest['patients_waiting']} patients waiting with only {latest['active_doctors']} doctor(s)."
                )

        # --- Type 3: Trend Deviation (Growth Rate) ---
        # Check if queue grown by > 50% in last 3 records
        if len(df) >= 3:
            recent_growth = df.iloc[0]['patients_waiting'] - df.iloc[2]['patients_waiting']
            if recent_growth > 10 and latest['patients_waiting'] > 20:
                 self._create_alert(
                    "Rapid Queue Growth", 
                    "Medium", 
                    f"Queue grew by {recent_growth} patients in short interval."
                )

    def _create_alert(self, type, severity, desc):
        # Check if similar alert exists recently (deduplication)
        recent = SilentIssue.query.filter_by(issue_type=type, is_resolved=False).order_by(SilentIssue.timestamp.desc()).first()
        if recent:
            # If recent alert is less than 1 hour old, skip
            if (datetime.utcnow() - recent.timestamp).total_seconds() < 3600:
                return

        alert = SilentIssue(
            issue_type=type,
            severity=severity,
            description=desc
        )
        db.session.add(alert)
        db.session.commit()
