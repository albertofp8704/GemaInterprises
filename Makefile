.PHONY: backend mobile android web seed

# Run the FastAPI backend locally
backend:
	uvicorn app.main:app --reload --port 8000

RAILWAY_URL=https://gemainterprises-production-a30b.up.railway.app

# Run the Flet mobile app on desktop (for dev preview against production)
mobile:
	GOAT_API_URL=$(RAILWAY_URL) python -m flet run mobile/main.py

# Run against local backend
mobile-local:
	GOAT_API_URL=http://localhost:8000 python -m flet run mobile/main.py

# Build Android APK (points to Railway)
android:
	GOAT_API_URL=$(RAILWAY_URL) flet build apk --project "GOAT Arc" --org com.goatarc

# Build iOS IPA (requires macOS + Xcode)
ios:
	GOAT_API_URL=$(RAILWAY_URL) flet build ipa --project "GOAT Arc" --org com.goatarc

# Build as web app
web:
	GOAT_API_URL=$(RAILWAY_URL) flet build web --project "GOAT Arc"

# Seed the database with quests + World Cup matches
seed:
	python -m app.seed_goat

# Install all dependencies
install:
	pip install -r requirements.txt
