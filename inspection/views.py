import json
import csv
from io import StringIO
import boto3
from django.conf import settings
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseNotFound
from django.utils.timezone import now
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from .models import CSVUploadHistory, Product, Inspection, FaultReport, Resolution
from .auth0 import requires_auth
from .require_auths import requires_role


@api_view(['POST'])
@requires_auth
@requires_role('admin')
def process_csv_file(request):
    try:
        body = json.loads(request.body)
        upload_id = body.get("upload_id")
        if not upload_id:
            return JsonResponse({"error": "Missing upload_id"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    try:
        upload = CSVUploadHistory.objects.get(id=upload_id)
        file_url = upload.file_url
        uploaded_by = upload.uploaded_by

        s3_base = f"https://{settings.AWS_S3_BUCKET_NAME2}.s3.{settings.AWS_REGION}.amazonaws.com/"
        if not file_url.startswith(s3_base):
            return JsonResponse({"error": "Invalid S3 file URL."}, status=400)

        key = file_url[len(s3_base):]
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        s3_object = s3.get_object(Bucket=settings.AWS_S3_BUCKET_NAME2, Key=key)
        content = s3_object['Body'].read().decode('utf-8')
        reader = csv.DictReader(StringIO(content))

        count = 0
        for row in reader:
            name = row.get("name")
            type_ = row.get("type")
            created_at = row.get("created_at")

            if not name or not type_:
                continue

            Product.objects.create(
                name=name,
                type=type_,
                status="pending",
                created_by=uploaded_by,
                created_at=created_at or now(),
                batch=upload
            )
            count += 1

        return JsonResponse({
            "message": f"{count} products created.",
            "file_url": file_url
        })

    except CSVUploadHistory.DoesNotExist:
        return JsonResponse({"error": "Upload ID not found"}, status=404)
    except s3.exceptions.NoSuchKey:
        return JsonResponse({"error": "File not found in S3."}, status=404)
    except Exception as e:
        print("Error while processing CSV:", e)
        return JsonResponse({"error": str(e)}, status=500)


@requires_auth
@requires_role('admin')
def get_presigned_for_products(request):
    file_name = request.GET.get('file_name')
    if not file_name:
        return JsonResponse({'error': 'file_name query param is required'}, status=400)

    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    try:
        presigned_url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': settings.AWS_S3_BUCKET_NAME2,
                'Key': file_name,
                'ContentType': request.GET.get('content_type', 'application/octet-stream')
            },
            ExpiresIn=3600,
            HttpMethod='PUT'
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    file_url = f"https://{settings.AWS_S3_BUCKET_NAME2}.s3.{settings.AWS_REGION}.amazonaws.com/{file_name}"

    return JsonResponse({
        'upload_url': presigned_url,
        'file_url': file_url,
    })


@api_view(['POST'])
@requires_auth
@requires_role('admin')
def save_uploaded_file_record(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        file_name = data['file_name']
        file_url = data['file_url']
        uploaded_by = data.get('uploaded_by', 'admin')

        record = CSVUploadHistory.objects.create(
            file_name=file_name,
            file_url=file_url,
            uploaded_by=uploaded_by,
            uploaded_at=now()
        )
        return JsonResponse({
            'message': 'Upload record saved',
            'upload_id': record.id  
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@requires_auth
@requires_role('admin')
def list_uploaded_files(request):
    uploads = CSVUploadHistory.objects.order_by('-uploaded_at').values(
        'file_name', 'file_url', 'uploaded_by', 'uploaded_at'
    )
    return JsonResponse(list(uploads), safe=False)


def get_presigned_url(request):
    file_name = request.GET.get('file_name')
    if not file_name:
        return JsonResponse({'error': 'file_name query param is required'}, status=400)

    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    try:
        presigned_url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': settings.AWS_S3_BUCKET_NAME, 
                'Key': file_name, 
                'ContentType': request.GET.get('content_type', 'application/octet-stream')
            },
            ExpiresIn=3600,
            HttpMethod='PUT'
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    file_url = f'https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_name}'
    return JsonResponse({
        'upload_url': presigned_url,
        'file_url': file_url,
    })

@api_view(['GET', 'POST'])
@requires_auth
@requires_role('worker')
def product_list_create(request):
    if request.method == 'GET':
        products = Product.objects.all()
        data = []
        for p in products:
            data.append({
                'id': p.id,
                'name': p.name,
                'type': p.type,
                'status': p.status,
                'created_by': p.created_by,
                'created_at': p.created_at.isoformat(),
            })
        return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        try:
            body = json.loads(request.body)
            name = body['name']
            type_ = body['type']
            created_by = body.get('created_by', 'system')
        except (KeyError, json.JSONDecodeError):
            return HttpResponseBadRequest("Invalid request payload")

        product = Product.objects.create(name=name, type=type_, created_by=created_by)
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'type': product.type,
            'status': product.status,
            'created_by': product.created_by,
            'created_at': product.created_at.isoformat(),
        }, status=201)


@api_view(['POST'])
@requires_auth
@requires_role('worker')
def inspect_product(request, product_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return HttpResponseNotFound("Product not found")

    try:
        body = json.loads(request.body)
        inspected_by = body.get('inspected_by', 'inspector')
        result = body['result']
        notes = body.get('inspection_notes', '')
    except (KeyError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid request payload")

    inspection = Inspection.objects.create(
        product=product,
        inspected_by=inspected_by,
        result=result,
        notes=notes
    )

    product.status = 'inspected' if result == 'pass' else 'faulty'
    product.save()

    return JsonResponse({
        'inspection_id': inspection.id,
        'product_id': product.id,
        'result': inspection.result,
        'notes': inspection.notes,
        'inspected_at': inspection.inspected_at.isoformat(),
        'product_status': product.status,
    }, status=201)


@api_view(['POST'])
@requires_auth
@requires_role('worker')
def report_fault(request, product_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return HttpResponseNotFound("Product not found")

    try:
        body = json.loads(request.body)
        description = body['description']
        image_url = body['image_url']
        created_by = body.get('created_by', 'operator')
    except (KeyError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid request payload")

    fault = FaultReport.objects.create(
        product=product,
        description=description,
        image_url=image_url,
        created_by=created_by,
        status='open',
    )

    product.status = 'faulty'
    product.save()

    return JsonResponse({
        'fault_id': fault.id,
        'product_id': product.id,
        'description': fault.description,
        'image_url': fault.image_url,
        'status': fault.status,
        'created_at': fault.created_at.isoformat(),
    }, status=201)


@api_view(['POST'])
@requires_auth
@requires_role('worker')
def resolve_fault(request, fault_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        fault = FaultReport.objects.get(id=fault_id)
    except FaultReport.DoesNotExist:
        return HttpResponseNotFound("Fault not found")

    if fault.status == 'closed':
        return JsonResponse({'error': 'Fault already resolved'}, status=409)

    try:
        body = json.loads(request.body)
        resolved_by = body.get('resolved_by', 'engineer')  # string now
        remarks = body['remarks']
    except (KeyError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid request payload")

    resolution = Resolution.objects.create(
        fault=fault,
        resolved_by=resolved_by,
        remarks=remarks
    )
    fault.status = 'closed'
    fault.save()

    product = fault.product
    if not FaultReport.objects.filter(product=product, status='open').exists():
        product.status = 'resolved'
        product.save()

    return JsonResponse({
        'resolution_id': resolution.id,
        'fault_id': fault.id,
        'remarks': resolution.remarks,
        'resolved_at': resolution.resolved_at.isoformat(),
        'fault_status': fault.status,
        'product_status': product.status,
    }, status=201)


@api_view(['GET'])
@requires_auth
@requires_role('worker')
def list_faults(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    faults = FaultReport.objects.all()
    data = []
    for f in faults:
        data.append({
            'fault_id': f.id,
            'product_id': f.product.id,
            'description': f.description,
            'image_url': f.image_url,
            'status': f.status,
            'created_at': f.created_at.isoformat(),
            'created_by': f.created_by,
        })
    return JsonResponse(data, safe=False)


@api_view(['GET'])
@requires_auth
@requires_role('worker')
def list_fault_reports(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    reports = FaultReport.objects.all().select_related('product')
    data = [{
        'id': report.id,
        'product': report.product.name,
        'description': report.description,
        'image_url': report.image_url,
        'status': report.status,
        'created_at': report.created_at.isoformat(),
    } for report in reports]

    return JsonResponse(data, safe=False)


@requires_auth
@requires_role("admin")
def protected_api(request):
    user = request.auth.get('sub') 
    return JsonResponse({"message": "Access granted", "user": user})