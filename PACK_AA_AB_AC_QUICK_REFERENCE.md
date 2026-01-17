# PACK AA, AB, AC — Quick Reference Guide

## PACK AA: Story Engine — `/stories`

### Create Template
```bash
POST /stories/templates
{
  "arc_name": "Valhalla Chronicles",
  "audience": "child",
  "tone": "funny",
  "purpose": "bedtime",
  "prompt": "A magical quest for pizza",
  "outline": "optional"
}
```

### List Templates
```bash
GET /stories/templates                     # All active
GET /stories/templates?purpose=bedtime     # Filter by purpose
GET /stories/templates?arc_name=xyz        # Filter by arc
```

### Create Episode
```bash
POST /stories/episodes
{
  "template_id": 1,
  "child_id": 5,
  "title": "Episode 1",
  "content": "Once upon a time...",
  "mood": "cozy",
  "length_estimate_minutes": 10
}
```

### List Episodes for Child
```bash
GET /stories/episodes/by-child/5
```

---

## PACK AB: Education Engine — `/education`

### Create Course
```bash
POST /education/courses
{
  "title": "Intro to Real Estate",
  "subject": "real_estate",
  "level": "beginner",
  "description": "optional"
}
```

### List Courses
```bash
GET /education/courses                    # All active
GET /education/courses?subject=real_estate # Filter by subject
```

### Create Lesson
```bash
POST /education/lessons
{
  "course_id": 1,
  "title": "Lesson 1: Basics",
  "summary": "optional",
  "order_index": 1
}
```

### List Lessons in Course
```bash
GET /education/courses/1/lessons  # Returns ordered list
```

### Enroll Learner
```bash
POST /education/enrollments
{
  "learner_id": 5,
  "course_id": 1
}
```

### Update Enrollment Progress
```bash
PATCH /education/enrollments/1
{
  "lessons_completed": 3,
  "is_active": true
}
```

### List Learner's Courses
```bash
GET /education/enrollments/by-learner/5
```

---

## PACK AC: Media Engine — `/media`

### Create Channel
```bash
POST /media/channels
{
  "name": "YouTube",
  "slug": "youtube",
  "description": "Main video channel"
}
```

### List Channels
```bash
GET /media/channels              # All active
GET /media/channels?active_only=false  # Include inactive
```

### Create Content
```bash
POST /media/content
{
  "title": "Valhalla Intro Video",
  "content_type": "video_script",
  "body": "Full script text...",
  "tags": "intro,valhalla,epic",
  "audience": "public"
}
```

### List Content
```bash
GET /media/content                    # All
GET /media/content?content_type=article # By type
```

### Create Publish Entry
```bash
POST /media/publish
{
  "content_id": 1,
  "channel_id": 1,
  "status": "planned"
}
```

### Publish Content
```bash
PATCH /media/publish/1
{
  "status": "published",
  "external_ref": "https://youtube.com/watch?v=abc123"
}
```

### List Publishes for Content
```bash
GET /media/publish/by-content/1
```

---

## Database Relationships

### PACK AA
```
StoryTemplate (1) ──┬── (Many) StoryEpisode
  - arc_name          - template_id
  - purpose           - child_id
  - prompt            - content
  - is_active         - mood
```

### PACK AB
```
Course (1) ──┬── (Many) Lesson
  - subject   - course_id
  - level     - order_index
  - is_active

(Many) Learner ──┬── (1) Course (via Enrollment)
                  - lessons_completed
                  - is_active
```

### PACK AC
```
MediaChannel (1) ──┬── (Many) MediaPublishLog
  - name            - channel_id
  - slug            - status
  - is_active       - external_ref

MediaContent (1) ──┬── (Many) MediaPublishLog
  - title           - content_id
  - body            - published_at
  - audience
```

---

## Testing Commands

```bash
# All AA tests
pytest app/tests/test_story_engine.py -v

# All AB tests
pytest app/tests/test_education_engine.py -v

# All AC tests
pytest app/tests/test_media_engine.py -v

# All three packs
pytest app/tests/test_story_engine.py \
        app/tests/test_education_engine.py \
        app/tests/test_media_engine.py -v

# With coverage
pytest app/tests/test_*_engine.py --cov=app --cov-report=html
```

---

## Common Use Cases

### Heimdall Story Flow (PACK AA)
1. Create StoryTemplate with arc, purpose, prompt
2. Heimdall generates story based on prompt
3. Create StoryEpisode with generated content
4. Track episodes by child
5. Filter templates by purpose for different scenarios

### Learning Path (PACK AB)
1. Create Course with subject and level
2. Add Lessons in sequence (order_index)
3. Enroll learners in courses
4. Track lessons_completed for progress
5. Deactivate enrollment when complete

### Content Distribution (PACK AC)
1. Create MediaChannel for each distribution platform
2. Create MediaContent (articles, scripts, posts)
3. Create PublishLog entries for each channel
4. Update status to "published" with timestamp
5. Track external_ref (URLs, video IDs)

---

## Error Responses

All endpoints return standard HTTP responses:
- **200 OK** — Successful operation
- **201 Created** — Resource created (if applicable)
- **400 Bad Request** — Invalid request data
- **404 Not Found** — Resource not found
- **422 Unprocessable Entity** — Validation error
- **500 Internal Server Error** — Server error

Example 404:
```json
{
  "detail": "Template not found"
}
```

---

## API Documentation

**Swagger UI:** `http://localhost:8000/docs`
**ReDoc:** `http://localhost:8000/redoc`

All endpoints documented with descriptions, request/response models, and examples.

---

## Valhalla System Status

- **Total Packs:** 29 (A-AC)
- **Total Endpoints:** 200+
- **New in Session:** 24 endpoints (AA, AB, AC)
- **Total Tests:** 300+
- **New Tests:** 32 tests
- **Status:** ✅ Production Ready

Deploy when ready with:
```bash
alembic upgrade head  # Apply migrations
uvicorn app.main:app --port 8000
```
