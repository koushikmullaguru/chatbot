# AI School Chat Application Backend

This is the backend API for the AI School Chat Application, built with FastAPI and PostgreSQL.

## Features

- User Management (Teachers, Parents, Students)
- Academic Hierarchy (Classes, Sections, Subjects, Chapters, Topics, Sub-topics)
- Learning & Chat System
- Teacher Content Management
- Assessment System
- Planner & Performance Tracking
- Authentication & Authorization

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Virtual environment (recommended)

### Installation

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd AI-School-Chat-Application/backend
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the PostgreSQL database
   ```bash
   createdb school_chat_db
   ```

5. Configure environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and other settings
   ```

6. Run the application
   ```bash
   python start.py
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/     # API endpoint modules
│   │   └── main.py        # Main API router
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration settings
│   │   ├── database.py    # Database connection
│   │   └── security.py    # Authentication utilities
│   ├── main.py            # FastAPI application
│   ├── models/            # SQLAlchemy models
│   └── schemas/           # Pydantic schemas
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
└── start.py               # Startup script
```

## API Endpoints

The API is organized into the following modules:

### 1. Auth
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/send-otp` - Send parent login code to email
- `POST /api/v1/auth/verify-otp` - Verify OTP and return access token
- `POST /api/v1/auth/logout` - Invalidate session/token

### 2. User/Profile
- `GET /api/v1/users/profile` - Get current user's profile data
- `PUT /api/v1/users/profile` - Update current user profile
- `GET /api/v1/users/students` - Get all linked student profiles for a parent
- `POST /api/v1/users/students/verify-pin` - Verify student PIN for profile access
- `PUT /api/v1/users/student-profiles/{id}/interests` - Save/update student interests
- `GET /api/v1/users/student-profiles/{id}/achievements` - Fetch list of student achievements

### 3. Academic
- `GET /api/v1/academic/classes` - Get all available classes/grades
- `GET /api/v1/academic/sections` - Get sections for a class
- `GET /api/v1/academic/subjects` - Get subjects for a class
- `GET /api/v1/academic/chapters` - Get chapters for a subject
- `GET /api/v1/academic/topics` - Get topics for a specific subject
- `GET /api/v1/academic/sub-topics` - Get granular sub-topics for a chapter

### 4. Chat
- `GET /api/v1/chat/sessions` - List all chat sessions for the user
- `POST /api/v1/chat/sessions` - Create new session
- `GET /api/v1/chat/sessions/{id}` - Get session details and messages
- `GET /api/v1/chat/sessions/{id}/messages` - Get message history for a session
- `POST /api/v1/chat/sessions/{id}/messages` - Send user message and get AI response

### 5. AI Generation
- `POST /api/v1/generator/quiz` - AI generates a quiz/worksheet
- `POST /api/v1/generator/exam` - AI generates a full formal exam paper
- `POST /api/v1/generator/revision` - AI generates revision notes/plans
- `POST /api/v1/generator/homework` - AI generates homework assignments
- `POST /api/v1/generator/content/generate-notes` - AI generates teacher lecture notes

### 6. Assessment
- `GET /api/v1/assessments` - List all teacher-created assessments
- `POST /api/v1/assessments/start-quiz/{id}` - Log the start of a quiz attempt
- `POST /api/v1/assessments/submit-quiz/{id}` - Submit answers for grading and results
- `GET /api/v1/assessments/quiz-results/{id}` - Fetch detailed quiz result
- `GET /api/v1/assessments/student-quiz-results` - List all results for a student

### 7. Planner
- `GET /api/v1/planner/tasks` - Get student tasks for the planner
- `POST /api/v1/planner/tasks` - Add new task to the planner
- `PUT /api/v1/planner/tasks/{id}` - Update task status
- `DELETE /api/v1/planner/tasks/{id}` - Remove task from planner
- `GET /api/v1/planner/progress/weekly` - Get weekly performance metrics

### 8. Reporting
- `GET /api/v1/performance/student` - Full performance report for a student
- `GET /api/v1/performance/teacher/insights` - Class-wide analytics for teachers
- `GET /api/v1/performance/parent/dashboard` - Dashboard for multiple linked children
- `GET /api/v1/performance/teacher/students` - List students in a teacher's class
- `GET /api/v1/performance/content/{id}/download` - Generate downloadable file for content

## Database Schema

The application uses the following main database tables:

### User Management
- `users` - User accounts (teachers, parents, students)
- `student_profiles` - Student profile information
- `parent_student_relations` - Parent-student relationships
- `student_interests` - Student interests
- `student_achievements` - Student achievements

### Academic Hierarchy
- `classes` - School classes/grades
- `sections` - Class sections
- `subjects` - Subjects
- `chapters` - Subject chapters
- `topics` - Chapter topics
- `sub_topics` - Topic sub-topics

### Academic Structure
- `syllabus_documents` - Syllabus documents

### Learning & Chat
- `chat_sessions` - Chat sessions
- `messages` - Chat messages

### Teacher Content
- `teacher_content_units` - Teacher-created content

### Assessments
- `assessments` - Assessments (quizzes, worksheets, exams)
- `questions` - Assessment questions
- `assessment_results` - Assessment results
- `student_answers` - Student answers

### Planner & Performance
- `tasks` - Student tasks
- `report_cards` - Student report cards
- `subject_grades` - Subject grades
- `study_sessions` - Study sessions

### System
- `otp_verifications` - OTP verification records
- `user_sessions` - User sessions

## Development

### Adding New Endpoints

1. Create a new file in `app/api/endpoints/` for your endpoint module
2. Define your API routes using FastAPI
3. Import the module in `app/api/main.py` and include it in the API router
4. Add corresponding schemas in `app/schemas/` if needed
5. Add corresponding models in `app/models/` if needed

### Database Migrations

For now, the application creates all tables automatically on startup. In a production environment, you should use a proper migration tool like Alembic.

## Testing

To run tests:
```bash
pytest
```

## License

This project is licensed under the MIT License.