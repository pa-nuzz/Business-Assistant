"""
Hash verification codes for security.
Transition from plaintext codes to SHA-256 hashed codes with per-code salts.
"""
from django.db import migrations, models
import secrets
import hashlib


def hash_existing_codes(apps, schema_editor):
    """Migrate existing plaintext codes to hashed codes."""
    EmailVerification = apps.get_model('core', 'EmailVerification')
    PasswordResetCode = apps.get_model('core', 'PasswordResetCode')
    
    # Hash existing email verification codes
    for verification in EmailVerification.objects.all():
        if verification.code:  # If plaintext code exists
            salt = secrets.token_hex(16)
            code_hash = hashlib.sha256(
                f"{salt}{verification.code}".encode()
            ).hexdigest()
            verification.salt = salt
            verification.code_hash = code_hash
            verification.save(update_fields=['salt', 'code_hash'])
    
    # Hash existing password reset codes
    for reset_code in PasswordResetCode.objects.all():
        if reset_code.code:  # If plaintext code exists
            salt = secrets.token_hex(16)
            code_hash = hashlib.sha256(
                f"{salt}{reset_code.code}".encode()
            ).hexdigest()
            reset_code.salt = salt
            reset_code.code_hash = code_hash
            reset_code.save(update_fields=['salt', 'code_hash'])


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_goal_metric_businessprofile_website_and_more'),
    ]

    operations = [
        # Step 1: Add new fields as nullable
        migrations.AddField(
            model_name='emailverification',
            name='code_hash',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='emailverification',
            name='salt',
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='passwordresetcode',
            name='code_hash',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='passwordresetcode',
            name='salt',
            field=models.CharField(max_length=32, null=True),
        ),
        
        # Step 2: Migrate existing data
        migrations.RunPython(hash_existing_codes, migrations.RunPython.noop),
        
        # Step 3: Remove old code field
        migrations.RemoveField(
            model_name='emailverification',
            name='code',
        ),
        migrations.RemoveField(
            model_name='passwordresetcode',
            name='code',
        ),
        
        # Step 4: Make new fields non-nullable
        migrations.AlterField(
            model_name='emailverification',
            name='code_hash',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='salt',
            field=models.CharField(max_length=32),
        ),
        migrations.AlterField(
            model_name='passwordresetcode',
            name='code_hash',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='passwordresetcode',
            name='salt',
            field=models.CharField(max_length=32),
        ),
        
        # Step 5: Update indexes (remove code index, add created_at index)
        migrations.RemoveIndex(
            model_name='emailverification',
            name='core_emailv_code_1f7a1e_idx',
        ),
        migrations.RemoveIndex(
            model_name='passwordresetcode',
            name='core_passwo_code_7922de_idx',
        ),
        migrations.AddIndex(
            model_name='emailverification',
            index=models.Index(fields=['created_at'], name='core_emailver_created_idx'),
        ),
        migrations.AddIndex(
            model_name='passwordresetcode',
            index=models.Index(fields=['created_at'], name='core_passwordr_created_idx'),
        ),
    ]
