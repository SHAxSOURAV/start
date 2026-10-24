# AWS S3 Media Storage & Retention Architecture Guide
## (`docs/MEDIA_STORAGE_GUIDELINES.md`)

This document defines the official media storage architecture, multi-provider fallback hierarchy, and S3 object retention lifecycle policies for this backend workspace.

---

## 1. Storage Provider Architecture & Hierarchy

The backend implements a **Unified Media Storage Engine** ([src/util/media_storage.py](file:///c:/Users/Sourav/Documents/Start/src/util/media_storage.py)) backed by **AWS S3** ([src/util/s3.py](file:///c:/Users/Sourav/Documents/Start/src/util/s3.py)) using native asynchronous I/O (`aioboto3`).

```mermaid
graph TD
    UploadReq[Incoming Media Upload] --> Adapter[Unified media_storage.py]
    Adapter --> ProviderCheck{config.storage_provider}
    
    ProviderCheck -->|s3 (Primary)| S3Client[AWS S3 via aioboto3]
    ProviderCheck -->|cloudinary| CloudinaryClient[Cloudinary REST API]
    ProviderCheck -->|local| LocalDisk[Local uploads/ directory]
    
    S3Client -->|On Error / Unconfigured| FallbackCloudinary[Fallback to Cloudinary]
    FallbackCloudinary -->|On Error| FallbackLocal[Fallback to Local uploads/]
```

### Environment Switch (`.env` Contract)
```bash
# Primary media storage engine: s3 | cloudinary | local
STORAGE_PROVIDER=s3

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=eu-north-1
AWS_S3_BUCKET_NAME=your-s3-bucket-name
```

---

## 2. Media Retention Lifecycle Policy (Retention Periods)

To prevent ballooning AWS cloud storage bills and maintain privacy compliance (GDPR/CCPA), every media item uploaded to S3 is categorized and tagged with a strict retention lifecycle:

| Media Category | Prefix / Folder | Retention Period | Description & Business Rules |
| :--- | :--- | :--- | :--- |
| **User Profiles** | `profile_images/` | **Permanent** | User avatars, driver photos, platform branding. Purged only when replaced by a new image or when an account is permanently purged after 30-day soft deletion. |
| **Temporary Uploads** | `temp/` | **2 Days** | Unattached uploads, draft posts, temporary file buffers. Purged if not finalized within 48 hours. |
| **Chat Media** | `chats/` | **180 Days** | Socket.IO chat room attachments, images, voice notes. Automatically cleaned up after 6 months. |
| **KYC & Documents** | `documents/` | **365 Days** | Driver licenses, identity verification documents, compliance proof. |
| **Exports & Reports** | `exports/` | **7 Days** | Generated accounting CSVs, PDF invoices, debug logs. |

---

## 3. Automated Retention Enforcement Mechanism

Retention is enforced through a dual-layer strategy:

### Layer 1: S3 Object Metadata & Tagging
When any file is uploaded (server-side proxy or presigned direct upload), the backend attaches S3 Object Tags:
```
RetentionCategory=temp&UploadedAt=20261024
```

### Layer 2: Async Background Worker Job ([src/jobs/s3_retention_cleanup_job.py](file:///c:/Users/Sourav/Documents/Start/src/jobs/s3_retention_cleanup_job.py))
- Managed by APScheduler (`AsyncIOScheduler`).
- Executes daily at **03:00 UTC** (`0 3 * * *`).
- Asynchronously iterates through `temp/`, `chats/`, `documents/`, and `exports/` prefixes using `aioboto3` paginators.
- Issues atomic batch deletion calls (`s3.delete_objects()`) for objects exceeding their retention threshold.

---

## 4. Developer & Agent Implementation Guide

### 4.1 Server-Side Proxy Upload (Multipart Form Endpoints)
In any controller or service where a file was accepted via `upload_file()` middleware:

```python
from src.util.media_storage import upload_media, delete_media

# 1. Upload new image (automatically tags RetentionCategory and uploads to S3)
image_url = await upload_media(
    local_path=local_file_path,
    folder="profile_images",
    retention_category="profiles",  # or 'temp', 'chats', 'documents'
)

# 2. Cleanup old media when replaced
if old_image_url:
    await delete_media(old_image_url)
```

### 4.2 High-Speed Direct Presigned Upload (Zero Server Load)
For large video files or high-concurrency mobile apps (React Native / Flutter / Web):

```python
from src.util.s3 import generate_presigned_upload_url

presigned_data = await generate_presigned_upload_url(
    folder="chats",
    filename="voice_note.mp4",
    content_type="video/mp4",
    expires_in=3600,
    retention_category="chats",
)
# Returns:
# {
#   "uploadUrl": "https://your-s3-bucket-name.s3.eu-north-1.amazonaws.com/chats/uuid.mp4?AWSAccessKeyId=...",
#   "key": "chats/uuid.mp4",
#   "publicUrl": "https://your-s3-bucket-name.s3.eu-north-1.amazonaws.com/chats/uuid.mp4",
#   "expiresIn": 3600,
#   "retentionCategory": "chats"
# }
```

### 4.3 Secure Presigned Download (For Private Documents)
For KYC or sensitive verification documents that should not be publicly accessible:

```python
from src.util.s3 import generate_presigned_download_url

secure_download_url = await generate_presigned_download_url(
    s3_url_or_key="documents/license_user_123.pdf",
    expires_in=1800,  # Valid for 30 minutes
)
```

---

## 5. Golden Rules for Media Storage

1. **Never use blocking `boto3` inside `async def`**: Always use `aioboto3` sessions or `upload_media`.
2. **Never leave temporary files on disk**: When uploading server-side, `upload_file_to_s3` automatically unlinks the local file from `uploads/` upon successful S3 transfer.
3. **Always specify `retention_category`**: Never dump un-categorized files into the bucket root. Always use `folder` and `retention_category`.
4. **Always clean up on update**: When a user replaces their profile avatar or document, call `await delete_media(old_url)` to prevent orphaned files.
