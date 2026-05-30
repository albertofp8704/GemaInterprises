.PHONY: backend mobile android web seed

# Run the FastAPI backend locally
backend:
	uvicorn app.main:app --reload --port 8000

# Run the Flet mobile app on desktop (for dev preview)
mobile:
	python -m flet run mobile/main.py

# Build Android APK
android:
	cd mobile && flet build android --project "GOAT Arc" --org com.goatarc

# Build iOS IPA (requires macOS + Xcode)
ios:
	cd mobile && flet build ios --project "GOAT Arc" --org com.goatarc

# Build as web app
web:
	cd mobile && flet build web --project "GOAT Arc"

# Seed the database with quests + World Cup matches
seed:
	python -m app.seed_goat

# Install all dependencies
install:
	pip install -r requirements.txt
