from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.product_list_create, name='list_or_create_products'),
    path('products/<int:product_id>/inspect/', views.inspect_product, name='inspect_product'),
    path('products/<int:product_id>/faults/', views.report_fault, name='report_fault'),
    path('faults/<int:fault_id>/resolve/', views.resolve_fault, name='resolve_fault'),
    path('faults/', views.list_faults, name='list_faults'),
    path('presigned-url/', views.get_presigned_url, name='get_presigned_url'),
    path('fault-reports/', views.list_fault_reports),
    path('get-upload-products-presigned-url/',views.get_presigned_for_products),
    path('save_uploaded_file_record/', views.save_uploaded_file_record),
    path('uploaded_files/', views.list_uploaded_files),
    path('protected/', views.protected_api),
    path('process_csv_file/', views.process_csv_file),
    # path('api/report-fault/<int:product_id>/', report_fault),
]
