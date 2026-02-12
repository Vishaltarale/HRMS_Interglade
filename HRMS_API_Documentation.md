# HRMS

## API Documentation

### Organization Management

#### 1. Create Organization

Creates a new organization in the system.

**Endpoint:** `POST api/organization/create/`

**Request Body:**
```json
{
  "orgName": "string",
  "orgLocation": "string", 
  "orgContact": "string",
  "orgEmail": "string",
  "orgLink": "string",
  "orgStatus": "string"
}
```

**Field Requirements:**
- `orgName`: Required, maximum 50 characters
- `orgLocation`: Required, maximum 100 characters  
- `orgContact`: Required, maximum 100 characters (digits only, 10-12 length)
- `orgEmail`: Required, must be unique
- `orgLink`: Required
- `orgStatus`: Required, must be either "Active" or "Inactive"

**Response:**

**Success (201 Created):**
```json
{
  "orgName": "Example Corp",
  "orgLocation": "New York, NY",
  "orgContact": "1234567890",
  "orgEmail": "contact@example.com",
  "orgLink": "https://example.com",
  "orgStatus": "Active"
}
```

**Error (400 Bad Request):**
```json
{
  "field_name": ["Error message"]
}
```

---

#### 2. List Organizations (Paginated)

Retrieves a paginated list of all organizations.

**Endpoint:** `GET api/organization/fetch/`

**Query Parameters:**
- `page`: Page number (optional, default: 1)

**Response:**

**Success (200 OK):**
```json
{
  "count": 25,
  "next": "http://localhost:8000/fetch/?page=2",
  "previous": null,
  "results": [
    {
      "id": "organization_id",
      "orgName": "Example Corp",
      "orgLocation": "New York, NY",
      "orgContact": "1234567890",
      "orgEmail": "contact@example.com",
      "orgLink": "https://example.com",
      "orgStatus": "Active"
    }
  ]
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/fetch/?page=1"
```

---

#### 3. Get Organization by ID

Retrieves a specific organization by its ID.

**Endpoint:** `GET api/organization/fetch/<str:pk>/`

**Path Parameters:**
- `pk`: Organization ID (string)

**Response:**

**Success (200 OK):**
```json
{
  "id": "organization_id",
  "orgName": "Example Corp",
  "orgLocation": "New York, NY",
  "orgContact": "1234567890",
  "orgEmail": "contact@example.com",
  "orgLink": "https://example.com",
  "orgStatus": "Active"
}
```

**Error (204 No Content):**
```json
{
  "error": "data not found"
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/fetch/organization_id/"
```

---

#### 4. Update Organization

Updates an existing organization (supports both full and partial updates).

**Endpoint:** `PUT api/organization/update/<str:pk>/` or `PATCH /update/<str:pk>/`

**Path Parameters:**
- `pk`: Organization ID (string)

**Request Body:**
```json
{
  "orgName": "Updated Corp Name",
  "orgLocation": "Updated Location",
  "orgContact": "9876543210",
  "orgEmail": "updated@example.com",
  "orgLink": "https://updated-example.com",
  "orgStatus": "Inactive"
}
```

**Response:**

**Success (201 Created):**
```json
{
  "id": "organization_id",
  "orgName": "Updated Corp Name",
  "orgLocation": "Updated Location",
  "orgContact": "9876543210",
  "orgEmail": "updated@example.com",
  "orgLink": "https://updated-example.com",
  "orgStatus": "Inactive"
}
```

**Error (400 Bad Request):**
```json
{
  "error": "data not found"
}
```
or
```json
{
  "field_name": ["Validation error message"]
}
```

**Example Request:**
```bash
curl -X PUT "http://localhost:8000/update/organization_id/" \
  -H "Content-Type: application/json" \
  -d '{
    "orgName": "Updated Corp Name",
    "orgStatus": "Inactive"
  }'
```

---

#### 5. Delete Organization

Deletes an organization from the system.

**Endpoint:** `DELETE api/organization/delete/<str:pk>/`

**Path Parameters:**
- `pk`: Organization ID (string)

**Response:**

**Success (200 OK):**
```json
{
  "Message": "Orgnization Record deleted successfully"
}
```

**Error (400 Bad Request):**
```json
{
  "error": "data not found"
}
```

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/delete/organization_id/"
```

---

### Data Model

The Organization model uses MongoDB with the following structure:

```python
class Organization(Document):
    orgName = StringField(required=True, max_length=50)
    orgLocation = StringField(required=True, max_length=100)
    orgContact = StringField(required=True, max_length=100)
    orgEmail = StringField(required=True, unique=True)
    orgLink = StringField(required=True)
    orgStatus = StringField(required=True, choices=["Active", "Inactive"])
```

**Database Configuration:**
- Collection: `organizations`
- Indexes: `orgEmail`, `orgName`

---

### Complete API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/create/` | Create new organization |
| GET | `/fetch/` | List all organizations (paginated) |
| GET | `/fetch/<id>/` | Get organization by ID |
| PUT/PATCH | `/update/<id>/` | Update organization |
| DELETE | `/delete/<id>/` | Delete organization |


---

## Department Management

Base URL: `/api/department/`

### Department API Endpoints

#### 1. Create Department

Creates a new department within an organization.

**Endpoint:** `POST /api/department/create/`

**Request Body:**
```json
{
  "deptName": "string",
  "deptCode": "string",
  "deptDesc": "string",
  "orgId": "organization_id",
  "orgStatus": "string"
}
```

**Field Requirements:**
- `deptName`: Required, maximum 50 characters
- `deptCode`: Required, maximum 100 characters, must be unique
- `deptDesc`: Required, maximum 200 characters
- `orgId`: Required, must reference an existing Organization ID
- `orgStatus`: Required, must be either "Active" or "Inactive"

**Response:**

**Success (201 Created):**
```json
{
  "id": "department_id",
  "deptName": "Human Resources",
  "deptCode": "HR001",
  "deptDesc": "Manages employee relations and organizational policies",
  "orgId": "organization_id",
  "orgStatus": "Active"
}
```

**Error (400 Bad Request):**
```json
{
  "field_name": ["Error message"]
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/department/create/" \
  -H "Content-Type: application/json" \
  -d '{
    "deptName": "Information Technology",
    "deptCode": "IT001",
    "deptDesc": "Manages technology infrastructure and software development",
    "orgId": "organization_id",
    "orgStatus": "Active"
  }'
```

---

#### 2. List Departments (Paginated)

Retrieves a paginated list of all departments.

**Endpoint:** `GET /api/department/fetch/`

**Query Parameters:**
- `page`: Page number (optional, default: 1)

**Response:**

**Success (200 OK):**
```json
{
  "count": 15,
  "next": "http://localhost:8000/api/department/fetch/?page=2",
  "previous": null,
  "results": [
    {
      "id": "department_id",
      "deptName": "Human Resources",
      "deptCode": "HR001",
      "deptDesc": "Manages employee relations and organizational policies",
      "orgId": "organization_id",
      "orgStatus": "Active"
    }
  ]
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/department/fetch/?page=1"
```

---

#### 3. Get Department by ID

Retrieves a specific department by its ID.

**Endpoint:** `GET /api/department/fetch/<str:pk>/`

**Path Parameters:**
- `pk`: Department ID (string)

**Response:**

**Success (200 OK):**
```json
{
  "id": "department_id",
  "deptName": "Human Resources",
  "deptCode": "HR001",
  "deptDesc": "Manages employee relations and organizational policies",
  "orgId": "organization_id",
  "orgStatus": "Active"
}
```

**Error (204 No Content):**
```json
{
  "error": "data not found"
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/department/fetch/department_id/"
```

---

#### 4. Update Department

Updates an existing department (full update only).

**Endpoint:** `PUT /api/department/update/<str:pk>/`

**Path Parameters:**
- `pk`: Department ID (string)

**Request Body:**
```json
{
  "deptName": "Updated Department Name",
  "deptCode": "UPDATED001",
  "deptDesc": "Updated department description",
  "orgId": "organization_id",
  "orgStatus": "Inactive"
}
```

**Response:**

**Success (201 Created):**
```json
{
  "id": "department_id",
  "deptName": "Updated Department Name",
  "deptCode": "UPDATED001",
  "deptDesc": "Updated department description",
  "orgId": "organization_id",
  "orgStatus": "Inactive"
}
```

**Error (400 Bad Request):**
```json
{
  "error": "data not found"
}
```
or
```json
{
  "field_name": ["Validation error message"]
}
```

**Example Request:**
```bash
curl -X PUT "http://localhost:8000/api/department/update/department_id/" \
  -H "Content-Type: application/json" \
  -d '{
    "deptName": "Updated IT Department",
    "deptCode": "IT002",
    "deptDesc": "Updated technology and innovation department",
    "orgId": "organization_id",
    "orgStatus": "Active"
  }'
```

---

#### 5. Delete Department

Deletes a department from the system.

**Endpoint:** `DELETE /api/department/delete/<str:pk>/`

**Path Parameters:**
- `pk`: Department ID (string)

**Response:**

**Success (200 OK):**
```json
{
  "Message": "Departments Record deleted successfully"
}
```

**Error (400 Bad Request):**
```json
{
  "error": "data not found"
}
```

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/api/department/delete/department_id/"
```

---

### Department Data Model

The Department model uses MongoDB with the following structure:

```python
class Departments(Document):
    deptName = StringField(required=True, max_length=50)
    deptCode = StringField(required=True, max_length=100, unique=True)
    deptDesc = StringField(required=True, max_length=200)
    orgId = ReferenceField(Organization, reverse_delete_rule=CASCADE, required=True)
    orgStatus = StringField(required=True, choices=["Active", "Inactive"])
```

**Database Configuration:**
- Collection: `departments`
- Indexes: `deptCode`, `deptName`, `orgId`
- Cascade Delete: When an Organization is deleted, all associated departments are automatically deleted

**Relationships:**
- `orgId`: References the Organization model with CASCADE delete rule

---

### Department API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/department/create/` | Create new department |
| GET | `/api/department/fetch/` | List all departments (paginated) |
| GET | `/api/department/fetch/<id>/` | Get department by ID |
| PUT | `/api/department/update/<id>/` | Update department |
| DELETE | `/api/department/delete/<id>/` | Delete department |

---

### Important Notes

**Department Management:**
- Departments are linked to organizations through the `orgId` field
- Department codes (`deptCode`) must be unique across the entire system
- When an organization is deleted, all its departments are automatically deleted (CASCADE)
- Only PUT method is supported for updates (no PATCH support)

**Data Validation:**
- All fields are required for department creation and updates
- Department codes must be unique system-wide
- Organization ID must reference an existing organization
- Status must be either "Active" or "Inactive"

---

## Shift Management

Base URL: `/api/shifts/`

### Shift Management Overview

The Shift management system provides comprehensive functionality for managing employee work shifts with time-based configurations. It supports different shift types with automatic late mark time calculation and IST timezone support.

---

### Shift CRUD Operations

#### 1. Create Shift

Creates a new shift with time configurations.

**Endpoint:** `POST /api/shifts/create/`

**Request Body:**
```json
{
  "shiftType": "string",
  "fromTime": "HH:MM:SS",
  "endTime": "HH:MM:SS",
  "lateMarkTime": "HH:MM:SS"
}
```

**Field Requirements:**
- `shiftType`: Required, choices: "Day", "Night", "Rotational", "Afternoon"
- `fromTime`: Required, format: "HH:MM:SS" in 24-hour IST (e.g., "09:00:00")
- `endTime`: Required, format: "HH:MM:SS" in 24-hour IST (e.g., "18:00:00")
- `lateMarkTime`: Optional, format: "HH:MM:SS" (auto-calculated if not provided)

**Automatic Late Mark Time Calculation:**
- **Day Shift**: 10:30:00 (10:30 AM)
- **Night Shift**: 22:30:00 (10:30 PM)
- **Afternoon Shift**: 15:30:00 (3:30 PM)
- **Rotational Shift**: fromTime + 2 hours + 30 minutes

**Response:**

**Success (201 Created):**
```json
{
  "id": "shift_id",
  "shiftType": "Day",
  "fromTime": "09:00:00",
  "endTime": "18:00:00",
  "lateMarkTime": "10:30:00"
}
```

**Error (400 Bad Request):**
```json
{
  "field_name": ["Error message"]
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/shifts/create/" \
  -H "Content-Type: application/json" \
  -d '{
    "shiftType": "Day",
    "fromTime": "09:00:00",
    "endTime": "18:00:00"
  }'
```

**Permissions:** HR, Admin

---

#### 2. List Shifts

Retrieves all shifts in the system.

**Endpoint:** `GET /api/shifts/fetch/`

**Response:**

**Success (200 OK):**
```json
[
  {
    "id": "shift_id_1",
    "shiftType": "Day",
    "fromTime": "09:00:00",
    "endTime": "18:00:00",
    "lateMarkTime": "10:30:00"
  },
  {
    "id": "shift_id_2",
    "shiftType": "Night",
    "fromTime": "21:00:00",
    "endTime": "06:00:00",
    "lateMarkTime": "22:30:00"
  },
  {
    "id": "shift_id_3",
    "shiftType": "Afternoon",
    "fromTime": "14:00:00",
    "endTime": "23:00:00",
    "lateMarkTime": "15:30:00"
  }
]
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/shifts/fetch/"
```

**Permissions:** HR, Admin

---

#### 3. Get Shift by ID

Retrieves a specific shift by its ID.

**Endpoint:** `GET /api/shifts/fetch/<str:pk>/`

**Path Parameters:**
- `pk`: Shift ID (string)

**Response:**

**Success (200 OK):**
```json
{
  "id": "shift_id",
  "shiftType": "Day",
  "fromTime": "09:00:00",
  "endTime": "18:00:00",
  "lateMarkTime": "10:30:00"
}
```

**Error (404 Not Found):**
```json
{
  "error": "Shift not found"
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/shifts/fetch/shift_id/"
```

**Permissions:** HR, Admin

---

#### 4. Update Shift

Updates an existing shift configuration.

**Endpoint:** `PUT /api/shifts/update/<str:pk>/`

**Path Parameters:**
- `pk`: Shift ID (string)

**Request Body:**
```json
{
  "shiftType": "Afternoon",
  "fromTime": "14:00:00",
  "endTime": "23:00:00",
  "lateMarkTime": "15:30:00"
}
```

**Response:**

**Success (200 OK):**
```json
{
  "id": "shift_id",
  "shiftType": "Afternoon",
  "fromTime": "14:00:00",
  "endTime": "23:00:00",
  "lateMarkTime": "15:30:00"
}
```

**Error (404 Not Found):**
```json
{
  "error": "Shift not found"
}
```

**Error (400 Bad Request):**
```json
{
  "field_name": ["Validation error message"]
}
```

**Example Request:**
```bash
curl -X PUT "http://localhost:8000/api/shifts/update/shift_id/" \
  -H "Content-Type: application/json" \
  -d '{
    "shiftType": "Afternoon",
    "fromTime": "14:00:00",
    "endTime": "23:00:00"
  }'
```

**Permissions:** HR, Admin

---

#### 5. Delete Shift

Deletes a shift from the system.

**Endpoint:** `DELETE /api/shifts/delete/<str:pk>/`

**Path Parameters:**
- `pk`: Shift ID (string)

**Response:**

**Success (204 No Content):**
```
(Empty response body)
```

**Error (404 Not Found):**
```json
{
  "error": "Shift not found"
}
```

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/api/shifts/delete/shift_id/"
```

**Permissions:** HR, Admin

---

### Shift Data Model

The Shift model uses MongoDB with string-based time storage:

```python
class Shift(Document):
    shiftType = StringField(required=True, choices=["Day", "Night", "Rotational", "Afternoon"])
    fromTime = StringField(required=True)    # "HH:MM:SS" format
    endTime = StringField(required=True)     # "HH:MM:SS" format
    lateMarkTime = StringField()             # "HH:MM:SS" format
```

**Database Configuration:**
- Collection: `shifts`
- Indexes: `shiftType`, unique compound index on `fromTime` and `endTime`

**Time Format:**
- All times stored as strings in "HH:MM:SS" format (24-hour IST)
- Examples: "09:00:00" (9:00 AM), "18:00:00" (6:00 PM), "22:30:00" (10:30 PM)

**Helper Methods:**
- `get_from_time_obj()`: Converts fromTime string to time object
- `get_end_time_obj()`: Converts endTime string to time object  
- `get_late_mark_time_obj()`: Converts lateMarkTime string to time object

---

### Shift Types and Default Configurations

#### Day Shift
- **Typical Hours**: 09:00:00 - 18:00:00
- **Default Late Mark**: 10:30:00 (1.5 hours after start)
- **Use Case**: Standard business hours

#### Night Shift  
- **Typical Hours**: 21:00:00 - 06:00:00 (next day)
- **Default Late Mark**: 22:30:00 (1.5 hours after start)
- **Use Case**: 24/7 operations, customer support

#### Afternoon Shift
- **Typical Hours**: 14:00:00 - 23:00:00
- **Default Late Mark**: 15:30:00 (1.5 hours after start)
- **Use Case**: Extended business hours, retail

#### Rotational Shift
- **Flexible Hours**: Configurable start and end times
- **Dynamic Late Mark**: Start time + 2.5 hours
- **Use Case**: Rotating schedules, multiple time zones

---

### Shift API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/shifts/create/` | Create new shift |
| GET | `/api/shifts/fetch/` | List all shifts |
| GET | `/api/shifts/fetch/<id>/` | Get shift by ID |
| PUT | `/api/shifts/update/<id>/` | Update shift |
| DELETE | `/api/shifts/delete/<id>/` | Delete shift |

---

### Important Notes

**Shift Management:**
- All shift operations require HR or Admin permissions
- Times are stored and processed in IST (Indian Standard Time)
- Automatic late mark time calculation based on shift type
- Unique constraint on fromTime and endTime combination prevents duplicate shifts

**Time Handling:**
- All times use 24-hour format (HH:MM:SS)
- String-based storage for consistent timezone handling
- Helper methods available for time object conversion
- Automatic validation of time format

**Business Logic:**
- Late mark times are automatically calculated if not provided
- Different shift types have different default late mark rules
- Rotational shifts have dynamic late mark calculation
- Time validation ensures proper format and logical sequences

**Integration:**
- Shifts are referenced by Employee model for attendance tracking
- Used in attendance check-in/check-out logic for late marking
- Essential for payroll and working hours calculation
- Supports multiple shift patterns for diverse business needs

---

## Employee Management

Base URL: `/api/employee/`

### Employee API Features

The Employee management system provides three main functionalities:
1. **Employee CRUD Operations** - Create, Read, Update, Delete employees
2. **Authentication & Authorization** - Login, logout, password management
3. **Attendance Management** - Check-in/out, attendance tracking, validation

---

### Employee CRUD Operations

#### 1. Create Employee

Creates a new employee with document uploads support.

**Endpoint:** `POST /api/employee/create/`

**Content-Type:** `multipart/form-data`

**Request Body:**
```json
{
  "firstName": "string",
  "middleName": "string",
  "lastName": "string",
  "location": "string",
  "email": "email",
  "password": "string",
  "mobileNumber": "string",
  "gender": "string",
  "dob": "YYYY-MM-DD",
  "doj": "YYYY-MM-DD",
  "status": "string",
  "role": "string",
  "reportingManager": "employee_id",
  "organizationId": "organization_id",
  "departmentId": "department_id",
  "designationId": "string",
  "shiftId": "shift_id",
  "currentAddress": {
    "street": "string",
    "city": "string",
    "state": "string",
    "zip": "string",
    "country": "string"
  },
  "permanentAddress": {
    "street": "string",
    "city": "string",
    "state": "string",
    "zip": "string",
    "country": "string"
  },
  "documents": {
    "adharCard": "file",
    "panCard": "file",
    "bankBook": "file",
    "xStandardMarksheet": "file",
    "xiiStandardMarksheet": "file",
    "degree": "file",
    "experienceLetter": "file",
    "photo": "file"
  }
}
```

**Field Requirements:**
- `firstName`, `lastName`: Required, max 100 characters
- `email`: Required, unique, valid email format
- `mobileNumber`: Required, exactly 10 digits
- `gender`: Required, choices: "male", "female", "other"
- `dob`, `doj`: Required, date format YYYY-MM-DD
- `status`: Required, choices: "active", "inactive"
- `role`: Required, choices: "admin", "hr", "JR_employee", "SR_employee"
- `organizationId`, `departmentId`, `shiftId`: Required references
- `currentAddress`, `permanentAddress`: Required embedded documents

**Response:**

**Success (201 Created):**
```json
{
  "success": true,
  "message": "Employee created successfully",
  "employeeId": "employee_id",
  "documents": {
    "adharCard": "http://localhost:8000/media/documents/adhar/filename.pdf",
    "photo": datetime": "27-12-2024 06:30 PM",
  "total_work_hours": 9.0,
  "work_duration": "9 hours 0 minutes",
  "timezone": "Asia/Kolkata (IST)",
  "is_completed": true,
  "location_details": {
    "address": "Wakad, Pune",
    "latitude": 18.5204,
    "longitude": 73.8567,
    "accuracy": 10
  }
}
```

**Error (400 Bad Request):**
```json
{
  "error": "No check-in record found for today. Please check-in first."
}
```

**Permissions:** Authenticated users

#### 3. Today's Attendance
**Endpoint:** `GET /api/employee/Attendance/today/`

**Response (200 OK):**
```json
{
  "date": "2024-12-27",
  "present_count": 45,
  "absent_count": 3,
  "half_day_count": 2,
  "late_count": 8,
  "on_time_count": 37,
  "date_display": "27-12-2024",
  "count": 50
}
```

**Permissions:** HR, Admin

#### 4. Employee Attendance List
**Endpoint:** `GET /api/employee/Attendance/<str:pk>/`

**Path Parameters:**
- `pk`: Employee ID (string)

**Query Parameters:**
- `page`: Page number (optional)
- `date`: Specific date filter (YYYY-MM-DD)
- `month`: Month filter (1-12)
- `year`: Year filter (YYYY)
- `status`: Status filter (present, absent, half_day, etc.)

**Response (200 OK):**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/employee/Attendance/emp_id/?page=2",
  "previous": null,
  "results": [
    {
      "id": "attendance_id",
      "employee": "employee_id",
      "date": "2024-12-27",
      "check_in_time": "09:30:00",
      "check_out_time": "18:30:00",
      "total_work_hours": 9.0,
      "status": "present",
      "is_late": false,
      "is_valid": true,
      "check_in_location": "Wakad, Pune",
      "check_out_location": "Wakad, Pune"
    }
  ]
}
```

**Permissions:** All authenticated users

#### 5. Overall Attendance List
**Endpoint:** `GET /api/employee/Attendance/overall/`

**Query Parameters:**
- `page`: Page number (optional)
- `date`: Specific date filter (YYYY-MM-DD)
- `month`: Month filter (1-12)
- `year`: Year filter (YYYY)
- `status`: Status filter

**Response:** Same format as Employee Attendance List

**Permissions:** HR, Admin

#### 6. Mark Single Attendance
**Endpoint:** `POST /api/employee/Attendance/mark/<str:pk>/`

**Path Parameters:**
- `pk`: Attendance record ID (string)

**Response (200 OK):**
```json
{
  "message": "Attendance marked as present"
}
```

**Error (400 Bad Request):**
```json
{
  "message": "Attendance already validated for 2024-12-27 for employee John"
}
```

**Permissions:** HR, Admin

#### 7. Mark All Attendance
**Endpoint:** `POST /api/employee/Attendance/allmark/`

**Query Parameters:**
- `date`: Specific date (YYYY-MM-DD)
- `month`: Month (1-12)
- `year`: Year (YYYY)

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "message": "Successfully validated attendance for today (2024-12-27)",
  "data": {
    "total_records": 50,
    "newly_validated": 15,
    "already_validated": 35,
    "filter_applied": "today (2024-12-27)"
  }
}
```

**Permissions:** HR, Admin

### Data Model
```python
class Attendance(Document):
    employee = ReferenceField(Employee, required=True)
    date = StringField(required=True)  # "YYYY-MM-DD"
    check_in_time = StringField()      # "HH:MM:SS"
    check_out_time = StringField()     # "HH:MM:SS"
    is_valid = BooleanField(default=False)
    is_late = BooleanField(default=False)
    total_work_hours = FloatField()
    status = StringField(choices=["present", "latemark", "pending", "absent", "WFH", "half_day", "on_leave"])
    check_in_location = StringField()
    check_out_location = StringField()
```

### Endpoints Summary
| Method | Endpoint | Description | Permissions |
|--------|----------|-------------|-------------|
| POST | `/api/employee/checkin/` | Employee check-in | Authenticated |
| POST | `/api/employee/checkout/` | Employee check-out | Authenticated |
| GET | `/api/employee/Attendance/today/` | Today's attendance summary | HR, Admin |
| GET | `/api/employee/Attendance/overall/` | Overall attendance list | HR, Admin |
| GET | `/api/employee/Attendance/<id>/` | Employee attendance list | All authenticated |
| POST | `/api/employee/Attendance/mark/<id>/` | Mark single attendance | HR, Admin |
| POST | `/api/employee/Attendance/allmark/` | Mark all attendance | HR, Admin |

**Important Notes:**
- Location-based check-in/out with GPS coordinates
- Automatic late marking based on shift timings
- Work hours calculation and status determination
- Bulk attendance validation for HR/Admin
- IST timezone support with string-based datetime storage

---

## Leave Management

**Base URL:** `/api/leave/`

### Overview
Leave management provides comprehensive leave request functionality with role-based access, multi-level approval workflow, and automatic balance management.

### API Endpoints

#### 1. Get Leave Requests (Role-Based)
**Endpoint:** `GET /api/leave/leaverequest/`

**Role-Based Access:**
- **HR/Admin**: See all leave requests
- **SR_employee**: See own + team's leave requests (where they are reporting manager)
- **JR_employee**: See only own leave requests

**Response (200 OK):**
```json
{
  "message": "All Employees Leave Requests",
  "role": "hr",
  "count": 25,
  "reporting_managers": [
    {
      "id": "manager_id",
      "firstName": "Jane",
      "lastName": "Smith"
    }
  ],
  "result": [
    {
      "id": "leave_request_id",
      "employee": "employee_id",
      "employee_name": "John Doe",
      "employee_department": "IT Department",
      "leave_type": "PL",
      "start_date": "2024-12-28",
      "end_date": "2024-12-30",
      "total_days": 3.0,
      "reason": "Family vacation",
      "status": "PENDING",
      "applied_date": "2024-12-27 10:30:00",
      "is_planned": true,
      "is_emergency": false,
      "is_on_probation": false,
      "has_sufficient_balance": true,
      "reporting_manager": "manager_id",
      "current_approver": "manager_id"
    }
  ]
}
```

**Permissions:** All authenticated users (role-based filtering)

#### 2. Create Leave Request
**Endpoint:** `POST /api/leave/leaverequest/`

**Request Body:**
```json
{
  "leave_type": "PL",
  "start_date": "2024-12-28",
  "end_date": "2024-12-30",
  "reason": "Family vacation",
  "is_planned": true,
  "is_emergency": false
}
```

**Field Requirements:**
- `leave_type`: Required, choices: "PL" (Paid Leave), "SPL" (Special Leave), "UPL" (Unpaid Leave), "SL" (Sick Leave)
- `start_date`, `end_date`: Required, format: "YYYY-MM-DD"
- `reason`: Required, description of leave purpose
- `is_planned`: Boolean, indicates if leave requires advance notice
- `is_emergency`: Boolean, indicates emergency leave (no notice required)

**Response (201 Created):**
```json
{
  "message": "Leave request created successfully",
  "request_id": "leave_request_id",
  "status": "PENDING",
  "details": {
    "id": "leave_request_id",
    "employee_name": "John Doe",
    "leave_type": "PL",
    "start_date": "2024-12-28",
    "end_date": "2024-12-30",
    "total_days": 3.0,
    "reason": "Family vacation",
    "status": "PENDING",
    "applied_date": "2024-12-27 10:30:00"
  }
}
```

**Permissions:** All authenticated users

#### 3. Get Employee Leave Requests
**Endpoint:** `GET /api/leave/leaverequest/<str:pk>/`

**Path Parameters:**
- `pk`: Employee ID (string)

**Response (200 OK):**
```json
{
  "message": "Leave Requests for John Doe",
  "count": 5,
  "reporting_managers": [
    {
      "id": "manager_id",
      "firstName": "Jane",
      "lastName": "Smith"
    }
  ],
  "result": [
    {
      "id": "leave_request_id",
      "leave_type": "PL",
      "start_date": "2024-12-28",
      "end_date": "2024-12-30",
      "total_days": 3.0,
      "reason": "Family vacation",
      "status": "APPROVED",
      "approved_by": "manager_id",
      "approved_date": "2024-12-27 14:30:00"
    }
  ]
}
```

**Permissions:** All authenticated users

#### 4. Update Leave Request
**Endpoint:** `PUT /api/leave/leaverequest/<str:pk>/`

**Path Parameters:**
- `pk`: Leave Request ID (string)

**Request Body:** Same as create leave request (partial updates supported)

**Response (200 OK):**
```json
{
  "message": "Leave Request updated successfully",
  "data": {
    "id": "leave_request_id",
    "leave_type": "SPL",
    "start_date": "2024-12-28",
    "end_date": "2024-12-29",
    "total_days": 2.0,
    "reason": "Updated reason",
    "status": "PENDING"
  }
}
```

**Error (400 Bad Request):**
```json
{
  "message": "Your Leave-Request is now APPROVED, you can't modify"
}
```

**Permissions:** All authenticated users (own requests only)

#### 5. Delete Leave Request
**Endpoint:** `DELETE /api/leave/leaverequest/<str:pk>/`

**Path Parameters:**
- `pk`: Leave Request ID (string)

**Response (204 No Content):**
```json
{
  "message": "Leave Request Deleted Successfully"
}
```

**Error (400 Bad Request):**
```json
{
  "error": "Cannot delete an approved leave request. Please contact HR."
}
```

**Permissions:** All authenticated users (own requests only)

#### 6. Approve Leave Request
**Endpoint:** `POST /api/leave/leaverequest/approve/<str:pk>/`

**Path Parameters:**
- `pk`: Leave Request ID (string)

**Approval Logic:**
- **Paid Leave (PL/SL)**: Deducted from earned leave balance
- **Special Leave (SPL)**: Deducted from special leave balance  
- **Unpaid Leave (UPL)**: No balance deduction
- **Probation Check**: Only UPL allowed for probationary employees
- **Notice Period**: Validates advance notice for planned leaves
- **Balance Check**: Ensures sufficient leave balance

**Response (200 OK):**
```json
{
  "message": "Leave request approved successfully",
  "leave_id": "leave_request_id",
  "status": "APPROVED",
  "approved_by": "Jane Smith",
  "approved_date": "27-12-2024 02:30 PM",
  "employee": {
    "id": "employee_id",
    "name": "John Doe",
    "previous_balance": {
      "earned_leave": 18,
      "special_leave": 1
    },
    "remaining_balance": {
      "earned_leave": 15,
      "special_leave": 1
    },
    "policy_details": {
      "policy_name": "Annual Leave Policy",
      "earned_leave_monthly": 1.5,
      "planned_notice_days": 10,
      "regular_notice_days": 2,
      "probation_days": 90,
      "leave_year_start": 1,
      "leave_year_end": 12,
      "is_active": true
    }
  },
  "leave_details": {
    "type": "PL",
    "days": 3.0,
    "start_date": "28-12-2024",
    "end_date": "30-12-2024",
    "reason": "Family vacation",
    "is_planned": true,
    "is_emergency": false
  }
}
```

**Error (400 Bad Request):**
```json
{
  "message": "Insufficient earned leave balance. Available: 2 days, Requested: 3 days"
}
```

**Permissions:** Admin, HR, SR_employee (reporting managers)

#### 7. Reject Leave Request
**Endpoint:** `POST /api/leave/leaverequest/reject/<str:pk>/`

**Path Parameters:**
- `pk`: Leave Request ID (string)

**Request Body:**
```json
{
  "reason": "Insufficient staffing during requested period"
}
```

**Response (200 OK):**
```json
{
  "message": "Leave Request Rejected Successfully",
  "details": {
    "rejected_by": "Jane Smith",
    "rejection_reason": "Insufficient staffing during requested period",
    "rejected_date": "27-12-2024 02:45 PM",
    "employee_name": "John Doe",
    "leave_dates": "28-12-2024 to 30-12-2024",
    "leave_type": "PL",
    "total_days": 3.0
  }
}
```

**Error (403 Forbidden):**
```json
{
  "error": "JR_employee - John doesn't have permission to reject this leave request"
}
```

**Permissions:** Admin, HR, SR_employee (reporting managers)

### Data Model
```python
class LeaveRequest(Document):
    employee = ReferenceField('Employee')
    employee_name = StringField()
    employee_department = StringField()
    reporting_manager = ReferenceField('Employee')
    
    leave_type = StringField(choices=['PL', 'SPL', 'UPL', 'SL'], required=True)
    start_date = StringField(required=True)  # "YYYY-MM-DD"
    end_date = StringField(required=True)    # "YYYY-MM-DD"
    total_days = FloatField(default=0.0)
    reason = StringField(required=True)
    
    status = StringField(choices=['PENDING', 'APPROVED', 'CANCELLED', 'REJECTED'], default='PENDING')
    applied_date = StringField()  # "YYYY-MM-DD HH:MM:SS"
    is_planned = BooleanField(default=False)
    is_emergency = BooleanField(default=False)
    is_on_probation = BooleanField(default=False)
    has_sufficient_balance = BooleanField(default=True)
```

### Endpoints Summary
| Method | Endpoint | Description | Permissions |
|--------|----------|-------------|-------------|
| GET | `/api/leave/leaverequest/` | Get leave requests (role-based) | All authenticated |
| POST | `/api/leave/leaverequest/` | Create leave request | All authenticated |
| GET | `/api/leave/leaverequest/<id>/` | Get employee leave requests | All authenticated |
| PUT | `/api/leave/leaverequest/<id>/` | Update leave request | All authenticated |
| DELETE | `/api/leave/leaverequest/<id>/` | Delete leave request | All authenticated |
| POST | `/api/leave/leaverequest/approve/<id>/` | Approve leave request | Admin, HR, SR_employee |
| POST | `/api/leave/leaverequest/reject/<id>/` | Reject leave request | Admin, HR, SR_employee |

**Important Notes:**
- Role-based access control with different views for HR, SR_employee, and JR_employee
- Automatic balance deduction upon leave approval
- Probation period validation - only unpaid leave allowed during probation
- Notice period enforcement for planned leaves
- Attendance record creation for approved leave periods

---

## Work From Home (WFH)

**Base URL:** `/api/leave/`

### Overview
Work From Home management provides simple request/approval workflow for remote work requests with date range support and reporting manager integration.

### API Endpoints

#### 1. Get All WFH Requests
**Endpoint:** `GET /api/leave/wfh/`

**Response (200 OK):**
```json
{
  "message": "All Work From Home Requests",
  "count": 10,
  "result": [
    {
      "id": "wfh_request_id",
      "employee": "employee_id",
      "start_date": "2024-12-28",
      "end_date": "2024-12-28",
      "total_days": 1.0,
      "reason": "Internet connectivity issues at office",
      "status": "pending",
      "applied_date": "2024-12-27 09:00:00",
      "reporting_manager": "manager_id"
    }
  ]
}
```

**Permissions:** All authenticated users

#### 2. Create WFH Request
**Endpoint:** `POST /api/leave/wfh/`

**Request Body:**
```json
{
  "start_date": "2024-12-28",
  "end_date": "2024-12-28",
  "reason": "Internet connectivity issues at office"
}
```

**Response (201 Created):**
```json
{
  "message": "Work From Home request created successfully",
  "request_id": "wfh_request_id",
  "status": "pending",
  "details": {
    "id": "wfh_request_id",
    "start_date": "2024-12-28",
    "end_date": "2024-12-28",
    "total_days": 1.0,
    "reason": "Internet connectivity issues at office",
    "status": "pending",
    "applied_date": "2024-12-27 09:00:00"
  }
}
```

**Permissions:** All authenticated users

#### 3. Get Employee WFH Requests
**Endpoint:** `GET /api/leave/wfh/<str:pk>/`

**Path Parameters:**
- `pk`: Employee ID (string)

**Response:** Same format as Get All WFH Requests

**Permissions:** All authenticated users

#### 4. Update WFH Request
**Endpoint:** `PUT /api/leave/wfh/<str:pk>/`

**Path Parameters:**
- `pk`: WFH Request ID (string)

**Request Body:** Same as create WFH request (partial updates supported)

**Response (200 OK):**
```json
{
  "message": "WFH Request updated successfully",
  "data": {
    "id": "wfh_request_id",
    "start_date": "2024-12-29",
    "end_date": "2024-12-29",
    "reason": "Updated reason for WFH",
    "status": "pending"
  }
}
```

**Permissions:** All authenticated users (own requests only)

#### 5. Delete WFH Request
**Endpoint:** `DELETE /api/leave/wfh/<str:pk>/`

**Path Parameters:**
- `pk`: WFH Request ID (string)

**Response (204 No Content):**
```json
{
  "message": "WFH Request Deleted Successfully"
}
```

**Permissions:** All authenticated users (own requests only)

### Data Model
```python
class WFH(Document):
    employee = ReferenceField('Employee', required=True)
    start_date = StringField(required=True)  # "YYYY-MM-DD"
    end_date = StringField(required=True)    # "YYYY-MM-DD"
    total_days = FloatField(default=0.0)
    reason = StringField(required=True)
    reporting_manager = ReferenceField('Employee')
    status = StringField(choices=['pending', 'approved', 'rejected'], default='pending')
```

### Endpoints Summary
| Method | Endpoint | Description | Permissions |
|--------|----------|-------------|-------------|
| GET | `/api/leave/wfh/` | Get all WFH requests | All authenticated |
| POST | `/api/leave/wfh/` | Create WFH request | All authenticated |
| GET | `/api/leave/wfh/<id>/` | Get employee WFH requests | All authenticated |
| PUT | `/api/leave/wfh/<id>/` | Update WFH request | All authenticated |
| DELETE | `/api/leave/wfh/<id>/` | Delete WFH request | All authenticated |

**Important Notes:**
- Simple request/approval workflow similar to leave requests
- Date range support for multi-day WFH requests
- Reporting manager assignment for approval routing

---

## Holiday Management

**Base URL:** `/api/leave/`

### Overview
Holiday management provides comprehensive holiday calendar functionality with multiple holiday types, department/location-specific applicability, and bulk upload capabilities.

### API Endpoints

#### 1. List/Create Holidays
**Get Holidays:** `GET /api/leave/holidays/`
**Create Holiday:** `POST /api/leave/holidays/`

**Query Parameters (GET):**
- `year`: Filter by year (default: current year)
- `type`: Filter by holiday type (NATIONAL, REGIONAL, COMPANY, OPTIONAL, RESTRICTED)
- `is_active`: Filter active holidays (default: true)
- `month`: Filter by month (1-12)

**GET Response (200 OK):**
```json
{
  "success": true,
  "count": 15,
  "holidays": [
    {
      "id": "holiday_id",
      "name": "New Year's Day",
      "date": "2024-01-01",
      "holiday_type": "NATIONAL",
      "description": "New Year celebration",
      "is_active": true,
      "year": 2024,
      "applicable_departments": [],
      "applicable_locations": [],
      "is_optional": false,
      "max_optional_selections": 0,
      "created_at": "2024-12-01 10:00:00"
    }
  ]
}
```

**POST Request Body:**
```json
{
  "name": "Independence Day",
  "date": "2024-08-15",
  "holiday_type": "NATIONAL",
  "description": "India Independence Day",
  "is_active": true,
  "applicable_departments": [],
  "applicable_locations": [],
  "is_optional": false,
  "max_optional_selections": 0
}
```

**POST Response (201 Created):**
```json
{
  "success": true,
  "message": "Holiday created successfully",
  "holiday": {
    "id": "holiday_id",
    "name": "Independence Day",
    "date": "2024-08-15",
    "holiday_type": "NATIONAL",
    "year": 2024
  }
}
```

**Permissions:** 
- GET: All authenticated users
- POST: HR, Admin only

#### 2. Holiday Details
**Get/Update/Delete Holiday:** `GET|PUT|DELETE /api/leave/holidays/<str:holiday_id>/`

**GET Response (200 OK):**
```json
{
  "success": true,
  "holiday": {
    "id": "holiday_id",
    "name": "Independence Day",
    "date": "2024-08-15",
    "holiday_type": "NATIONAL",
    "description": "India Independence Day",
    "is_active": true,
    "year": 2024
  }
}
```

**PUT Request Body:** Same as create holiday (partial updates supported)

**DELETE Response (200 OK):**
```json
{
  "success": true,
  "message": "Holiday \"Independence Day\" deleted successfully"
}
```

**Permissions:**
- GET: All authenticated users
- PUT/DELETE: HR, Admin only

#### 3. Calendar Holidays
**Endpoint:** `GET /api/leave/calendar/holidays/`

**Query Parameters:**
- `year`: Filter by year (default: current year)
- `month`: Filter by month (1-12)

**Response (200 OK):**
```json
{
  "success": true,
  "count": 8,
  "events": [
    {
      "id": "holiday_id",
      "title": "New Year's Day",
      "date": "2024-01-01",
      "type": "holiday",
      "holiday_type": "NATIONAL",
      "description": "New Year celebration",
      "is_optional": false,
      "color": "#FF5252"
    }
  ]
}
```

**Color Codes:**
- NATIONAL: #FF5252 (Red)
- REGIONAL: #FF9800 (Orange)
- COMPANY: #2196F3 (Blue)
- OPTIONAL: #4CAF50 (Green)
- RESTRICTED: #9E9E9E (Grey)

**Permissions:** All authenticated users

#### 4. Bulk Holiday Upload
**Endpoint:** `POST /api/leave/holidays/bulk-upload/`

**Request Body:**
```json
{
  "holidays": [
    {
      "name": "Republic Day",
      "date": "2024-01-26",
      "holiday_type": "NATIONAL",
      "description": "India Republic Day"
    },
    {
      "name": "Holi",
      "date": "2024-03-25",
      "holiday_type": "NATIONAL",
      "description": "Festival of Colors"
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "created_count": 2,
  "error_count": 0,
  "holidays": [
    {
      "id": "holiday_id_1",
      "name": "Republic Day",
      "date": "2024-01-26",
      "holiday_type": "NATIONAL"
    },
    {
      "id": "holiday_id_2",
      "name": "Holi",
      "date": "2024-03-25",
      "holiday_type": "NATIONAL"
    }
  ],
  "errors": []
}
```

**Permissions:** HR, Admin only

### Data Model
```python
class Holiday(Document):
    name = StringField(required=True, max_length=200)
    date = StringField(required=True)  # "YYYY-MM-DD"
    holiday_type = StringField(choices=['NATIONAL', 'REGIONAL', 'COMPANY', 'OPTIONAL', 'RESTRICTED'])
    description = StringField(max_length=500)
    is_active = BooleanField(default=True)
    year = IntField(required=True)
    applicable_departments = ListField(StringField())
    applicable_locations = ListField(StringField())
    is_optional = BooleanField(default=False)
    max_optional_selections = IntField(default=0)
```

### Endpoints Summary
| Method | Endpoint | Description | Permissions |
|--------|----------|-------------|-------------|
| GET | `/api/leave/holidays/` | List holidays | All authenticated |
| POST | `/api/leave/holidays/` | Create holiday | HR, Admin |
| GET | `/api/leave/holidays/<id>/` | Get holiday details | All authenticated |
| PUT | `/api/leave/holidays/<id>/` | Update holiday | HR, Admin |
| DELETE | `/api/leave/holidays/<id>/` | Delete holiday | HR, Admin |
| GET | `/api/leave/calendar/holidays/` | Calendar holidays | All authenticated |
| POST | `/api/leave/holidays/bulk-upload/` | Bulk upload holidays | HR, Admin |

**Important Notes:**
- Multiple holiday types (National, Regional, Company, Optional, Restricted)
- Department/location-specific holiday applicability
- Calendar integration with color-coded display
- Bulk upload capability for efficient holiday setup
- Year-based organization with filtering options

---

## API Summary

### Base URLs
- **Organization:** `/api/organization/`
- **Department:** `/api/department/`
- **Shift:** `/api/shifts/`
- **Employee:** `/api/employee/`
- **Leave/WFH/Holiday:** `/api/leave/`

### Permission Levels
- **Public:** No authentication required
- **Authenticated:** Valid JWT token required
- **HR/Admin:** HR or Admin role required
- **SR_employee:** Senior employee role (can manage team)
- **JR_employee:** Junior employee role (limited access)

### Key Features
- **Role-based access control** across all modules
- **JWT authentication** with token blacklisting
- **MongoDB integration** with proper indexing
- **IST timezone support** with string-based datetime storage
- **File upload support** for employee documents
- **Location-based attendance** tracking
- **Multi-level approval** workflows
- **Comprehensive filtering** and pagination
- **Bulk operations** for administrative efficiency
- **Audit trails** with timestamps and user tracking

---

*This documentation covers all HRMS API endpoints with complete request/response examples, data models, and business logic explanations.*e  
- **Unpaid Leave (UPL)**: No balance deduction
- **Probation Check**: Only UPL allowed for probationary employees
- **Notice Period**: Validates advance notice for planned leaves
- **Balance Check**: Ensures sufficient leave balance

**Response:**

**Success (200 OK):**
```json
{
  "message": "Leave request approved successfully",
  "leave_id": "leave_request_id",
  "status": "APPROVED",
  "approved_by": "Jane Smith",
  "approved_date": "27-12-2024 02:30 PM",
  "employee": {
    "id": "employee_id",
    "name": "John Doe",
    "previous_balance": {
      "earned_leave": 18,
      "special_leave": 1
    },
    "remaining_balance": {
      "earned_leave": 15,
      "special_leave": 1
    },
    "policy_details": {
      "policy_name": "Annual Leave Policy",
      "earned_leave_monthly": 1.5,
      "planned_notice_days": 10,
      "regular_notice_days": 2,
      "probation_days": 90,
      "leave_year_start": 1,
      "leave_year_end": 12,
      "is_active": true
    }
  },
  "leave_details": {
    "type": "PL",
    "days": 3.0,
    "start_date": "28-12-2024",
    "end_date": "30-12-2024",
    "reason": "Family vacation",
    "is_planned": true,
    "is_emergency": false
  }
}
```

**Error (400 Bad Request):**
```json
{
  "message": "Insufficient earned leave balance. Available: 2 days, Requested: 3 days"
}
```

**Permissions:** Admin, HR, SR_employee (reporting managers)

---

#### 2. Reject Leave Request

Rejects a leave request with a reason.

**Endpoint:** `POST /api/leave/leaverequest/reject/<str:pk>/`

**Path Parameters:**
- `pk`: Leave Request ID (string)

**Request Body:**
```json
{
  "reason": "Insufficient staffing during requested period"
}
```

**Response:**

**Success (200 OK):**
```json
{
  "message": "Leave Request Rejected Successfully",
  "details": {
    "rejected_by": "Jane Smith",
    "rejection_reason": "Insufficient staffing during requested period",
    "rejected_date": "27-12-2024 02:45 PM",
    "employee_name": "John Doe",
    "leave_dates": "28-12-2024 to 30-12-2024",
    "leave_type": "PL",
    "total_days": 3.0
  }
}
```

**Error (403 Forbidden):**
```json
{
  "error": "JR_employee - John doesn't have permission to reject this leave request"
}
```

**Permissions:** Admin, HR, SR_employee (reporting managers)

---

### Work From Home (WFH) Management

#### 1. Get All WFH Requests

Retrieves all WFH requests (admin view) or employee-specific requests.

**Endpoint:** `GET /api/leave/wfh/`

**Response:**

**Success (200 OK):**
```json
{
  "message": "All Work From Home Requests",
  "count": 10,
  "result": [
    {
      "id": "wfh_request_id",
      "employee": "employee_id",
      "start_date": "2024-12-28",
      "end_date": "2024-12-28",
      "total_days": 1.0,
      "reason": "Internet connectivity issues at office",
      "status": "pending",
      "applied_date": "2024-12-27 09:00:00",
      "reporting_manager": "manager_id"
    }
  ]
}
```

**Permissions:** All authenticated users

---

#### 2. Create WFH Request

Creates a new Work From Home request.

**Endpoint:** `POST /api/leave/wfh/`

**Request Body:**
```json
{
  "start_date": "2024-12-28",
  "end_date": "2024-12-28",
  "reason": "Internet connectivity issues at office"
}
```

**Response:**

**Success (201 Created):**
```json
{
  "message": "Work From Home request created successfully",
  "request_id": "wfh_request_id",
  "status": "pending",
  "details": {
    "id": "wfh_request_id",
    "start_date": "2024-12-28",
    "end_date": "2024-12-28",
    "total_days": 1.0,
    "reason": "Internet connectivity issues at office",
    "status": "pending",
    "applied_date": "2024-12-27 09:00:00"
  }
}
```

**Permissions:** All authenticated users

---

#### 3. Get Employee WFH Requests

Retrieves WFH requests for a specific employee.

**Endpoint:** `GET /api/leave/wfh/<str:pk>/`

**Path Parameters:**
- `pk`: Employee ID (string)

**Response:** Same format as Get All WFH Requests

**Permissions:** All authenticated users

---

#### 4. Update WFH Request

Updates an existing WFH request.

**Endpoint:** `PUT /api/leave/wfh/<str:pk>/`

**Path Parameters:**
- `pk`: WFH Request ID (string)

**Request Body:** Same as create WFH request (partial updates supported)

**Response:**

**Success (200 OK):**
```json
{
  "message": "WFH Request updated successfully",
  "data": {
    "id": "wfh_request_id",
    "start_date": "2024-12-29",
    "end_date": "2024-12-29",
    "reason": "Updated reason for WFH",
    "status": "pending"
  }
}
```

**Permissions:** All authenticated users (own requests only)

---

#### 5. Delete WFH Request

Deletes a WFH request.

**Endpoint:** `DELETE /api/leave/wfh/<str:pk>/`

**Path Parameters:**
- `pk`: WFH Request ID (string)

**Response:**

**Success (204 No Content):**
```json
{
  "message": "WFH Request Deleted Successfully"
}
```

**Permissions:** All authenticated users (own requests only)

---

### Holiday Management

#### 1. List/Create Holidays

**Get Holidays:** `GET /api/leave/holidays/`
**Create Holiday:** `POST /api/leave/holidays/`

**Query Parameters (GET):**
- `year`: Filter by year (default: current year)
- `type`: Filter by holiday type (NATIONAL, REGIONAL, COMPANY, OPTIONAL, RESTRICTED)
- `is_active`: Filter active holidays (default: true)
- `month`: Filter by month (1-12)

**GET Response:**

**Success (200 OK):**
```json
{
  "success": true,
  "count": 15,
  "holidays": [
    {
      "id": "holiday_id",
      "name": "New Year's Day",
      "date": "2024-01-01",
      "holiday_type": "NATIONAL",
      "description": "New Year celebration",
      "is_active": true,
      "year": 2024,
      "applicable_departments": [],
      "applicable_locations": [],
      "is_optional": false,
      "max_optional_selections": 0,
      "created_at": "2024-12-01 10:00:00"
    }
  ]
}
```

**POST Request Body:**
```json
{
  "name": "Independence Day",
  "date": "2024-08-15",
  "holiday_type": "NATIONAL",
  "description": "India Independence Day",
  "is_active": true,
  "applicable_departments": [],
  "applicable_locations": [],
  "is_optional": false,
  "max_optional_selections": 0
}
```

**POST Response:**

**Success (201 Created):**
```json
{
  "success": true,
  "message": "Holiday created successfully",
  "holiday": {
    "id": "holiday_id",
    "name": "Independence Day",
    "date": "2024-08-15",
    "holiday_type": "NATIONAL",
    "year": 2024
  }
}
```

**Permissions:** 
- GET: All authenticated users
- POST: HR, Admin only

---

#### 2. Holiday Details

**Get/Update/Delete Holiday:** `GET|PUT|DELETE /api/leave/holidays/<str:holiday_id>/`

**GET Response:**
```json
{
  "success": true,
  "holiday": {
    "id": "holiday_id",
    "name": "Independence Day",
    "date": "2024-08-15",
    "holiday_type": "NATIONAL",
    "description": "India Independence Day",
    "is_active": true,
    "year": 2024
  }
}
```

**PUT Request Body:** Same as create holiday (partial updates supported)

**DELETE Response:**
```json
{
  "success": true,
  "message": "Holiday \"Independence Day\" deleted successfully"
}
```

**Permissions:**
- GET: All authenticated users
- PUT/DELETE: HR, Admin only

---

#### 3. Calendar Holidays

Gets holidays formatted for calendar display.

**Endpoint:** `GET /api/leave/calendar/holidays/`

**Query Parameters:**
- `year`: Filter by year (default: current year)
- `month`: Filter by month (1-12)

**Response:**

**Success (200 OK):**
```json
{
  "success": true,
  "count": 8,
  "events": [
    {
      "id": "holiday_id",
      "title": "New Year's Day",
      "date": "2024-01-01",
      "type": "holiday",
      "holiday_type": "NATIONAL",
      "description": "New Year celebration",
      "is_optional": false,
      "color": "#FF5252"
    }
  ]
}
```

**Color Codes:**
- NATIONAL: #FF5252 (Red)
- REGIONAL: #FF9800 (Orange)
- COMPANY: #2196F3 (Blue)
- OPTIONAL: #4CAF50 (Green)
- RESTRICTED: #9E9E9E (Grey)

**Permissions:** All authenticated users

---

#### 4. Bulk Holiday Upload

Uploads multiple holidays at once.

**Endpoint:** `POST /api/leave/holidays/bulk-upload/`

**Request Body:**
```json
{
  "holidays": [
    {
      "name": "Republic Day",
      "date": "2024-01-26",
      "holiday_type": "NATIONAL",
      "description": "India Republic Day"
    },
    {
      "name": "Holi",
      "date": "2024-03-25",
      "holiday_type": "NATIONAL",
      "description": "Festival of Colors"
    }
  ]
}
```

**Response:**

**Success (201 Created):**
```json
{
  "success": true,
  "created_count": 2,
  "error_count": 0,
  "holidays": [
    {
      "id": "holiday_id_1",
      "name": "Republic Day",
      "date": "2024-01-26",
      "holiday_type": "NATIONAL"
    },
    {
      "id": "holiday_id_2",
      "name": "Holi",
      "date": "2024-03-25",
      "holiday_type": "NATIONAL"
    }
  ],
  "errors": []
}
```

**Permissions:** HR, Admin only

---

### Data Models

#### Leave Request Model
```python
class LeaveRequest(Document):
    employee = ReferenceField('Employee')
    employee_name = StringField()
    employee_department = StringField()
    reporting_manager = ReferenceField('Employee')
    
    leave_type = StringField(choices=['PL', 'SPL', 'UPL', 'SL'], required=True)
    start_date = StringField(required=True)  # "YYYY-MM-DD"
    end_date = StringField(required=True)    # "YYYY-MM-DD"
    total_days = FloatField(default=0.0)
    reason = StringField(required=True)
    
    status = StringField(choices=['PENDING', 'APPROVED', 'CANCELLED', 'REJECTED'], default='PENDING')
    applied_date = StringField()  # "YYYY-MM-DD HH:MM:SS"
    is_planned = BooleanField(default=False)
    is_emergency = BooleanField(default=False)
    is_on_probation = BooleanField(default=False)
    has_sufficient_balance = BooleanField(default=True)
```

#### WFH Model
```python
class WFH(Document):
    employee = ReferenceField('Employee', required=True)
    start_date = StringField(required=True)  # "YYYY-MM-DD"
    end_date = StringField(required=True)    # "YYYY-MM-DD"
    total_days = FloatField(default=0.0)
    reason = StringField(required=True)
    reporting_manager = ReferenceField('Employee')
    status = StringField(choices=['pending', 'approved', 'rejected'], default='pending')
```

#### Holiday Model
```python
class Holiday(Document):
    name = StringField(required=True, max_length=200)
    date = StringField(required=True)  # "YYYY-MM-DD"
    holiday_type = StringField(choices=['NATIONAL', 'REGIONAL', 'COMPANY', 'OPTIONAL', 'RESTRICTED'])
    description = StringField(max_length=500)
    is_active = BooleanField(default=True)
    year = IntField(required=True)
    applicable_departments = ListField(StringField())
    applicable_locations = ListField(StringField())
    is_optional = BooleanField(default=False)
    max_optional_selections = IntField(default=0)
```

---

### Leave Management API Endpoints Summary

| Method | Endpoint | Description | Permissions |
|--------|----------|-------------|-------------|
| **Leave Requests** |
| GET | `/api/leave/leaverequest/` | Get leave requests (role-based) | All authenticated |
| POST | `/api/leave/leaverequest/` | Create leave request | All authenticated |
| GET | `/api/leave/leaverequest/<id>/` | Get employee leave requests | All authenticated |
| PUT | `/api/leave/leaverequest/<id>/` | Update leave request | All authenticated |
| DELETE | `/api/leave/leaverequest/<id>/` | Delete leave request | All authenticated |
| **Leave Approval** |
| POST | `/api/leave/leaverequest/approve/<id>/` | Approve leave request | Admin, HR, SR_employee |
| POST | `/api/leave/leaverequest/reject/<id>/` | Reject leave request | Admin, HR, SR_employee |
| **Work From Home** |
| GET | `/api/leave/wfh/` | Get all WFH requests | All authenticated |
| POST | `/api/leave/wfh/` | Create WFH request | All authenticated |
| GET | `/api/leave/wfh/<id>/` | Get employee WFH requests | All authenticated |
| PUT | `/api/leave/wfh/<id>/` | Update WFH request | All authenticated |
| DELETE | `/api/leave/wfh/<id>/` | Delete WFH request | All authenticated |
| **Holiday Management** |
| GET | `/api/leave/holidays/` | List holidays | All authenticated |
| POST | `/api/leave/holidays/` | Create holiday | HR, Admin |
| GET | `/api/leave/holidays/<id>/` | Get holiday details | All authenticated |
| PUT | `/api/leave/holidays/<id>/` | Update holiday | HR, Admin |
| DELETE | `/api/leave/holidays/<id>/` | Delete holiday | HR, Admin |
| GET | `/api/leave/calendar/holidays/` | Calendar holidays | All authenticated |
| POST | `/api/leave/holidays/bulk-upload/` | Bulk upload holidays | HR, Admin |

---

### Important Notes

**Leave Management:**
- **Role-based access control** with different views for HR, SR_employee, and JR_employee
- **Automatic balance deduction** upon leave approval
- **Probation period validation** - only unpaid leave allowed during probation
- **Notice period enforcement** for planned leaves
- **Attendance record creation** for approved leave periods

**Approval Workflow:**
- **Multi-level approval** system with reporting manager hierarchy
- **Balance validation** before approval
- **Automatic attendance marking** as 'on_leave' for approved periods
- **Comprehensive audit trail** with approval/rejection timestamps

**Work From Home:**
- **Simple request/approval workflow** similar to leave requests
- **Date range support** for multi-day WFH requests
- **Reporting manager assignment** for approval routing

**Holiday Management:**
- **Multiple holiday types** (National, Regional, Company, Optional, Restricted)
- **Department/location-specific** holiday applicability
- **Calendar integration** with color-coded display
- **Bulk upload capability** for efficient holiday setup
- **Year-based organization** with filtering options

**Data Storage:**
- **IST timezone support** with string-based datetime storage
- **Automatic field calculation** (total days, employee details)
- **Comprehensive indexing** for efficient queries
- **Audit trail maintenance** with created/updated timestamps