"""
Add performance indexes for common queries.
Optimizes database queries for 10k+ concurrent users.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0010_hash_verification_codes'),
    ]

    operations = [
        # Add composite index for user conversations (user + deleted_at + updated_at)
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(
                fields=['user', 'deleted_at', '-updated_at'],
                name='core_conv_user_del_upd_idx'
            ),
        ),
        
        # Add composite index for task dashboard queries (user + status + priority + deleted_at)
        migrations.AddIndex(
            model_name='task',
            index=models.Index(
                fields=['user', 'status', 'priority', 'deleted_at'],
                name='core_task_user_stat_prio_idx'
            ),
        ),
        
        # Add composite index for document status queries (user + status + deleted_at)
        migrations.AddIndex(
            model_name='document',
            index=models.Index(
                fields=['user', 'status', 'deleted_at'],
                name='core_doc_user_stat_del_idx'
            ),
        ),
        
        # Add composite index for message queries (conversation + created_at)
        migrations.AddIndex(
            model_name='message',
            index=models.Index(
                fields=['conversation', 'created_at'],
                name='core_msg_conv_created_idx'
            ),
        ),
        
        # Add composite index for user memory queries (user + category)
        migrations.AddIndex(
            model_name='usermemory',
            index=models.Index(
                fields=['user', 'category'],
                name='core_mem_user_cat_idx'
            ),
        ),
        
        # Add composite index for task assignment queries (assignee + status + deleted_at)
        migrations.AddIndex(
            model_name='task',
            index=models.Index(
                fields=['assignee', 'status', 'deleted_at'],
                name='core_task_assign_stat_idx'
            ),
        ),
        
        # Add composite index for notification queries (user + is_read + created_at)
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['user', 'is_read', '-created_at'],
                name='core_notif_user_read_idx'
            ),
        ),
    ]
