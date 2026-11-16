import pandas as pd
import os

def save_emails_to_excel(emails, filename="emails.xlsx"):
    try:
        df = pd.DataFrame(emails)

        if df.empty:
            return {
                "status": "success",
                "message": "No emails found to export"
            }

        df.to_excel(filename, index=False, engine="openpyxl")

        return {
            "status": "success",
            "message": "Emails saved successfully",
            "file": os.path.abspath(filename),
            "total_emails": len(df)
        }

    except Exception as exc:
        raise Exception(f"Failed to save emails to Excel: {str(exc)}")