

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mac_address', models.CharField(max_length=17, unique=True, verbose_name='MAC-адрес')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP-адрес')),
                ('vendor', models.CharField(blank=True, max_length=100, verbose_name='Производитель')),
                ('status', models.CharField(choices=[('safe', 'Безопасное'), ('suspicious', 'Подозрительное'), ('attacking', 'Атакующее'), ('blocked', 'Заблокированное')], default='safe', max_length=20, verbose_name='Статус')),
                ('first_seen', models.DateTimeField(auto_now_add=True, verbose_name='Первое обнаружение')),
                ('last_seen', models.DateTimeField(auto_now=True, verbose_name='Последнее обнаружение')),
                ('failed_attempts', models.IntegerField(default=0, verbose_name='Неудачных попыток')),
                ('successful_connections', models.IntegerField(default=0, verbose_name='Успешных подключений')),
            ],
            options={
                'verbose_name': 'Устройство',
                'verbose_name_plural': 'Устройства',
                'ordering': ['-last_seen'],
            },
        ),
        migrations.CreateModel(
            name='WPSAttackEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('pin_attempt', 'Попытка PIN'), ('brute_force', 'Брутфорс'), ('pixie_dust', 'Pixie Dust атака'), ('null_pin', 'NULL PIN атака'), ('success', 'Успешное подключение')], max_length=20, verbose_name='Тип события')),
                ('timestamp', models.DateTimeField(verbose_name='Время события')),
                ('target_bssid', models.CharField(max_length=17, verbose_name='BSSID цели')),
                ('target_essid', models.CharField(blank=True, max_length=100, verbose_name='ESSID цели')),
                ('pin_tried', models.CharField(blank=True, max_length=8, verbose_name='Испытанный PIN')),
                ('success', models.BooleanField(default=False, verbose_name='Успешно')),
                ('signal_strength', models.IntegerField(default=-70, verbose_name='Уровень сигнала (дБм)')),
                ('notes', models.TextField(blank=True, verbose_name='Примечания')),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='wps_detector.device', verbose_name='Устройство')),
            ],
            options={
                'verbose_name': 'Событие WPS атаки',
                'verbose_name_plural': 'События WPS атак',
                'ordering': ['-timestamp'],
            },
        ),
    ]
