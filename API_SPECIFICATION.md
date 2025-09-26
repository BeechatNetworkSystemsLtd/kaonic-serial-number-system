# Kaonic Serial Number System - API Specification

## 🎯 Overview

This document provides the complete API specification for the enhanced Kaonic Serial Number System server, including proper request formats, authentication methods, and response handling for mobile app clients.

## 🔐 Authentication Methods

The server supports two authentication methods:

### 1. **ECC Signature Authentication** (Recommended)
- Uses P-256 ECDSA signatures
- Factory-specific cryptographic keys
- Enhanced security for production use

### 2. **HMAC Signature Authentication** (Legacy)
- Uses HMAC-SHA256 signatures
- Backward compatibility for existing clients
- Simpler implementation for testing

## 📱 Mobile App Integration Guide

### **Step 1: Key Generation and Registration**

#### 1.1 Generate ECC Key Pair
```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
import base64

# Generate P-256 ECC key pair
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

# Convert to PEM format
public_key_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()

# Extract base64 part for API
public_key_b64 = public_key_pem.replace("-----BEGIN PUBLIC KEY-----\n", "").replace("\n-----END PUBLIC KEY-----", "")
```

#### 1.2 Register Public Key
```http
POST /register_public_key
Content-Type: application/json

{
    "factory_name": "My Factory Name",
    "public_key": "BGFT8+6pte4ctgP3A2pMQOY4nW2aAf1v0J06lrjTttU2LfFGLBStaTK28iGf2BloqT6ZuouuL4RefECVQNqh4xk="
}
```

**Response:**
```json
{
    "message": "Public key registration request submitted",
    "request_id": 123,
    "status": "pending"
}
```

#### 1.3 Check Registration Status
```http
GET /check_registration_status?public_key=BGFT8+6pte4ctgP3A2pMQOY4nW2aAf1v0J06lrjTttU2LfFGLBStaTK28iGf2BloqT6ZuouuL4RefECVQNqh4xk=
```

**Response:**
```json
{
    "request_id": 123,
    "factory_name": "My Factory Name",
    "status": "approved",
    "created_at": "2023-12-01T10:30:00Z",
    "approved_at": "2023-12-01T10:35:00Z",
    "approved_by": "admin"
}
```

### **Step 2: Serial Number Uploads**

#### 2.1 Individual Serial Upload (ECC Signature)

**Request Headers:**
```
X-Signature: <base64_encoded_ecdsa_signature>
X-Timestamp: <unix_timestamp>
X-Factory-ID: <factory_name>
```

**Request Body:**
```
Content-Type: multipart/form-data
file: <csv_file>
```

**Python Implementation:**
```python
import requests
import hashlib
import base64
import time
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

def upload_serials_with_ecc(csv_content, private_key, factory_name, server_url="http://localhost:5000"):
    # Compute file hash
    csv_hash = hashlib.sha256(csv_content.encode()).hexdigest()
    
    # Generate timestamp
    timestamp = str(int(time.time()))
    
    # Create signature message
    message = f"{timestamp}{csv_hash}"
    
    # Sign with ECC private key
    signature = private_key.sign(
        message.encode(),
        ec.ECDSA(hashes.SHA256())
    )
    signature_b64 = base64.b64encode(signature).decode()
    
    # Prepare request
    files = {'file': ('serials.csv', csv_content, 'text/csv')}
    headers = {
        'X-Signature': signature_b64,
        'X-Timestamp': timestamp,
        'X-Factory-ID': factory_name
    }
    
    response = requests.post(f"{server_url}/add_serials", files=files, headers=headers)
    return response.json()
```

#### 2.2 Batch Serial Upload (ECC Signature)

**Request Headers:**
```
X-Signature: <base64_encoded_ecdsa_signature>
X-Timestamp: <unix_timestamp>
X-Factory-ID: <factory_name>
X-Batch-ID: <unique_batch_identifier>
X-Test-Run-Count: <number_of_test_runs>
```

**Python Implementation:**
```python
def upload_batch_serials_with_ecc(csv_content, private_key, factory_name, batch_id, test_run_count, server_url="http://localhost:5000"):
    # Compute file hash
    csv_hash = hashlib.sha256(csv_content.encode()).hexdigest()
    
    # Generate timestamp
    timestamp = str(int(time.time()))
    
    # Create signature message
    message = f"{timestamp}{csv_hash}"
    
    # Sign with ECC private key
    signature = private_key.sign(
        message.encode(),
        ec.ECDSA(hashes.SHA256())
    )
    signature_b64 = base64.b64encode(signature).decode()
    
    # Prepare request
    files = {'file': ('batch_serials.csv', csv_content, 'text/csv')}
    headers = {
        'X-Signature': signature_b64,
        'X-Timestamp': timestamp,
        'X-Factory-ID': factory_name,
        'X-Batch-ID': batch_id,
        'X-Test-Run-Count': str(test_run_count)
    }
    
    response = requests.post(f"{server_url}/add_batch_serials", files=files, headers=headers)
    return response.json()
```

#### 2.3 Chunked Serial Upload (ECC Signature)

**Request Headers:**
```
X-Signature: <base64_encoded_ecdsa_signature>
X-Timestamp: <unix_timestamp>
X-Factory-ID: <factory_name>
X-Batch-ID: <unique_batch_identifier>
X-Chunk-Index: <chunk_index>
X-Total-Chunks: <total_chunks>
```

**Python Implementation:**
```python
def upload_chunk_serials_with_ecc(csv_content, private_key, factory_name, batch_id, chunk_index, total_chunks, server_url="http://localhost:5000"):
    # Compute file hash
    csv_hash = hashlib.sha256(csv_content.encode()).hexdigest()
    
    # Generate timestamp
    timestamp = str(int(time.time()))
    
    # Create signature message
    message = f"{timestamp}{csv_hash}"
    
    # Sign with ECC private key
    signature = private_key.sign(
        message.encode(),
        ec.ECDSA(hashes.SHA256())
    )
    signature_b64 = base64.b64encode(signature).decode()
    
    # Prepare request
    files = {'file': (f'chunk_{chunk_index}.csv', csv_content, 'text/csv')}
    headers = {
        'X-Signature': signature_b64,
        'X-Timestamp': timestamp,
        'X-Factory-ID': factory_name,
        'X-Batch-ID': batch_id,
        'X-Chunk-Index': str(chunk_index),
        'X-Total-Chunks': str(total_chunks)
    }
    
    response = requests.post(f"{server_url}/add_chunk_serials", files=files, headers=headers)
    return response.json()
```

### **Step 3: Queue Management**

#### 3.1 Check Queue Status
```http
GET /queue_status?public_key=<base64_public_key>
```

**Response:**
```json
{
    "factory_id": "My Factory Name",
    "pending_uploads": 5,
    "failed_uploads": 2,
    "last_upload": "2023-12-01T10:30:00Z"
}
```

#### 3.2 Retry Failed Uploads
```http
POST /retry_failed_uploads
Content-Type: application/json

{
    "public_key": "<base64_public_key>"
}
```

**Response:**
```json
{
    "message": "Failed uploads reset to pending",
    "factory_id": "My Factory Name"
}
```

## 🔧 Alternative: HMAC Authentication (Legacy)

For backward compatibility or simpler implementation:

### HMAC Signature Generation
```python
import hmac
import hashlib
import base64

def create_hmac_signature(message, secret_key="flutter_client_secret_key"):
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()

def upload_serials_with_hmac(csv_content, factory_name, server_url="http://localhost:5000"):
    # Compute file hash
    csv_hash = hashlib.sha256(csv_content.encode()).hexdigest()
    
    # Generate timestamp
    timestamp = str(int(time.time()))
    
    # Create signature message
    message = f"{timestamp}{csv_hash}"
    
    # Create HMAC signature
    signature_b64 = create_hmac_signature(message)
    
    # Prepare request
    files = {'file': ('serials.csv', csv_content, 'text/csv')}
    headers = {
        'X-Signature': signature_b64,
        'X-Timestamp': timestamp,
        'X-Factory-ID': factory_name
    }
    
    response = requests.post(f"{server_url}/add_serials", files=files, headers=headers)
    return response.json()
```

## 📊 Complete Mobile App Implementation

### Flutter/Dart Implementation Example

```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:crypto/crypto.dart';
import 'package:pointycastle/export.dart';

class KaonicApiClient {
  final String serverUrl;
  final String factoryName;
  final ECPrivateKey privateKey;
  final ECPublicKey publicKey;

  KaonicApiClient({
    required this.serverUrl,
    required this.factoryName,
    required this.privateKey,
    required this.publicKey,
  });

  // Register factory public key
  Future<Map<String, dynamic>> registerPublicKey() async {
    final publicKeyPem = _publicKeyToPem(publicKey);
    final publicKeyB64 = _extractBase64FromPem(publicKeyPem);

    final response = await http.post(
      Uri.parse('$serverUrl/register_public_key'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'factory_name': factoryName,
        'public_key': publicKeyB64,
      }),
    );

    return jsonDecode(response.body);
  }

  // Check registration status
  Future<Map<String, dynamic>> checkRegistrationStatus() async {
    final publicKeyB64 = _extractBase64FromPem(_publicKeyToPem(publicKey));
    
    final response = await http.get(
      Uri.parse('$serverUrl/check_registration_status?public_key=$publicKeyB64'),
    );

    return jsonDecode(response.body);
  }

  // Upload serials with ECC signature
  Future<Map<String, dynamic>> uploadSerials(String csvContent) async {
    final timestamp = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    final csvHash = sha256.convert(utf8.encode(csvContent)).toString();
    final message = '$timestamp$csvHash';
    
    final signature = _signMessage(message);
    final signatureB64 = base64Encode(signature);

    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$serverUrl/add_serials'),
    );

    request.headers.addAll({
      'X-Signature': signatureB64,
      'X-Timestamp': timestamp.toString(),
      'X-Factory-ID': factoryName,
    });

    request.files.add(
      http.MultipartFile.fromString(
        'file',
        csvContent,
        filename: 'serials.csv',
        contentType: ContentType('text', 'csv'),
      ),
    );

    final response = await request.send();
    final responseBody = await response.stream.bytesToString();
    return jsonDecode(responseBody);
  }

  // Upload batch serials
  Future<Map<String, dynamic>> uploadBatchSerials(
    String csvContent,
    String batchId,
    int testRunCount,
  ) async {
    final timestamp = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    final csvHash = sha256.convert(utf8.encode(csvContent)).toString();
    final message = '$timestamp$csvHash';
    
    final signature = _signMessage(message);
    final signatureB64 = base64Encode(signature);

    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$serverUrl/add_batch_serials'),
    );

    request.headers.addAll({
      'X-Signature': signatureB64,
      'X-Timestamp': timestamp.toString(),
      'X-Factory-ID': factoryName,
      'X-Batch-ID': batchId,
      'X-Test-Run-Count': testRunCount.toString(),
    });

    request.files.add(
      http.MultipartFile.fromString(
        'file',
        csvContent,
        filename: 'batch_serials.csv',
        contentType: ContentType('text', 'csv'),
      ),
    );

    final response = await request.send();
    final responseBody = await response.stream.bytesToString();
    return jsonDecode(responseBody);
  }

  // Check queue status
  Future<Map<String, dynamic>> getQueueStatus() async {
    final publicKeyB64 = _extractBase64FromPem(_publicKeyToPem(publicKey));
    
    final response = await http.get(
      Uri.parse('$serverUrl/queue_status?public_key=$publicKeyB64'),
    );

    return jsonDecode(response.body);
  }

  // Retry failed uploads
  Future<Map<String, dynamic>> retryFailedUploads() async {
    final publicKeyB64 = _extractBase64FromPem(_publicKeyToPem(publicKey));
    
    final response = await http.post(
      Uri.parse('$serverUrl/retry_failed_uploads'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'public_key': publicKeyB64}),
    );

    return jsonDecode(response.body);
  }

  // Helper methods
  String _publicKeyToPem(ECPublicKey publicKey) {
    // Convert ECPublicKey to PEM format
    // Implementation depends on your crypto library
    return '-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----';
  }

  String _extractBase64FromPem(String pem) {
    return pem
        .replaceAll('-----BEGIN PUBLIC KEY-----', '')
        .replaceAll('-----END PUBLIC KEY-----', '')
        .replaceAll('\n', '');
  }

  List<int> _signMessage(String message) {
    // Sign message with ECC private key
    // Implementation depends on your crypto library
    return [];
  }
}
```

## 🚨 Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
    "error": "Invalid public key format: Could not deserialize key data"
}
```

#### 401 Unauthorized
```json
{
    "error": "Unauthorized"
}
```

#### 403 Forbidden
```json
{
    "error": "Request expired"
}
```

#### 429 Too Many Requests
```json
{
    "error": "Rate limit exceeded"
}
```

#### 500 Internal Server Error
```json
{
    "error": "Internal Server Error"
}
```

### Error Handling Best Practices

1. **Check Response Status**: Always check HTTP status codes
2. **Parse Error Messages**: Extract meaningful error information
3. **Implement Retry Logic**: Handle rate limiting and network errors
4. **Log Errors**: Record errors for debugging
5. **User Feedback**: Provide clear error messages to users

## 🔒 Security Considerations

### Rate Limiting
- **All Endpoints**: 100 requests per minute per IP
- **Registration**: 100 requests per minute per IP
- **Individual Uploads**: 100 requests per minute per IP
- **Batch Uploads**: 100 requests per minute per IP
- **Chunked Uploads**: 100 requests per minute per IP

### Signature Requirements
- **Timestamp**: Must be within 5 minutes of server time
- **File Hash**: SHA-256 hash of the entire file content
- **Signature**: Valid ECDSA signature or HMAC signature
- **Factory ID**: Must match registered factory name

### Best Practices
1. **Secure Key Storage**: Store private keys securely
2. **Key Rotation**: Implement regular key rotation
3. **Network Security**: Use HTTPS in production
4. **Input Validation**: Validate all inputs before sending
5. **Error Handling**: Don't expose sensitive information in errors

## 📋 Testing Checklist

### Registration Flow
- [ ] Generate ECC key pair
- [ ] Register public key
- [ ] Check registration status
- [ ] Wait for admin approval

### Upload Flow
- [ ] Test individual serial upload
- [ ] Test batch serial upload
- [ ] Test chunked serial upload
- [ ] Verify signature validation
- [ ] Test error handling

### Queue Management
- [ ] Check queue status
- [ ] Test retry failed uploads
- [ ] Verify queue monitoring

## 🎯 Success Criteria

The mobile app should be able to:
1. **Generate and register ECC key pairs**
2. **Upload serials with proper ECC signatures**
3. **Handle batch uploads efficiently**
4. **Manage offline queue operations**
5. **Provide clear error feedback to users**
6. **Implement proper retry mechanisms**

This API specification provides everything needed for the mobile app to successfully communicate with the enhanced Kaonic Serial Number System server! 🚀
