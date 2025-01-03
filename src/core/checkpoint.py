from typing import Dict, Any, Optional
import json
from datetime import datetime
import aiofiles
import os

class CheckpointHandler:
    def __init__(self, checkpoint_file: str):
        self.checkpoint_file = checkpoint_file
        self.last_checkpoint = self._load_checkpoint()

    async def save_checkpoint(
        self,
        batch_num: int,
        items_processed: int,
        results: List[Any]
    ) -> None:
        """Save processing checkpoint"""
        checkpoint = {
            'timestamp': datetime.utcnow().isoformat(),
            'batch_num': batch_num,
            'items_processed': items_processed,
            'results': [r.to_dict() for r in results if r.success]
        }
        
        async with aiofiles.open(self.checkpoint_file, 'w') as f:
            await f.write(json.dumps(checkpoint))
        
        self.last_checkpoint = checkpoint

    def _load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load previous checkpoint if exists"""
        if not os.path.exists(self.checkpoint_file):
            return None
            
        try:
            with open(self.checkpoint_file) as f:
                return json.load(f)
        except Exception:
            return None

    def get_resume_position(self) -> int:
        """Get position to resume processing from"""
        if not self.last_checkpoint:
            return 0
        return self.last_checkpoint['items_processed']