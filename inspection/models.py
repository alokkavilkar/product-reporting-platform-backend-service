from django.db import models
from django.utils.timezone import now

class CSVUploadHistory(models.Model):
    file_name = models.CharField(max_length=255)
    file_url = models.URLField()
    uploaded_by = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(default=now)

    def __str__(self):
        return self.file_name

class Product(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('inspected', 'Inspected'),
        ('faulty', 'Faulty'),
        ('resolved', 'Resolved'),
    ]
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    created_by = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)    
    batch = models.ForeignKey(CSVUploadHistory, on_delete=models.SET_NULL, null=True, blank=True,related_name="products")

class Inspection(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    inspected_by = models.CharField(max_length=100)
    result = models.CharField(max_length=10, choices=[('pass', 'Pass'), ('fail', 'Fail')])
    notes = models.TextField(blank=True)
    inspected_at = models.DateTimeField(auto_now_add=True)

class FaultReport(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    description = models.TextField()
    image_url = models.URLField()
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=[('open', 'Open'), ('closed', 'Closed')], default='open')

class Resolution(models.Model):
    fault = models.OneToOneField(FaultReport, on_delete=models.CASCADE)
    resolved_by = models.CharField(max_length=100)
    remarks = models.TextField()
    resolved_at = models.DateTimeField(auto_now_add=True)
