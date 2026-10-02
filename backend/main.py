import os
import json
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
load_dotenv()

# Allow OAuth token responses whose granted scopes differ from the
# originally requested set.
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import bcrypt
from jose import jwt, JWTError
from google_auth_oauthlib.flow import Flow

from database import engine, Base, SessionLocal
import models
from models import Task
from security.permissions import check_permission
from agent.executor import execute_tool
from agent.service import run_agent
from tools.sheets import read_sheet, update_sheet


# ==================================================
# GOOGLE OAUTH CONFIGURATION
# ==================================================

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

# Temporary in-memory OAuth state storage.
google_oauth_sessions = {}


# ==================================================
# JWT CONFIGURATION
# ==================================================

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
SECRET_KEY = os.getenv("SECRET_KEY")

if ENVIRONMENT == "production" and not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set in production")

if not SECRET_KEY:
    SECRET_KEY = "development-only-change-me"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()


# ==================================================
# DATABASE DEPENDENCY
# ==================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ==================================================
# CREATE FASTAPI APP
# ==================================================

app = FastAPI(
    title="Autonomous Work Agent API",
    description="Backend API for the Autonomous Work Agent",
    version="1.0.0"
)


# ==================================================
# CORS
# ==================================================

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ==================================================
# CREATE DATABASE TABLES
# ==================================================

Base.metadata.create_all(bind=engine)


# ==================================================
# REQUEST MODELS
# ==================================================

class TaskCreate(BaseModel):
    workspace: str
    goal: str


class TaskRequest(BaseModel):
    goal: str


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ConnectionRequest(BaseModel):
    service: str


class PermissionRequest(BaseModel):
    service: str
    action: str
    allowed: int


class ApprovalRequest(BaseModel):
    service: str
    action: str
    task_id: int | None = None


class ApprovalDecision(BaseModel):
    status: str


class ToolActivityRequest(BaseModel):
    task_id: int
    tool: str
    result: str


class SheetRequest(BaseModel):
    spreadsheet_id: str
    range_name: str


class SheetUpdateRequest(BaseModel):
    spreadsheet_id: str
    range_name: str
    values: list[list[str]]


class AgentTaskRequest(BaseModel):
    workspace: str
    goal: str


# ==================================================
# CREATE JWT ACCESS TOKEN
# ==================================================

def create_access_token(user_id: int):

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


# ==================================================
# VERIFY JWT / GET CURRENT USER
# ==================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        return int(user_id)

    except (JWTError, ValueError, TypeError):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


# ==================================================
# HOME
# ==================================================

@app.get("/")
def home():

    return {
        "message": "Autonomous Work Agent backend is running"
    }


# ==================================================
# REGISTER
# ==================================================

@app.post("/register")
def register(user: RegisterRequest):

    db = SessionLocal()

    try:

        password_bytes = user.password.encode("utf-8")

        if len(password_bytes) < 8 or len(password_bytes) > 72:
            raise HTTPException(
                status_code=400,
                detail="Password must be 8 to 72 bytes long"
            )

        existing_user = db.query(models.User).filter(
            models.User.email == user.email
        ).first()

        if existing_user:
            return {
                "message": "User already exists"
            }

        password_hash = bcrypt.hashpw(
            password_bytes,
            bcrypt.gensalt()
        ).decode("utf-8")

        new_user = models.User(
            email=user.email,
            password_hash=password_hash
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "User registered successfully",
            "id": new_user.id,
            "email": new_user.email
        }

    finally:
        db.close()


# ==================================================
# LOGIN
# ==================================================

@app.post("/login")
def login(user: LoginRequest):

    db = SessionLocal()

    try:

        existing_user = db.query(models.User).filter(
            models.User.email == user.email
        ).first()

        password_bytes = user.password.encode("utf-8")

        if len(password_bytes) > 72:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        if not existing_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        password_matches = bcrypt.checkpw(
            password_bytes,
            existing_user.password_hash.encode("utf-8")
        )

        if not password_matches:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        access_token = create_access_token(
            existing_user.id
        )

        return {
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": existing_user.id,
            "email": existing_user.email
        }

    finally:
        db.close()


# ==================================================
# CURRENT USER
# ==================================================

@app.get("/me")
def get_me(
    current_user_id: int = Depends(get_current_user)
):

    return {
        "message": "You are authenticated",
        "user_id": current_user_id
    }


# ==================================================
# TASKS
# ==================================================

@app.post("/tasks")
def create_task(
    task_data: TaskCreate,
    current_user_id: int = Depends(get_current_user)
):

    db = SessionLocal()

    try:

        task = Task(
            goal=task_data.goal,
            status="running",
            user_id=current_user_id,
            workspace=task_data.workspace
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        print("\n================================")
        print("STARTING AGENT")
        print("Task ID:", task.id)
        print("Workspace:", task.workspace)
        print("Goal:", task.goal)
        print("================================\n")

        result = run_agent(
            goal=task.goal,
            user_id=current_user_id,
            workspace=task.workspace,
            task_id=task.id
        )

        if result.get("status") == "approval_required":
            task.status = "waiting_approval"

        elif result.get("status") == "completed":
            task.status = "completed"

        else:
            task.status = "failed"

        db.commit()

        return {
            "message": "Task executed",
            "id": task.id,
            "workspace": task.workspace,
            "goal": task.goal,
            "status": task.status,
            "result": result
        }

    except Exception as e:

        print("TASK ERROR:", str(e))

        return {
            "message": "Task execution failed",
            "error": str(e)
        }

    finally:
        db.close()


@app.get("/tasks")
def get_tasks(
    current_user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):

    tasks = db.query(models.Task).filter(
        models.Task.user_id == current_user_id
    ).all()

    return tasks


# ==================================================
# CONNECTIONS
# ==================================================

@app.post("/connections")
def create_connection(
    connection: ConnectionRequest,
    current_user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):

    new_connection = models.Connection(
        service=connection.service,
        user_id=current_user_id
    )

    db.add(new_connection)
    db.commit()
    db.refresh(new_connection)

    return {
        "message": "Connection created",
        "id": new_connection.id,
        "service": new_connection.service,
        "status": new_connection.status,
        "user_id": new_connection.user_id
    }


@app.get("/connections")
def get_connections(
    current_user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):

    connections = db.query(models.Connection).filter(
        models.Connection.user_id == current_user_id
    ).all()

    return connections


# ==================================================
# PERMISSIONS
# ==================================================

@app.post("/permissions")
def create_permission(
    permission: PermissionRequest,
    current_user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):

    new_permission = models.Permission(
        service=permission.service,
        action=permission.action,
        allowed=permission.allowed,
        user_id=current_user_id
    )

    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)

    return {
        "message": "Permission created",
        "id": new_permission.id,
        "service": new_permission.service,
        "action": new_permission.action,
        "allowed": new_permission.allowed,
        "user_id": new_permission.user_id
    }


@app.get("/permissions")
def get_permissions(
    current_user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):

    permissions = db.query(models.Permission).filter(
        models.Permission.user_id == current_user_id
    ).all()

    return permissions


# ==================================================
# APPROVALS
# ==================================================

@app.post("/approvals")
def create_approval(
    approval: ApprovalRequest,
    current_user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):

    # An approval may reference only a task owned by the authenticated user.
    if approval.task_id is not None:
        task = db.query(models.Task).filter(
            models.Task.id == approval.task_id,
            models.Task.user_id == current_user_id
        ).first()

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

    service = approval.service.strip().lower()
    action = approval.action.strip().lower()

    allowed_actions = {
        "update_sheet",
        "append_rows",
        "clear_range",
        "delete_row",
        "delete_column",
        "format_header_bold",
        "send_email",
        "trash_email",
    }

    if action not in allowed_actions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported approval action"
        )

    if service not in {"google", "google_sheets", "gmail"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported approval service"
        )

    sheet_actions = {
        "update_sheet", "append_rows", "clear_range",
        "delete_row", "delete_column", "format_header_bold"
    }
    gmail_actions = {"send_email", "trash_email"}

    if (action in sheet_actions and service not in {"google", "google_sheets"}) or \
       (action in gmail_actions and service != "gmail"):
        raise HTTPException(
            status_code=400,
            detail="Service and action do not match"
        )

    new_approval = models.Approval(
        service=service,
        action=action,
        task_id=approval.task_id,
        user_id=current_user_id
    )

    db.add(new_approval)
    db.commit()
    db.refresh(new_approval)

    return {
        "message": "Approval requested",
        "id": new_approval.id,
        "service": new_approval.service,
        "action": new_approval.action,
        "task_id": new_approval.task_id,
        "status": new_approval.status,
        "user_id": new_approval.user_id
    }

@app.get("/approvals")
def get_approvals(
    current_user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):

    approvals = db.query(models.Approval).filter(
        models.Approval.user_id == current_user_id
    ).all()

    return approvals


@app.post("/approvals/{approval_id}")
def decide_approval(
    approval_id: int,
    decision: ApprovalDecision,
    current_user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):

    # ==================================================
    # 1. FIND APPROVAL
    # ==================================================

    approval = db.query(models.Approval).filter(
        models.Approval.id == approval_id,
        models.Approval.user_id == current_user_id
    ).first()

    if not approval:

        raise HTTPException(
            status_code=404,
            detail="Approval not found"
        )

    # Defense in depth: if this approval references a task, that task
    # must also belong to the authenticated user.
    if approval.task_id is not None:
        owned_task = db.query(models.Task).filter(
            models.Task.id == approval.task_id,
            models.Task.user_id == current_user_id
        ).first()

        if not owned_task:
            raise HTTPException(
                status_code=404,
                detail="Approval task not found"
            )

    # ==================================================
    # 2. CHECK PENDING
    # ==================================================

    if approval.status != "pending":

        raise HTTPException(
            status_code=400,
            detail=f"Approval is already {approval.status}"
        )

    # ==================================================
    # 3. VALIDATE DECISION
    # ==================================================

    decision_status = decision.status.lower().strip()

    if decision_status not in ["approved", "rejected"]:

        raise HTTPException(
            status_code=400,
            detail="Status must be approved or rejected"
        )

    # ==================================================
    # 4. REJECT
    # ==================================================

    if decision_status == "rejected":

        approval.status = "rejected"

        db.commit()
        db.refresh(approval)

        return {
            "message": "Approval rejected. No action was executed.",
            "id": approval.id,
            "status": approval.status
        }

    # ==================================================
    # 5. READ APPROVAL DETAILS
    # ==================================================

    try:

        approval_details = json.loads(
            approval.details or "{}"
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Invalid approval details: {str(error)}"
        )

    spreadsheet_id = approval_details.get(
        "spreadsheet_id"
    )

    range_name = approval_details.get(
        "range_name"
    )

    if not spreadsheet_id:

        raise HTTPException(
            status_code=400,
            detail="Spreadsheet ID missing from approval."
        )

    # ==================================================
    # 6. GET GOOGLE CONNECTION
    # ==================================================

    connection = db.query(
        models.Connection
    ).filter(
        models.Connection.user_id == current_user_id,
        models.Connection.service == "google",
        models.Connection.status == "connected"
    ).order_by(
        models.Connection.id.desc()
    ).first()

    if not connection:

        raise HTTPException(
            status_code=404,
            detail="Google account is not connected"
        )

    # ==================================================
    # 7. CHECK PERMISSION AGAIN
    # ==================================================

    allowed = check_permission(
        db=db,
        user_id=current_user_id,
        service="google",
        action=approval.action
    )

    if not allowed:

        raise HTTPException(
            status_code=403,
            detail=f"Permission denied for {approval.action}"
        )

    # ==================================================
    # 8. COMMON GOOGLE CREDENTIALS
    # ==================================================

    tool_arguments = {
        "access_token": connection.access_token,
        "refresh_token": connection.refresh_token,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "scopes": GOOGLE_SCOPES,
        "spreadsheet_id": spreadsheet_id,
        "range_name": range_name
    }

    # ==================================================
    # 9. ACTION-SPECIFIC ARGUMENTS
    # ==================================================

    if approval.action == "update_sheet":

        values = approval_details.get("values")

        if not values:

            raise HTTPException(
                status_code=400,
                detail="Values missing from approval."
            )

        tool_arguments["values"] = values

    elif approval.action == "append_rows":

        values = approval_details.get("values")

        if not values:

            raise HTTPException(
                status_code=400,
                detail="Values missing from approval."
            )

        tool_arguments["values"] = values

    elif approval.action == "clear_range":

        tool_arguments["range_name"] = approval_details.get(
            "range_name",
            range_name
        )

    elif approval.action == "delete_row":

        row_index = approval_details.get("row_index")

        if not isinstance(row_index, int) or row_index < 0:

            raise HTTPException(
                status_code=400,
                detail="Invalid row_index."
            )

        tool_arguments["row_index"] = row_index

    elif approval.action == "delete_column":

        column_index = approval_details.get("column_index")

        if not isinstance(column_index, int) or column_index < 0:

            raise HTTPException(
                status_code=400,
                detail="Invalid column_index."
            )

        tool_arguments["column_index"] = column_index

    elif approval.action == "format_header_bold":

        pass

    else:

        raise HTTPException(
            status_code=400,
            detail=f"Unsupported approval action: {approval.action}"
        )

    # ==================================================
    # 10. EXECUTE ACTUAL TOOL
    # ==================================================

    try:

        result = execute_tool(
            approval.action,
            tool_arguments
        )

    except Exception as error:

        approval.status = "failed"

        db.commit()

        return {
            "message": f"Tool execution failed: {str(error)}",
            "id": approval.id,
            "status": "failed"
        }

    # ==================================================
    # 11. VERIFY UPDATE
    # ==================================================

    verified = None

    if approval.action == "update_sheet":

        verification_arguments = {
            "access_token": connection.access_token,
            "refresh_token": connection.refresh_token,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "scopes": GOOGLE_SCOPES,
            "spreadsheet_id": spreadsheet_id,
            "range_name": range_name,
            "expected_values": approval_details["values"]
        }

        try:

            verified = execute_tool(
                "verify_sheet",
                verification_arguments
            )

        except Exception as error:

            approval.status = "failed"

            db.commit()

            return {
                "message": (
                    "Sheet update succeeded, "
                    f"but verification failed: {str(error)}"
                ),
                "id": approval.id,
                "status": "failed",
                "verified": False
            }

        if not verified:

            approval.status = "failed"

            db.commit()

            return {
                "message": "Sheet was updated but verification failed.",
                "id": approval.id,
                "status": "failed",
                "verified": False
            }

    # ==================================================
    # 12. MARK APPROVAL COMPLETE
    # ==================================================

    approval.status = "approved"

    db.commit()
    db.refresh(approval)

    # ==================================================
    # 13. RETURN RESULT
    # ==================================================

    response = {
        "message": (
            f"Approval approved and {approval.action} executed."
        ),
        "id": approval.id,
        "status": "approved",
        "action": approval.action,
        "result": result
    }

    if verified is not None:
        response["verified"] = verified

    return response


# ==================================================
# TOOL ACTIVITY
# ==================================================

@app.post("/activity")
def create_activity(
    activity: ToolActivityRequest,
    current_user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):

    owned_task = db.query(models.Task).filter(
        models.Task.id == activity.task_id,
        models.Task.user_id == current_user_id
    ).first()

    if not owned_task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    new_activity = models.ToolActivity(
        task_id=activity.task_id,
        tool=activity.tool,
        result=activity.result,
        user_id=current_user_id
    )

    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)

    return {
        "message": "Tool activity recorded",
        "id": new_activity.id,
        "task_id": new_activity.task_id,
        "tool": new_activity.tool,
        "result": new_activity.result,
        "user_id": new_activity.user_id
    }


@app.get("/activity")
def get_activity(
    current_user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):

    activities = db.query(models.ToolActivity).filter(
        models.ToolActivity.user_id == current_user_id
    ).all()

    return activities


# ==================================================
# GOOGLE OAUTH LOGIN
# ==================================================

@app.get("/auth/google")
def google_login(
    current_user_id: int = Depends(get_current_user)
):

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",

        # Request the current scope set instead of
        # incrementally reusing the old Sheets-only grant.
        include_granted_scopes="false",

        # Force Google to show the consent screen.
        prompt="consent"
    )

    google_oauth_sessions[state] = {
        "code_verifier": flow.code_verifier,
        "user_id": current_user_id
    }

    return {
        "authorization_url": authorization_url
    }


# ==================================================
# GOOGLE OAUTH CALLBACK
# ==================================================

@app.get("/auth/google/callback")
def google_callback(code: str, state: str):

    oauth_session = google_oauth_sessions.get(state)

    if not oauth_session:

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state"
        )

    code_verifier = oauth_session["code_verifier"]
    user_id = oauth_session["user_id"]

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
        code_verifier=code_verifier,
        state=state
    )

    try:

        flow.fetch_token(code=code)

        credentials = flow.credentials

        db = SessionLocal()

        try:

            # Update the existing Google connection instead of
            # creating duplicate stale connections.
            existing_connection = db.query(
                models.Connection
            ).filter(
                models.Connection.user_id == user_id,
                models.Connection.service == "google"
            ).order_by(
                models.Connection.id.desc()
            ).first()

            if existing_connection:

                existing_connection.status = "connected"
                existing_connection.access_token = credentials.token

                if credentials.refresh_token:
                    existing_connection.refresh_token = (
                        credentials.refresh_token
                    )

                connection = existing_connection

            else:

                connection = models.Connection(
                    service="google",
                    status="connected",
                    user_id=user_id,
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token
                )

                db.add(connection)

            db.commit()
            db.refresh(connection)

            return {
                "message": "Google account connected successfully",
                "connection_id": connection.id,
                "user_id": user_id,
                "service": "google",
                "status": "connected"
            }

        except Exception as e:

            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Failed to save Google connection: {str(e)}"
            )

        finally:
            db.close()

    finally:

        # OAuth state should only be usable once.
        google_oauth_sessions.pop(state, None)


# ==================================================
# SHEETS READ
# ==================================================

@app.post("/sheets/read")
def read_sheet_endpoint(
    request: SheetRequest,
    current_user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):

    connection = db.query(
        models.Connection
    ).filter(
        models.Connection.user_id == current_user_id,
        models.Connection.service == "google",
        models.Connection.status == "connected"
    ).order_by(
        models.Connection.id.desc()
    ).first()

    if not connection:

        raise HTTPException(
            status_code=404,
            detail="Google account is not connected"
        )

    values = read_sheet(
        access_token=connection.access_token,
        refresh_token=connection.refresh_token,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=GOOGLE_SCOPES,
        spreadsheet_id=request.spreadsheet_id,
        range_name=request.range_name
    )

    return {
        "message": "Sheet data retrieved successfully",
        "spreadsheet_id": request.spreadsheet_id,
        "range": request.range_name,
        "values": values
    }


# ==================================================
# SHEETS UPDATE
# ==================================================

@app.post("/sheets/update")
def update_sheet_endpoint(
    request: SheetUpdateRequest,
    current_user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):

    connection = db.query(
        models.Connection
    ).filter(
        models.Connection.user_id == current_user_id,
        models.Connection.service == "google",
        models.Connection.status == "connected"
    ).order_by(
        models.Connection.id.desc()
    ).first()

    if not connection:

        raise HTTPException(
            status_code=404,
            detail="Google account is not connected"
        )

    allowed = check_permission(
        db=db,
        user_id=current_user_id,
        service="google",
        action="update_sheet"
    )

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail="Permission denied for update_sheet"
        )

    updated_cells = update_sheet(
        access_token=connection.access_token,
        refresh_token=connection.refresh_token,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=GOOGLE_SCOPES,
        spreadsheet_id=request.spreadsheet_id,
        range_name=request.range_name,
        values=request.values
    )

    return {
        "message": "Sheet updated successfully",
        "spreadsheet_id": request.spreadsheet_id,
        "range": request.range_name,
        "updated_cells": updated_cells
    }


# ==================================================
# AGENT RUN
# ==================================================

@app.post("/agent/run")
def run_agent_endpoint(
    request: AgentTaskRequest,
    current_user_id: int = Depends(get_current_user)
):

    result = run_agent(
        goal=request.goal,
        user_id=current_user_id,
        workspace=request.workspace
    )

    return result
