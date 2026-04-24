from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_emailverification_passwordresetcode'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='taskaisuggestion',
            index=models.Index(
                fields=['user', 'was_accepted', '-created_at'],
                name='suggestion_pending_idx'
            ),
        ),
    ]
