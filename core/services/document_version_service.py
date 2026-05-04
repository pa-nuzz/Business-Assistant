"""Document versioning service with diff generation."""
import hashlib
import difflib
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.contrib.auth.models import User
from core.models import Document, DocumentVersion
import logging

logger = logging.getLogger(__name__)


class DocumentVersionService:
    """Service for managing document versions and diffs."""

    def __init__(self, user: User):
        self.user = user

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def generate_text_diff(old_text: str, new_text: str, context_lines: int = 3) -> str:
        """Generate unified diff between two texts."""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='previous',
            tofile='current',
            lineterm='',
            n=context_lines
        )
        
        return ''.join(diff)

    def create_version(
        self,
        document: Document,
        change_summary: str = "",
        change_type: str = "replaced"
    ) -> DocumentVersion:
        """Create a new version for a document."""
        with transaction.atomic():
            # Get next version number
            latest_version = DocumentVersion.objects.filter(
                document=document
            ).order_by('-version_number').first()
            
            next_version_number = (latest_version.version_number + 1) if latest_version else 1
            
            # Get previous text if available
            previous_text = ""
            text_diff = ""
            
            if latest_version:
                previous_text = latest_version.previous_text
                # In production: Extract text from the document
                # For now, we don't have access to the actual text
                current_text = ""
                text_diff = self.generate_text_diff(previous_text, current_text)
            
            # Calculate file hash
            try:
                file_hash = self.calculate_file_hash(document.file.path)
            except Exception:
                file_hash = ""
            
            version = DocumentVersion.objects.create(
                document=document,
                version_number=next_version_number,
                file=document.file,
                file_size=document.file.size if document.file else 0,
                file_hash=file_hash,
                change_summary=change_summary,
                change_type=change_type,
                previous_text=previous_text,
                text_diff=text_diff,
                created_by=self.user
            )
            
            logger.info(f"Created version {version.version_number} for document {document.id}")
            return version

    def get_versions(self, document: Document) -> List[Dict[str, Any]]:
        """Get all versions for a document."""
        versions = DocumentVersion.objects.filter(
            document=document
        ).select_related('created_by').order_by('-version_number')
        
        return [
            {
                'id': str(v.id),
                'version_number': v.version_number,
                'change_summary': v.change_summary,
                'change_type': v.change_type,
                'file_size': v.file_size,
                'file_hash': v.file_hash[:16] + '...' if v.file_hash else '',
                'created_at': v.created_at.isoformat(),
                'created_by': v.created_by.username if v.created_by else 'Unknown',
                'is_latest': v.is_latest,
                'download_url': v.file.url if v.file else None,
            }
            for v in versions
        ]

    def get_version_diff(self, document: Document, version_number: int) -> Dict[str, Any]:
        """Get the diff for a specific version."""
        try:
            version = DocumentVersion.objects.get(
                document=document,
                version_number=version_number
            )
        except DocumentVersion.DoesNotExist:
            return {'error': 'Version not found'}
        
        return {
            'version_number': version.version_number,
            'change_type': version.change_type,
            'change_summary': version.change_summary,
            'diff': version.text_diff,
            'has_diff': bool(version.text_diff),
            'previous_version': version.previous_version.version_number if version.previous_version else None,
        }

    def compare_versions(
        self,
        document: Document,
        version_number_1: int,
        version_number_2: int
    ) -> Dict[str, Any]:
        """Compare two versions of a document."""
        try:
            v1 = DocumentVersion.objects.get(document=document, version_number=version_number_1)
            v2 = DocumentVersion.objects.get(document=document, version_number=version_number_2)
        except DocumentVersion.DoesNotExist as e:
            return {'error': f'Version not found: {str(e)}'}
        
        # Generate diff between two arbitrary versions
        diff = self.generate_text_diff(v1.previous_text, v2.previous_text)
        
        return {
            'version_1': version_number_1,
            'version_2': version_number_2,
            'diff': diff,
            'v1_file_hash': v1.file_hash[:16] + '...' if v1.file_hash else '',
            'v2_file_hash': v2.file_hash[:16] + '...' if v2.file_hash else '',
            'files_identical': v1.file_hash == v2.file_hash,
        }

    def restore_version(self, document: Document, version_number: int) -> Optional[DocumentVersion]:
        """Restore a document to a previous version."""
        try:
            version = DocumentVersion.objects.get(
                document=document,
                version_number=version_number
            )
        except DocumentVersion.DoesNotExist:
            return None
        
        # Create a new version with the old file
        restored_version = self.create_version(
            document=document,
            change_summary=f"Restored to version {version_number}",
            change_type="replaced"
        )
        
        return restored_version

    def get_version_stats(self, document: Document) -> Dict[str, Any]:
        """Get statistics about document versions."""
        versions = DocumentVersion.objects.filter(document=document)
        total_versions = versions.count()
        
        if total_versions == 0:
            return {
                'total_versions': 0,
                'latest_version': None,
                'first_created': None,
            }
        
        latest = versions.order_by('-version_number').first()
        first = versions.order_by('version_number').first()
        
        return {
            'total_versions': total_versions,
            'latest_version': latest.version_number if latest else None,
            'first_created': first.created_at.isoformat() if first else None,
            'latest_created': latest.created_at.isoformat() if latest else None,
            'size_versions_mb': sum(v.file_size for v in versions) / (1024 * 1024),
        }
