from django.db import models


class Device(models.Model):
    STATUS_CHOICES = [
        ('safe', 'Безопасное'),
        ('suspicious', 'Подозрительное'),
        ('attacking', 'Атакующее'),
        ('blocked', 'Заблокированное'),
    ]

    mac_address = models.CharField(max_length=17, unique=True, verbose_name='MAC-адрес')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP-адрес')
    vendor = models.CharField(max_length=100, blank=True, verbose_name='Производитель')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='safe', verbose_name='Статус')
    first_seen = models.DateTimeField(auto_now_add=True, verbose_name='Первое обнаружение')
    last_seen = models.DateTimeField(auto_now=True, verbose_name='Последнее обнаружение')
    failed_attempts = models.IntegerField(default=0, verbose_name='Неудачных попыток')
    successful_connections = models.IntegerField(default=0, verbose_name='Успешных подключений')

    class Meta:
        verbose_name = 'Устройство'
        verbose_name_plural = 'Устройства'
        ordering = ['-last_seen']

    def __str__(self):
        return f"{self.mac_address} ({self.get_status_display()})"


class WPSAttackEvent(models.Model):
    EVENT_TYPES = [
        ('pin_attempt', 'Попытка PIN'),
        ('brute_force', 'Брутфорс'),
        ('pixie_dust', 'Pixie Dust атака'),
        ('null_pin', 'NULL PIN атака'),
        ('success', 'Успешное подключение'),
    ]

    device = models.ForeignKey(
        Device, on_delete=models.CASCADE,
        related_name='events', verbose_name='Устройство'
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, verbose_name='Тип события')
    timestamp = models.DateTimeField(verbose_name='Время события')
    target_bssid = models.CharField(max_length=17, verbose_name='BSSID цели')
    target_essid = models.CharField(max_length=100, blank=True, verbose_name='ESSID цели')
    pin_tried = models.CharField(max_length=8, blank=True, verbose_name='Испытанный PIN')
    success = models.BooleanField(default=False, verbose_name='Успешно')
    signal_strength = models.IntegerField(default=-70, verbose_name='Уровень сигнала (дБм)')
    notes = models.TextField(blank=True, verbose_name='Примечания')

    class Meta:
        verbose_name = 'Событие WPS атаки'
        verbose_name_plural = 'События WPS атак'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.event_type} от {self.device.mac_address} в {self.timestamp}"