import pandas as pd
from typing import List, Optional
from models import Issue

class DataLoader:
    def __init__(self, logger: Optional[ContextLogger] = None):
        self.logger = logger or ContextLogger(__name__)

    def load_from_csv(self, filepath: str) -> List[Issue]:
        """Load and validate issues from CSV file"""
        try:
            df = pd.read_csv(filepath)
            required_cols = {'issue_id', 'creator_user_id', 'assigned_group'}
            
            # Validate columns
            missing = required_cols - set(df.columns)
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

            # Clean data
            df = df.dropna(subset=['issue_id'])
            df = df[df['creator_group'].isna()]  # Only process null creator groups
            
            # Convert to issues
            issues = []
            for _, row in df.iterrows():
                try:
                    issue = Issue(
                        issue_id=str(row['issue_id']).strip(),
                        creator_user_id=str(row['creator_user_id']).strip(),
                        assigned_group=str(row['assigned_group']).strip(),
                        creator_group=None
                    )
                    issues.append(issue)
                except Exception as e:
                    self.logger.warning(
                        f"Error converting row: {str(e)}",
                        row=row.to_dict()
                    )
                    
            self.logger.info(f"Loaded {len(issues)} issues from CSV")
            return issues
            
        except Exception as e:
            self.logger.error(f"Error loading CSV: {str(e)}")
            raise