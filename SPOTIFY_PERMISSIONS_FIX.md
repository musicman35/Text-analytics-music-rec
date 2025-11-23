# Fixing Spotify Audio Features 403 Error

## The Problem

Spotify's API is returning 403 (Forbidden) when trying to access audio features. This happens because:
1. Your app might be in "Development Mode" (limited to 25 users)
2. The audio features endpoint has stricter permissions
3. Your app hasn't been verified/approved by Spotify

## Solution: Request Extended Quota Mode

### Step 1: Go to Your Spotify Dashboard
1. Visit https://developer.spotify.com/dashboard
2. Click on your app ("Music Recommendation System" or whatever you named it)

### Step 2: Check Your Current Mode
- Look at the top of your app page
- You'll see either:
  - **"Development Mode"** (limited)
  - **"Extended Quota Mode"** (what we want)

### Step 3: Request Extended Quota Mode

If you're in Development Mode:

1. Click **"Settings"** in your app
2. Look for **"Quota Extension"** or **"Request Extended Quota"** button
3. Fill out the form:
   - **Use Case**: Academic/Educational Project
   - **Description**:
     ```
     Graduate school Text Analytics final project. Building a multi-agent
     music recommendation system using audio features for personalized
     recommendations. The system analyzes audio characteristics (energy,
     valence, danceability, etc.) to provide contextual music suggestions.
     ```
   - **Expected Users**: 1-10 (academic demo)
   - **API Calls**: 5,000-10,000 (for data collection)

4. Submit the request

### Step 4: Wait for Approval
- Usually takes 1-3 business days
- You'll receive an email when approved
- Once approved, the 403 errors will go away

---

## Alternative: Use Mock Audio Features (For Testing)

If you need to proceed immediately without waiting for approval, we can:

**Option A: Generate Reasonable Mock Data**
- Use genre-based defaults for audio features
- Pop: high energy (0.7), positive valence (0.8)
- Rock: medium-high energy (0.75), moderate valence (0.6)
- Hip-Hop: moderate energy (0.65), varied valence (0.5-0.7)
- Electronic: high energy (0.8), varied valence
- R&B: medium energy (0.5), emotional valence (0.4-0.6)

**Option B: Use Track Preview URLs**
- Spotify provides preview URLs without restrictions
- We can use track metadata (tempo, duration, etc.)
- Less accurate but works immediately

---

## Recommended Approach

### For Academic Project Demo:

1. **Short Term (Today)**: Use mock audio features to build and test the system
2. **Medium Term (This Week)**: Request Extended Quota Mode
3. **Long Term (Next Week)**: Once approved, re-collect data with real audio features

### For Production:

- Always use Extended Quota Mode
- Consider Spotify for Developers Enterprise for commercial use

---

## How to Request Mock Features (Immediate Solution)

If you want to proceed with the project right now, I can modify the code to:

1. Detect 403 errors on audio features
2. Generate genre-appropriate mock features
3. Still collect all other song data (name, artist, ID, etc.)
4. Replace with real features later when approved

**Advantages:**
- ✅ System works immediately
- ✅ Can demo and test all features
- ✅ Easy to replace with real data later
- ✅ Genre-based defaults are reasonably accurate

**Command to proceed with mock features:**
```bash
# I'll modify the spotify_collector.py to use fallback features
# Then you can run:
python collect_data.py --quick
```

---

## What To Do Right Now

**Choose One:**

### A. Wait for Spotify Approval (Recommended for final submission)
1. Request Extended Quota Mode (steps above)
2. Wait 1-3 days
3. Collect real data

### B. Use Mock Features (Recommended to start building NOW)
1. Let me modify the code to handle 403 gracefully
2. Generate genre-based audio features
3. Complete data collection today
4. Replace with real data when approved

Which would you like to do?
